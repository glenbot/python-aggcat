"""
=============
Python Aggcat
=============

Python client for Intuit Customer Account Data APIs

::

    pip install python-aggcat

`See full documentation for quickstart <https://aggcat.readthedocs.org/en/latest/>`_
"""
from distutils.core import setup
__version__ = "0.6"


setup(
  author = 'Glen Zangirolami',
  author_email = 'glenbot@gmail.com',
  maintainer = 'Glen Zangirolami',
  maintainer_email = 'glenbot@gmail.com',
  description = 'Client for Intuit Customer Account Data APIs',
  long_description = __doc__,
  fullname = 'python-aggcat',
  name = 'python-aggcat',
  url = 'https://github.com/glenbot/python-aggcat',
  download_url = 'https://github.com/glenbot/python-aggcat',
  version = __version__,
  platforms = ['Linux'],
  packages = [
    'aggcat'
  ],
  install_requires = [
    'lxml==3.2.1',
    'M2Crypto==0.21.1',
    'requests==1.2.0',
    'requests-oauthlib==0.3.3'
  ],
  classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Other Environment',
    'Intended Audience :: Developers',
    'Operating System :: Unix',
    'Programming Language :: Python',
    'License :: OSI Approved :: MIT License'
  ]
)