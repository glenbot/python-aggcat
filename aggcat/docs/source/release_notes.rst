Release Notes
-------------

**0.4**

* Updates to the docs

**0.3**

* Switched oAuth backend from ``oAuth2`` to ``requests-oauthlib`` because it is maintained and causing less issues. Plus, requests is awesome ;)

* Added ``verify_ssl`` keyword argument to :class:`AggcatClient` so that the library work under Python 2.6 due to an SSL library bug parsing Intuits SSL Certificate. See :ref:`known_issues`

* Added Counter backport for Python 2.6 `http://code.activestate.com/recipes/576611-counter-class/ <http://code.activestate.com/recipes/576611-counter-class/>`_

**0.2**

* Cleanup
* Made end_date an optional parameter in `get_account_transactions` to reflect intuit
* Added `requirements.pip` file do that docs build correctly on readthedocs.org

**0.1**

* Initial Release
