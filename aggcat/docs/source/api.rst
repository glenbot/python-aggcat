API
===

.. _initializing_client:

Initializing the client
-----------------------

.. autoclass:: aggcat.AggcatClient

.. _getting_credential_fields:

Authorization & updating credentials
------------------------------------

Getting credential fields
^^^^^^^^^^^^^^^^^^^^^^^^^

At some point in time you will need to allow a user to login to an institution so you can get their account information. :meth:`get_credential_fields` is not part of Intuit's API, but aids you in getting the fields you need to present in your UI layer.

To get credential fields use :meth:`get_credential_fields`. It will give you the fields in a ``list`` format pre-ordered. It's a precursor to :meth:`discover_and_add_accounts`

.. automethod:: aggcat.AggcatClient.get_credential_fields

Authenticating and adding accounts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you have gathered the username and password for a specific institution you well need to :meth:`discover_and_add_accounts`. This particular endpoint will either return a list of accounts if authentication works or return a list of challanges that need to be answered.

.. automethod:: aggcat.AggcatClient.discover_and_add_accounts

Responding to a challenge
^^^^^^^^^^^^^^^^^^^^^^^^^

If you attempted to authenticate and received back a :class:`Challenge` response the you will need to answer that challenge by sending your responses to :meth:`confirm_challenge`

.. automethod:: aggcat.AggcatClient.confirm_challenge

Updating outdated login credentials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have changed your institution credentials you will need to let Intuit know that it needs to use new credentials. For example, let's assume you have a Bank of America or JP Morgan Chase account and changed your password from the banking web site. At this point Intuit will need to be notified of this update.

.. automethod:: aggcat.AggcatClient.update_institution_login

Updating outdated challenge responses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.update_challenge


Working with Institutions
-------------------------

Getting all Institutions
^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.get_institutions

.. _search_for_institution:

Searching for your institution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: search_inst.rst

Getting Institution details
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.get_institution_details


Accounts & Account transactions
-------------------------------

Here is the meat of the API. This is what you came for, the ability to aggregate your financials. Here be dragons or not. :)

Customer accounts
^^^^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.get_customer_accounts

Login Accounts
^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.get_login_accounts


Single Account Details
^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.get_account

Transactions
^^^^^^^^^^^^

This might hurt or be candy to your eyes depending on how good of a budgeter you are. heh!

.. automethod:: aggcat.AggcatClient.get_account_transactions

Investement Positions
^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.get_investment_positions

Updating Account Type
^^^^^^^^^^^^^^^^^^^^^

Certain banks do not present account types in any of the API data or data that comes back from
screen scraping banks accounts without APIs. In those cases the account types are noted as "Other".
Most likely, you will know what the account actually is so you can update the type here.

.. automethod:: aggcat.AggcatClient.update_account_type

Deleting An Account
^^^^^^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.delete_account

Deleting a customer
^^^^^^^^^^^^^^^^^^^

.. automethod:: aggcat.AggcatClient.delete_customer
