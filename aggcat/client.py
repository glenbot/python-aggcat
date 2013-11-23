from __future__ import absolute_import

import urlparse

import requests
from requests_oauthlib import OAuth1Session
from lxml import etree

from .saml import SAML
from .exceptions import HTTPError
from .utils import remove_namespaces
from .parser import Objectify
from .helpers import AccountType


class AggCatResponse(object):
    """General response object that contains the HTTP status code
    and response text"""
    def __init__(self, status_code, headers, content):
        self.status_code = status_code
        self.headers = headers
        self.content = content

    def __repr__(self):
        return u'<AggCatResponse %s>' % self.status_code


class AggcatClient(object):
    """Intuit Customer Data API client

    :param string consumer_key: The OAuth consumer key given on the Intuit application page
    :param string consumer_secret: The OAuth consumer secret given on the Intuit application page
    :param string saml_identity_provider_id: The SAML identitity provider id given on the Intuit application page
    :param integer customer_id: It can be any integer. Try using the database primary key of a user
                        in your system or some other unique identifier such as a guid. If you are just
                        testing you can use whatever integer you want.
    :param string private_key: The absolute path to the generated x509 private key
    :param boolean objectify: (optional) Convert XML into pythonic object on every API call. Default: ``True``
    :param boolean verify_ssl: (optional) Verify SSL Certificate. See :ref:`known_issues`. Default: ``True``

    :returns: :class:`AggcatClient`

    Assuming you have an *OAuth Consumer Key*, *Oauth Consumer Secret*, *SAML Identity Provider ID*,
    and a path to the x509 certificates generated, you are ready to start querying::

        from aggcat import AggcatClient

        client = AggcatClient(
            'oauth_consumer_key',
            'oauth_consumer_secret',
            'saml_identity_provider_id',
            'customer_id',
            '/path/to/x509/appname.key'
        )

    .. note::

        ``customer_id`` (Integer) It can be any integer. Try using the database primary key
        of a user in your system or some other unique identifier such as a guid.
        If you are just testing you can use whatever integer you want.

        ``objectify`` (Boolean) This is a BETA functionality. It will objectify the XML returned from
        intuit into standard python objects so you don't have to mess with XML. Default: ``True``
    """
    def __init__(self, consumer_key, consumer_secret, saml_identity_provider_id, customer_id, private_key, objectify=True, verify_ssl=True):
        # base API url
        self.base_url = 'https://financialdatafeed.platform.intuit.com/rest-war/v1'

        # standard values needed for intuit API authentication
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.saml_identity_provider_id = saml_identity_provider_id
        self.customer_id = customer_id
        self.private_key = private_key

        # verify ssl
        self.verify_ssl = verify_ssl

        # SAML object to help create SAML assertion message
        self.saml = SAML(private_key, saml_identity_provider_id, customer_id)

        # intuit saml authentication url
        self.saml_url = 'https://oauth.intuit.com/oauth/v1/get_access_token_by_saml'

        # contact intuit, authenticate, and get the consumer tokens
        self._oauth_tokens = self._get_oauth_tokens()

        # Beta objectification
        self.objectify = objectify

        # assign the client
        self.client = self._client()

    def _client(self):
        """Build an oAuth client from consumer tokens, and oauth tokens"""
        # initialze the oauth session for requests
        session = OAuth1Session(
            self.consumer_key,
            self.consumer_secret,
            self._oauth_tokens['oauth_token'][0],
            self._oauth_tokens['oauth_token_secret'][0]
        )
        return session

    def _get_oauth_tokens(self):
        """Get an oauth token by sending over the SAML assertion"""
        payload = {'saml_assertion': self.saml.assertion()}
        headers = {'Authorization': 'OAuth oauth_consumer_key="%s"' % self.consumer_key}

        r = requests.post(self.saml_url, data=payload, headers=headers)

        if r.status_code == 200:
            return urlparse.parse_qs(r.text)
        else:
            raise HTTPError('A %s error occured retrieving token. Please check your settings.' % r.status_code)

    def _refresh_client(self):
        """If a token expires, refresh the client"""
        # refresh the saml assertion
        self.saml.refresh()

        # set new auth tokens
        self._oauth_tokens = self._get_oauth_tokens()

        # get a new client
        self.client = self._client()

    def _build_url(self, path):
        """Build a url from a string path"""
        return '%s/%s' % (self.base_url, path)

    def _make_request(self, path, method='GET', body=None, query={}, headers={}):
        """Make the signed request to the API"""
        # build the query url
        url = self._build_url(path)

        # check for plain object request
        return_obj = self.objectify

        if method == 'GET':
            response = self.client.get(url, params=query, verify=self.verify_ssl)

        if method == 'PUT':
            headers.update({'Content-Type': 'application/xml'})
            response = self.client.put(url, data=body, headers=headers, verify=self.verify_ssl)

        if method == 'DELETE':
            response = self.client.delete(url, verify=self.verify_ssl)

        if method == 'POST':
            headers.update({'Content-Type': 'application/xml'})
            response = self.client.post(url, data=body, headers=headers, verify=self.verify_ssl)

        # refresh the token if token expires and retry the query
        if 'www-authenticate' in response.headers:
            if response.headers['www-authenticate'] == 'OAuth oauth_problem="token_rejected"':
                self._refresh_client()
                self._make_request(path, method, body, query, headers)

        if response.status_code not in [200, 201, 401]:
            raise HTTPError('Status Code: %s, Response %s' % (response.status_code, response.text,))

        if return_obj:
            try:
                return AggCatResponse(
                    response.status_code,
                    response.headers,
                    Objectify(response.content).get_object()
                )
            except etree.XMLSyntaxError:
                return None

        return AggCatResponse(response.status_code, response.content)

    def _remove_namespaces(self, tree):
        """Remove the namspaces from the Intuit XML for easier parsing"""
        return remove_namespaces(tree)

    def _generate_login_xml(self, **credentials):
        """Generate the xml needed to login"""
        xml_credentials = []

        # loop through the required credentials and generate xml credential keys and values
        for name, value in credentials.iteritems():
            xml_credentials.append('<credential><name>%s</name><value>%s</value></credential>' % (
                name,
                value
            ))

        xml = """
        <InstitutionLogin xmlns="http://schema.intuit.com/platform/fdatafeed/institutionlogin/v1">
        <credentials>%s</credentials>
        </InstitutionLogin>
        """.strip()

        return xml % ''.join(xml_credentials)

    def _generate_challenge_response(self, responses):
        """Generate a challenge xml to post back to :meth:`discover_and_add_accounts` in case
        of two-factor authentication or other types of authentication"""
        xml_responses = []

        xml = """
        <InstitutionLogin xmlns="http://schema.intuit.com/platform/fdatafeed/institutionlogin/v1">
        <challengeResponses>%s</challengeResponses>
        </InstitutionLogin>
        """.strip()

        for response in responses:
            xml_responses.append(
                '<response xmlns="http://schema.intuit.com/platform/fdatafeed/challenge/v1">%s</response>' % response
            )

        return xml % ''.join(xml_responses)

    def _validate_credentials(self, institution_id, **credentials):
        """Get required fields and match the `name` key with the keys in the credentials passed
        to ensure that all required fields exist"""
        required_fields = self.get_credential_fields(institution_id)

        for field in required_fields:
            if field['name'] not in credentials.keys():
                error_msg = 'A required credential field is missing. Required credentials fields are %s. You provided %s.'
                raise ValueError(error_msg % ([f['name'] for f in required_fields], credentials.keys()))

    def get_credential_fields(self, institution_id):
        """Get a dictionary of fields required to login
        to a specific institution.

        :param integer institution_id: The institution's id. See :ref:`search_for_institution`.
        :returns: ``list`` of credentials to present.

        ::

            >>> client.get_credential_fields(100000)
            >>> [{'description': 'Banking Userid',
                  'displayFlag': 'true',
                  'displayOrder': '1',
                  'instructions': 'Enter banking userid (demo)',
                  'mask': 'false',
                  'name': 'Banking Userid',
                  'status': 'Active',
                  'valueLengthMax': '20',
                  'valueLengthMin': '1'},
                 {'description': 'Banking Password',
                  'displayFlag': 'true',
                  'displayOrder': '2',
                  'instructions': 'Enter banking password (go)',
                  'mask': 'true',
                  'name': 'Banking Password',
                  'status': 'Active',
                  'valueLengthMax': '20',
                  'valueLengthMin': '1'}]

        The fields that are returned are already ordered by the `displayOrder` field. The `name` field
        goes into the html input tags name attribute. The `mask` field will let you know if it's a
        password field. The list above might convert to this html::

            <form method="POST" action="/login-to-bank/">
                <div>Enter banking userid (demo): <input type="text" name="Banking Userid" /></div>
                <div>Enter banking password (go): <input type="password" name="Banking Password" /></div>
                <input type="submit" value="Login to your bank" />
            </form>
        """
        fields = []

        response = self.get_institution_details(institution_id)
        t = etree.fromstring(response.content.to_xml())

        # remove all the namespaces for easier parsing and get all the keys
        t = etree.fromstring(self._remove_namespaces(t))
        keys = t.xpath('./keys/key')

        # extract the field name and value
        for key in keys:
            fields_data = {}
            for part in key.xpath('./*'):
                fields_data[part.tag] = part.text
            # only provide fields that should be displayed to the user
            if fields_data['displayFlag'] == 'true':
                fields.append(fields_data)

        # order by displayOrder
        fields = sorted(fields, key=lambda x: x['displayOrder'])

        return fields

    def get_institutions(self):
        """Get a list of financial instituions

        :returns: :class:`AccgatResponse`

        ::

            >>> institutions = client.get_institutions()
            >>> len(institutions)
            18716
            >>> institutions[0].institution_name
            'Carolina Foothills FCU Credit Card'

        .. note::

            This call takes a very long time! Once you get your ``institution_id``
            write it down so you don't forget it. Saving the output using
            :meth:`AggCatResponse.content.to_xml()` is a good idea.
        """
        return self._make_request('institutions')

    def get_institution_details(self, institution_id):
        """Get the details of a finanical institution

        :param integer institution_id: The institution's id. See :ref:`search_for_institution`.
        :returns: :class:`AccgatResponse`

        ::

            >>> r = client.get_institution_details()
            >>> r
            <AggCatResponse 200>
            >>> r.content
            <Institutiondetail object @ 0x110371f50>
            >>> r.content.institution_name
            'JP Morgan Chase Bank'
            >>> r.content.address.address1
            'P O Box 36520'
        """
        return self._make_request('institutions/%s' % institution_id)

    def discover_and_add_accounts(self, institution_id, **credentials):
        """Attempt to add the account with the credentials given

        :param integer institution_id: The institution's id. See :ref:`search_for_institution`.
        :param dictionary credentials: Credentials
        :returns: :class:`AccgatResponse`

        If a *challenge response is not required* it will look similar to the example below::

            >>> client.get_credential_fields(100000)
            >>> [{'description': 'Banking Userid',
                  'displayFlag': 'true',
                  'displayOrder': '1',
                  'instructions': 'Enter banking userid (demo)',
                  'mask': 'false',
                  'name': 'Banking Userid',
                  'status': 'Active',
                  'valueLengthMax': '20',
                  'valueLengthMin': '1'},
                 {'description': 'Banking Password',
                  'displayFlag': 'true',
                  'displayOrder': '2',
                  'instructions': 'Enter banking password (go)',
                  'mask': 'true',
                  'name': 'Banking Password',
                  'status': 'Active',
                  'valueLengthMax': '20',
                  'valueLengthMin': '1'}]
            >>> r = client.discover_and_add_accounts(100000, **{
                'Banking Userid': 'direct',
                'Banking Password': 'anyvalue',
               })
            >>> r
            <AggCatResponse 201>
            >>> r.content
            <Accountlist object [<Creditaccount object @ 0x10d12d790>,<Loanaccount object @ 0x10d12d810> ...] @ 0x10d12d710>

        If a *challenge response is required* we get a different result::

            >>> r = client.discover_and_add_accounts(100000, **{
                'Banking Userid': 'direct',
                'Banking Password': 'anyvalue',
               })
            >>> r
            <AggCatResponse 401>
            >>> r.content
            <Challenges object [<Challenge object @ 0x10d12d5d0>,<Challenge object @ 0x10d12d110> ...] @ 0x10d0ffc50>

        Notice that ``r.content`` is now a :class:`Challenges` object. Listing the challenges will give
        to the questions that must be asked to the user::

            >>> for c in r.content:
                    print c.text
            Enter your first pet's name:
            Enter your high school's name:

        You might convert this into an html form

        .. code-block:: html

            <form action="/login/confirm-challenge" method="POST>
                <div>Enter your first pet's name: <input type="text" name="response_1" /></div>
                <div>Enter your high school's name: <input type="text" name="response_2" /></div>
            </form>

            <input type="submit" value="Confirm Challenges" />
        """

        # validate the credentials passed
        self._validate_credentials(institution_id, **credentials)

        login_xml = self._generate_login_xml(**credentials)
        return self._make_request(
            'institutions/%s/logins' % institution_id,
            'POST',
            login_xml
        )

    def confirm_challenge(self, institution_id, challenge_session_id, challenge_node_id, responses):
        """Post challenge responses and add accounts

        :param integer institution_id: The institution's id. See :ref:`search_for_institution`.
        :param string challenge_session_id: The session id received from `AggcatResponse.headers` in :meth:`discover_and_add_accounts`
        :param string challenge_node_id: The session id received from `AggcatResponse.headers` in :meth:`discover_and_add_accounts`
        :param list responses: A list of responses, ex. ['Cats Name', 'First High School']
        :returns: An :class:`AggcatReponse` with attribute ``content`` being an :class:`AccountList`

        When using :meth:`discover_and_add_accounts` you might get a challenge response::

            >>> r = client.discover_and_add_accounts(100000, **{
                'Banking Userid': 'direct',
                'Banking Password': 'anyvalue',
               })
            >>> r
            <AggCatResponse 401>
            >>> r.content
            <Challenges object [<Challenge object @ 0x10d12d5d0>,<Challenge object @ 0x10d12d110> ...] @ 0x10d0ffc50>
            >>> r.headers
            {'challengenodeid': '10.136.17.82',
             'challengesessionid': 'c31c8a55-754e-4252-8212-b8143270f84f',
             'connection': 'close',
             'content-length': '275',
             'content-type': 'application/xml',
             'date': 'Mon, 12 Aug 2013 03:15:42 GMT',
             'intuit_tid': 'e41418d4-7b77-401e-a158-12514b0d84e3',
             'server': 'Apache/2.2.22 (Unix)',
             'status': '401',
             'via': '1.1 ipp-gateway-ap02'}

        * The ``challenge_session_id`` parameter comes from ``r.headers['challengesessionid']``
        * The ``challenge_node_id`` parameter comes from ``r.headers['challengenodeid']``

        Now confirm the challenge::

            >>> challenge_session_id = r.headers['challengesessionid']
            >>> challenge_node_id = r.headers['challengenodeid']
            >>> responses = ['Black Cat', 'Meow High School']
            >>> accounts = r.confirm_challenge(
                    1000000,
                    challenge_session_id,
                    challenge_node_id,
                    responses
                )
            >>> accounts
            <AggCatResponse 201>
            >>> accounts.content
            <Accountlist object [<Creditaccount object @ 0x10d12d790>,<Loanaccount object @ 0x10d12d810> ...] @ 0x10d12d710>
        """
        xml = self._generate_challenge_response(responses)

        headers = {
            'challengeNodeId': challenge_node_id,
            'challengeSessionId': challenge_session_id
        }

        return self._make_request(
            'institutions/%s/logins' % institution_id,
            'POST',
            xml,
            headers=headers
        )

    def get_customer_accounts(self):
        """Get a list of all current customer accounts

        :returns: :class:`AggcatResponse`

        This endpoint assumes that the customer accounts we are getting
        are for the one set in :ref:`initializing_client`::

            >>> r = ac.get_customer_accounts()
            >>> r.content
            <Accountlist object [<Investmentaccount object @ 0x1104779d0>,<Creditaccount object @ 0x110477d50> ...] @ 0x110477b10>
            >>> for account in r.content:
                    print account.account_nickname, account. account_number
            My Retirement 0000000001
            My Visa 4100007777
            My Mortgage 1000000001
            My Brokerage 0000000000
            My Roth IRA 2000004444
            My Savings 1000002222
            My Line of Credit 8000006666
            My CD 2000005555
            My Auto Loan 8000008888
            My Checking 1000001111

        .. note::
            Attributes on accounts very depending on account type. See `account reference
            in the Intuit documentation <https://developer.intuit.com/docs/0020_customeraccountdata/customer_account_data_api/0020_api_documentation/0035_getaccount>`_.
            Also note that when the XML gets objectified XML attributes like ``accountId`` get converted
            to ``account_id``
        """
        return self._make_request('accounts')

    def get_login_accounts(self, login_id):
        """Get a list of account belonging to a login

        :param integer login_id: Login id of the instiution. This can be retrieved from an account.
        :returns: :class:`AggcatResponse`

        You may have multiple logins. For example, a Fidelity Account and a Bank of America. This
        will allow you to get onlt the accounts for a specified login::

             >>> client.get_login_accounts(83850162)
             <AggCatResponse 200>
             >>> r.content
             <Accountlist object [<Investmentaccount object @ 0x1090c9bd0>,<Loanaccount object @ 0x1090c9890> ...] @ 0x1090c9b10>
             >>> len(r.content)
             10
             >>> r.content[0]
             <Investmentaccount object @ 0x1090c9bd0>

        .. note::

            Attributes on accounts very depending on account type. See `account reference
            in the Intuit documentation <https://developer.intuit.com/docs/0020_customeraccountdata/customer_account_data_api/0020_api_documentation/0035_getaccount>`_.
            Also note that when the XML gets objectified XML attributes like ``accountId`` get converted
            to ``account_id``
        """
        return self._make_request('logins/%s/accounts' % login_id)

    def get_account(self, account_id):
        """Get the details of an account

        :param integer account_id: the id of an account retrieved from :meth:`get_login_accounts`
            or :meth:`get_customer_accounts`.
        :returns: :class:`AggcatResponse`

        ::

             >>> r = client.get_account(400004540560)
             <AggCatResponse 200>
             >>> r.content
             <Investmentaccount object @ 0x1091cfc10>
             >>> r.content.account_id
             '400004540560'

        .. note::
            Attributes on accounts very depending on type. See `account reference
            in the Intuit documentation <https://developer.intuit.com/docs/0020_customeraccountdata/customer_account_data_api/0020_api_documentation/0035_getaccount>`_.
            Also note that when the XML gets objectified XML attributes like ``accountId`` get converted
            to ``account_id``
        """
        return self._make_request('accounts/%s' % account_id)

    def get_account_transactions(self, account_id, start_date, end_date=None):
        """Get specific account transactions from a date range

        :param integer account_id: the id of an account retrieved from :meth:`get_login_accounts`
            or :meth:`get_customer_accounts`.
        :param string start_date: the date you want the transactions to start in the format YYYY-MM-DD
        :param string end_date: (optional) the date you want the transactions to end in the format YYYY-MM-DD
        :returns: :class:`AggcatResponse`

        ::

            >>> r = ac.get_account_transactions(400004540560, '2013-08-10', '2013-08-12')
            >>> r
            <AggCatResponse 200>
            >>> r.content
            <Transactionlist object [<Investmenttransaction object @ 0x10a380710>,<Investmenttransaction object @ 0x10a380750> ...] @ 0x109ce8a50>
            >>> len(r.content)
            3
            >>> for t in r.content:
                    print t.id, t.description, t.total_amount, t.currency_type
            400189790351 IRA debit 222 -8.1 USD
            400190413930 IRA debit 224 -8.12 USD
            400190413931 IRA credit 223 8.11 USD

        .. note::
            Attributes on transactions very depending on transaction type. See `transaction reference
            in the Intuit documentation <https://developer.intuit.com/docs/0020_customeraccountdata/customer_account_data_api/0020_api_documentation/0030_getaccounttransactions>`_.
            When the XML gets objectified XML attributes like ``totalAmount`` get converted
            to ``total_amount``. This endpoint is not ordered by the date of transaction.

            **Pending** transactions are unstable, the transaction id will change once the it has
            posted so it is difficult to correlate a once pending transaction with its posted one.
        """
        query = {
            'txnStartDate': start_date,
        }

        # add the end date if provided
        if end_date:
            query.update({
                'txnEndDate': end_date
            })

        return self._make_request(
            'accounts/%s/transactions' % account_id,
            query=query
        )

    def get_investment_positions(self, account_id):
        """Get the investment positions of an account

        :param integer account_id: the id of an account retrieved from :meth:`get_login_accounts`
            or :meth:`get_customer_accounts`.
        :returns: :class:`AggcatResponse`

        ::

             >>> r = client.get_investment_positions(400004540560)
             <AggCatResponse 200>
             >>> r.content
             <Investmentpositions object @ 0x10a25ebd0>

        .. note::

            This endpoint has needs to be tested with an account that
            actually returns data here
        """
        return self._make_request('accounts/%s/positions' % account_id)

    def update_account_type(self, account_id, account_name, account_type):
        """Update an account's type

        :param integer account_id: the id of an account retrieved from :meth:`get_login_accounts`
            or :meth:`get_customer_accounts`.
        :param string account_name: See possible values for account names and types below
        :param string account_type: See possible values for account names and types below
        :returns: ``None``

        ::

             >>> client.update_account_type(400004540560, 'investment', '403b')

        **Possible values for account names and types**

        +------------+---------------------------------------------------------------------------------------------+
        | Name       | Types                                                                                       |
        +============+=============================================================================================+
        | banking    | checking, savings, moneymrkt, cd, cashmanagement, overdraft                                 |
        +------------+---------------------------------------------------------------------------------------------+
        | credit     | creditcard, lineofcredit, other                                                             |
        +------------+---------------------------------------------------------------------------------------------+
        | loan       | loan, auto, commercial, constr, consumer, homeequity, military, mortgage, smb, student      |
        +------------+---------------------------------------------------------------------------------------------+
        | investment | taxable, 401k, brokerage, ira, 403b, keogh, trust, tda, simple, normal, sarsep, ugma, other |
        +------------+---------------------------------------------------------------------------------------------+

        """
        body = AccountType(account_name, account_type).to_xml()

        return self._make_request(
            'accounts/%s' % account_id,
            'PUT',
            body
        )

    def update_institution_login(self, institution_id, login_id, refresh=True, **credentials):
        """Update an instiutions login information

        :param integer institution_id: The institution's id. See :ref:`search_for_institution`.
        :param string login_id: Login id of the instiution. This can be retrieved from an account.
        :param boolean refresh: (optional) Setting this to ``False`` will only update the credentials
            in intuit and will not query against the instituion. This might cause issues because some
            institutions require you to re-answer the challenge questions. Default: ``True``
        :param dict credentials: New credentials. See :ref:`getting_credential_fields`.
        :returns: :class:`None` if update is valid or :class:`AggcatResponse` if challenge occurs.

        If a challenge response does not occur::

            >>> r = ac.update_institution_login(100000, 83850162, **{
                    'Banking Userid': 'direct',
                    'Banking Password': 'anyvalue'
                })
            >>> type(r)
            NoneType

        If a challenge response occurs::

            >>> r = ac.update_institution_login(100000, 83850162, **{
                    'Banking Userid': 'tfa_choice',
                    'Banking Password': 'anyvalue'
                })
            >>> r
            <AggCatResponse 401>
            >>> r.content
            <Challenges object [<Challenge object @ 0x10d12d5d0>,<Challenge object @ 0x10d12d110> ...] @ 0x10d0ffc50>

        Notice that ``r.content`` is now a :class:`Challenges` object. Listing the challenges will give
        to the questions that must be asked to the user::

            >>> for c in r.content:
                    print c.text
            Enter your first pet's name:
            Enter your high school's name:

        You might convert this into an html form

        .. code-block:: html

            <form action="/login/confirm-challenge" method="POST>
                <div>Enter your first pet's name: <input type="text" name="response_1" /></div>
                <div>Enter your high school's name: <input type="text" name="response_2" /></div>
            </form>

            <input type="submit" value="Confirm Challenges" />
        """
        # check if we need to refresh against the financial institution
        query = {}
        if refresh:
            query = {'refresh': refresh}

        # validate the credentials passed
        self._validate_credentials(institution_id, **credentials)

        login_xml = self._generate_login_xml(**credentials)
        return self._make_request(
            'logins/%s' % login_id,
            'PUT',
            login_xml,
            query=query,
        )

    def update_challenge(self, login_id, challenge_session_id, challenge_node_id, responses, refresh=True):
        """Update an instiutions challenge information

        :param string login_id: Login id of the instiution. This can be retrieved from an account.
        :param string challenge_session_id: The session id received from `AggcatResponse.headers` in :meth:`discover_and_add_accounts`
        :param string challenge_node_id: The session id received from `AggcatResponse.headers` in :meth:`discover_and_add_accounts`
        :param list responses: A list of responses, ex. ['Cats Name', 'First High School']
        :param boolean refresh: (optional) Setting this to ``False`` will only update the credentials
            in intuit and will not query against the instituion. This might cause issues because some
            institutions require you to re-answer the challenge questions. Default: ``True``
        :returns: :class:`None`

        When using :meth:`update_institution_login` you might get a challenge response::

            >>> r = client.update_institution_login(100000, 83850162, **{
                'Banking Userid': 'tfa_choice',
                'Banking Password': 'anyvalue',
               })
            >>> r
            <AggCatResponse 401>
            >>> r.content
            <Challenges object [<Challenge object @ 0x10d12d5d0>,<Challenge object @ 0x10d12d110> ...] @ 0x10d0ffc50>
            >>> r.headers
            {'challengenodeid': '10.136.17.82',
             'challengesessionid': 'c31c8a55-754e-4252-8212-b8143270f84f',
             'connection': 'close',
             'content-length': '275',
             'content-type': 'application/xml',
             'date': 'Mon, 12 Aug 2013 03:15:42 GMT',
             'intuit_tid': 'e41418d4-7b77-401e-a158-12514b0d84e3',
             'server': 'Apache/2.2.22 (Unix)',
             'status': '401',
             'via': '1.1 ipp-gateway-ap02'}

        * The ``challenge_session_id`` parameter comes from ``r.headers['challengesessionid']``
        * The ``challenge_node_id`` parameter comes from ``r.headers['challengenodeid']``

        Now update the challenge::

            >>> challenge_session_id = r.headers['challengesessionid']
            >>> challenge_node_id = r.headers['challengenodeid']
            >>> responses = ['Black Cat', 'Meow High School']
            >>> r.update_challenge(
                    83850162,
                    challenge_session_id,
                    challenge_node_id,
                    responses
                )
        """
        xml = self._generate_challenge_response(responses)

        # check if we need to refresh against the financial institution
        query = {}
        if refresh:
            query = {'refresh': refresh}

        headers = {
            'challengeNodeId': challenge_node_id,
            'challengeSessionId': challenge_session_id
        }

        return self._make_request(
            'logins/%s' % login_id,
            'POST',
            xml,
            query=query,
            headers=headers
        )

    def delete_account(self, account_id):
        """Delete an account

        :param integer account_id: the id of an account retrieved from :meth:`get_login_accounts`
            or :meth:`get_customer_accounts`.
        :returns: `None`

        ::

             >>> r = client.delete_account(400004540560)

        """
        return self._make_request(
            'accounts/%s' % account_id,
            'DELETE'
        )

    def delete_customer(self):
        """Delete the current customer

        :returns: `None`

        .. warning::

            This deletes all information about the customer. You will have to re-authenticate and
            rediscover accounts. This endpoint assumes that the customer account getting deleted is
            the one set in :ref:`initializing_client`. Once this endpoint has been called **do not call**
            any other endpoints with this customer because the system will automatically create them again!

        ::

            >>> client.delete_customer()

        """

        return self._make_request(
            'customers',
            'DELETE'
        )

    def list_files(self):
        """List of files available for download that contain
        your bulk customer information"""
        raise NotImplementedError('Due to not having a production account available. That costs money.')

    def get_file_data(self, file_name, range=None):
        """The file data of `file_name` and `range` of bytes"""
        raise NotImplementedError('Due to not having a production account available. That costs money.')

    def delete_file(self, file_name):
        """Delete a file"""
        raise NotImplementedError('Due to not having a production account available. That costs money.')
