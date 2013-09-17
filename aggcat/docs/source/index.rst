.. AggCat documentation master file, created by
   sphinx-quickstart on Sun Aug 11 15:21:54 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Quick Start
===========

Ready to get your financial data? This quickstart is intended to get you setup to start using `Intuit's Customer Account Data API <https://developer.intuit.com/#CustomerAccountDataAPI>`_.

Before Using The API Client
---------------------------

You must take a few steps on Intuit's website before using the API client:

1. `Create a development account <https://developer.intuit.com/>`_ and login.
2. `Create a new application <https://developer.intuit.com/Application/Create>`_ in the Customer Account Data category. It's easiest to `follow the instructions in the help documentation <https://developer.intuit.com/docs/0020_customeraccountdata/009_using_customeraccountdata/0010_gettingstarted/0015_create_an_cad_integration>`_.
3. `Create and upload self a generated x509 certificate to your application <https://developer.intuit.com/docs/0020_customeraccountdata/009_using_customeraccountdata/0010_gettingstarted/0015_create_an_cad_integration/0010_creating_x.509_public_certificates>`_. It's easiest to use openssl to generate the certificate. *It's best to name your key the same as your application name*. **Don't lose these certificates!**
4. `Gather the login details <https://developer.intuit.com/Application/List>`_ and store them somewhere. You will need *OAuth Consumer Key*, *Oauth Consumer Secret*, *SAML Identity Provider ID*

Installation
------------

::

    pip install python-aggcat


.. _known_issues:

Known Issues
------------

The SSL library in Python 2.6 and below has a bug and will not parse the ``AlternativeNames`` out of the Intuit SSL cert causing a name mismatch during cetificate validation. For now, please pass ``verify_ssl = False`` to the :class:`AggcatClient` when initializing it. While less secure, I wanted the verification to be turned off explictly so you are aware. If possible, upgrade to Python 2.7+.

Initializing the API Client
---------------------------

Assuming you have an *OAuth Consumer Key*, *Oauth Consumer Secret*, *SAML Identity Provider ID*, and a path to the x509 certificates you generated you are ready to start querying::

    from aggcat import AggcatClient

    client = AggcatClient(
        'oauth_consumer_key',
        'oauth_consumer_secret',
        'saml_identity_provider_id',
        'customer_id',
        '/path/to/x509/appname.key'
    )

.. note::

    ``customer_id`` (Integer) It can be any integer. You should try using the database primary key
    of a user in your system or some other unique identifier such as a guid.
    If you are just testing you can use whatever integer you want.

    ``objectify`` (Boolean) This is a BETA functionality. It will objectify the XML returned from
    intuit into standard python objects so you don't have to mess with XML. Default: ``True``

Querying the API
----------------

Here are a few sample queries that don't require you to add an account

Getting all institutions
^^^^^^^^^^^^^^^^^^^^^^^^

::

    institutions = client.get_institutions()

.. note ::

    This query will take a very long time depending on your internet connection. It returns 18000+ institutions in XML format. Sux :(

If you are using the ``objectify = True`` keyword argument on the client you can access the institutions in a pythonic way

::
    
    >>> institutions = client.get_institutions()
    >>> len(institutions.content)
    18716
    >>> institutions.content[0].institution_name
    'Carolina Foothills FCU Credit Card'

Searching for your institution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: search_inst.rst

Getting the institution details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From the previous search example, we can use 13728 to get the institution details

::

    institution_details = client.get_institution_details(13278)

::
    
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?><InstitutionDetail xmlns="http://schema.intuit.com/platform/fdatafeed/institution/v1" xmlns:ns2="http://schema.intuit.com/platform/fdatafeed/common/v1"><institutionId>13278</institutionId><institutionName>JP Morgan Chase Bank</institutionName><homeUrl>https://www.chase.com/</homeUrl><phoneNumber>1-877-242-7372</phoneNumber><address><ns2:address1>P O Box 36520</ns2:address1><ns2:address2>Suite IL1-0291</ns2:address2><ns2:city>Louisville</ns2:city><ns2:state>KY</ns2:state><ns2:postalCode>40233</ns2:postalCode><ns2:country>USA</ns2:country></address><emailAddress>http://www.chase.com/cm/cs?pagename=Chase/Href&amp;urlname=chase/cc/contactus/email</emailAddress><specialText>Please enter your JP Morgan Chase Bank User ID and Password required for login.</specialText><currencyCode>USD</currencyCode><keys><key><name>usr_password</name><status>Active</status><displayFlag>true</displayFlag><displayOrder>2</displayOrder><mask>true</mask><description>Password</description></key><key><name>usr_name</name><status>Active</status><displayFlag>true</displayFlag><displayOrder>1</displayOrder><mask>false</mask><description>User ID</description></key></keys></InstitutionDetail>

If you are using the ``objectify = True`` keyword argument on the client you can access the institution parameters in a Pythonic way

::

    >>> institution = client.get_institution_details(13278)
    >>> institution
    <AggCatResponse 200>
    >>> institution.content
    <Institutiondetail object @ 0x10ddfa4d0>
    >>> institution.content.institution_name
    'JP Morgan Chase Bank'
    >>> institution.content.home_url
    'https://www.chase.com/'
    >>> institution.currency_code
    'USD'

User's Guide
------------

.. toctree::
   :maxdepth: 3

   api

.. include:: release_notes.rst
