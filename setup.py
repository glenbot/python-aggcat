"""
=============
Python Aggcat
=============

Python client for Intuit Customer Account Data APIs
"""
from distutils.core import setup
__version__ = "0.1"


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
    'requests==1.2.0'
  ],
  classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Server Environment',
    'Intended Audience :: Developers',
    'Operating System :: Linux',
    'Programming Language :: Python',
    'License :: OSI Approved :: MIT License'
  ]
)