from __future__ import absolute_import

import os
import sys
import ConfigParser
from datetime import datetime

from ..client import AggcatClient
from ..exceptions import HTTPError

from nose.tools import raises, nottest


class TestClient(object):
    """Test Aggcat Client"""
    @classmethod
    def setup_class(self):
        self.institution_id = 100000

        self.base_url = 'https://financialdatafeed.platform.intuit.com/rest-war/v1'
        self.config_file = os.path.join(os.environ['HOME'], '.aggcat_config')

        if not os.path.isfile(self.config_file):
            sys.exit('Please create an aggcat configuration file in ~/.aggcat_config to run tests.')

        client_config = ConfigParser.ConfigParser()
        client_config.readfp(open(self.config_file))

        self.client_args = (
            client_config.get('aggcat', 'consumer_key'),
            client_config.get('aggcat', 'consumer_secret'),
            client_config.get('aggcat', 'saml_identity_provider_id'),
            client_config.get('aggcat', 'customer_id'),
            client_config.get('aggcat', 'private_key'),
        )

        self.ac = AggcatClient(*self.client_args, objectify=True)

    @classmethod
    def teardown_class(self):
        self.ac.delete_customer()

    @nottest
    def get_data(self, file_name):
        with open('aggcat/tests/data/%s' % file_name, 'r') as f:
            return f.read()

    def test_client_setup(self):
        """Client Test: API parameters are setup"""
        consumer_key, consumer_secret, saml_identity_provider_id, \
            customer_id, private_key = self.client_args

        assert self.ac.consumer_key == consumer_key
        assert self.ac.consumer_secret == consumer_secret
        assert self.ac.saml_identity_provider_id == saml_identity_provider_id
        assert self.ac.customer_id == customer_id
        assert self.ac.private_key == private_key

    @nottest
    def _float_test(self, string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    @raises(HTTPError)
    def test_bad_account(self):
        """Client Test: Intuit bad/anyvalue account"""
        # Will use direct type transactions both debit and credit.
        self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'bad',
            'Banking Password': 'anyvalue'
        })

    @raises(HTTPError)
    def test_bad2_account(self):
        """Client Test: Intuit anyvalue/bad account"""
        # Will use direct type transactions both debit and credit.
        self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'anyvalue',
            'Banking Password': 'bad'
        })

    @raises(HTTPError)
    def test_request_error_account(self):
        """Client Test: Intuit request_error/anyvalue account"""
        # Will use direct type transactions both debit and credit.
        self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'request_error',
            'Banking Password': 'anyvalue'
        })

    def test_two_factor_q_account(self):
        """Client Test: Intuit tfa_text/anyvalue question account"""
        r = self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'tfa_text',
            'Banking Password': 'anyvalue'
        })

        assert r.content.to_xml() == self.get_data('api_two_factor_account.xml')

    def test_two_factor2_q_account(self):
        """Client Test: Intuit tfa_text2/anyvalue question account"""
        r = self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'tfa_text2',
            'Banking Password': 'anyvalue'
        })

        assert r.content.to_xml() == self.get_data('api_two_factor2_account.xml')

    def test_two_factor_choice_account(self):
        """Client Test: Intuit tfa_choice/anyvalue choice account"""
        r = self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'tfa_choice',
            'Banking Password': 'anyvalue'
        })

        assert r.content.to_xml() == self.get_data('api_two_factor_choice_account.xml')

    def test_two_factor_image_account(self):
        """Client Test: Intuit tfa_image/anyvalue image account"""
        r = self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'tfa_image',
            'Banking Password': 'anyvalue'
        })

        assert r.content.to_xml() == self.get_data('api_two_factor_image_account.xml')

    def test_two_factor_dynamic_image_account(self):
        """Client Test: Intuit tfa_dynamic_image/anyvalue dynamic image account"""
        r = self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'tfa_dynamic_image',
            'Banking Password': 'anyvalue'
        })

        assert r.content.to_xml() == self.get_data('api_two_factor_dynamic_image_account.xml')

    def test_get_credential_fields(self):
        """Client Test: Credential fields"""
        return_value = eval(self.get_data('api_get_credential_fields.list'))

        # get the serialized credential fields
        r = self.ac.get_credential_fields(self.institution_id)

        assert r == return_value
        assert r[0]['name'] == return_value[0]['name']
        assert r[1]['valueLengthMax'] == return_value[1]['valueLengthMax']
        assert r[0]['description'] == return_value[0]['description']
        assert r[1]['name'] == return_value[1]['name']

    def test_get_institution_details(self):
        """Client Test: Institution details"""
        r = self.ac.get_institution_details(self.institution_id)

        assert int(r.content.institution_id) == self.institution_id
        assert r.content.home_url == 'http://www.intuit.com'
        assert r.content.email_address == 'CustomerCentralBank@intuit.com'

    def test_url_building(self):
        """Client Test: URL building"""
        assert self.ac._build_url('institutions') == \
            '%s/%s' % (self.base_url, 'institutions')

    @raises(ValueError)
    def test_y0_credentials_validation_failure(self):
        """Client Test: Test if credentials passed are invalid"""
        self.ac._validate_credentials(self.institution_id, **{
            'baduser': 'badvalue',
            'badpass': 'badvalue',
        })

    @raises(HTTPError)
    def test_y01_get_account(self):
        """Client Test: Get account with bad account id"""
        self.ac.get_account('something_made_up')

    @raises(HTTPError)
    def test_y02_get_account_transactions(self):
        """Client Test: Get transactions with bad account id"""
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        self.ac.get_account_transactions('something_made_up', start_date, end_date)

    def test_z01_discover_and_add_accounts(self):
        """Client Test: Inuit discover and add direct/anyvalue accounts"""
        r = self.ac.discover_and_add_accounts(self.institution_id, **{
            'Banking Userid': 'direct',
            'Banking Password': 'anyvalue'
        })

        for account in r.content:
            assert int(account.institution_id) == self.institution_id

    def test_z02_get_customer_accounts(self):
        """Client Test: Get customer accounts"""
        r = self.ac.get_customer_accounts()

        for account in r.content:
            assert int(account.institution_id) == self.institution_id

    def test_z03_get_account(self):
        """Client Test: Get account"""
        accounts = self.ac.get_customer_accounts()
        r = self.ac.get_account(accounts.content[0].account_id)

        assert r.content.account_id == accounts.content[0].account_id

    def test_z04_get_account_transactions(self):
        """Client Test: Get account transactions"""
        accounts = self.ac.get_customer_accounts()

        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        r = self.ac.get_account_transactions(
            accounts.content[0].account_id,
            start_date,
            end_date
        )

        for t in r.content:
            assert self._float_test(t.amount) == True

    @raises(HTTPError)
    def test_z05_get_account_transactions_bad_date(self):
        """Client Test: Get account transactions with bad date"""
        accounts = self.ac.get_customer_accounts()

        self.ac.get_account_transactions(
            accounts.content[0].account_id,
            'some_bad_date',
            'some_bad_date'
        )

    @raises(HTTPError)
    def test_z06_delete_account_bad_id(self):
        """Client Test: Delete account with bad id"""
        self.ac.delete_account('some_bad_account_id')

    def test_z07_delete_account(self):
        """Client Test: Delete account"""
        accounts = self.ac.get_customer_accounts()

        r = self.ac.delete_account(accounts.content[0].account_id)

        assert r.content == ''
        assert r.status_code == 200

    def test_z08_get_login_accounts(self):
        """Client Test: Get login accounts"""
        accounts = self.ac.get_customer_accounts()

        r = self.ac.get_login_accounts(accounts.content[0].institution_login_id)

        for account in r.content:
            assert int(account.institution_id) == self.institution_id

    def test_z09_get_investement_positions(self):
        """Client Test: Get investement positions"""
        accounts = self.ac.get_customer_accounts()

        r = self.ac.get_investment_positions(accounts.content[0].account_id)

        assert r.content.to_xml() == self.get_data('api_get_investment_positions.xml')

    @raises(ValueError)
    def test_z10_update_account_type_invalid_params(self):
        """Client Test: Update account type invalid params"""

        self.ac.update_account_type(1000000000, 'banking', 'bad_type')

    @raises(HTTPError)
    def test_z11_update_account_type(self):
        """Client Test: Update account type"""
        accounts = self.ac.get_customer_accounts()

        self.ac.update_account_type(accounts.content[0].account_id, 'banking', 'cashmanagement')

    def test_z12_update_institution_login(self):
        """Client Test: Update institution login"""
        accounts = self.ac.get_customer_accounts()

        r = self.ac.update_institution_login(
            self.institution_id,
            accounts.content[0].institution_login_id,
            **{
            'Banking Userid': 'direct',
            'Banking Password': 'anyvalue'
        })

        assert r.content == ''
        assert r.status_code == 200

    @raises(HTTPError)
    def test_z13_update_institution_login(self):
        """Client Test: Update institution login"""
        accounts = self.ac.get_customer_accounts()

        self.ac.update_institution_login(
            self.institution_id,
            accounts.content[0].institution_login_id,
            **{
            'Banking Userid': '',
            'Banking Password': ''
        })

    @raises(NotImplementedError)
    def test_z14_list_files(self):
        """Client Test: List files"""
        self.ac.list_files()

    @raises(NotImplementedError)
    def test_z15_get_file_data(self):
        """Client Test: Get file data"""
        self.ac.get_file_data('fake_file_name.gz')

    @raises(NotImplementedError)
    def test_z16_delete_file(self):
        """Client Test: Delete file"""
        self.ac.delete_file('fake_file_name.gz')
