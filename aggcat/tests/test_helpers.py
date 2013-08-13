from __future__ import absolute_import

from ..helpers import AccountType

from nose.tools import raises, nottest


class TestHelpers(object):
    """Test Helpers"""
    @nottest
    def get_data(self, file_name):
        with open('aggcat/tests/data/%s' % file_name, 'r') as f:
            return f.read()

    @raises(ValueError)
    def test_invalid(self):
        """Helper Test: Invalid account type"""
        AccountType('banking', 'bad_data').to_xml()

    @raises(ValueError)
    def test_invalid2(self):
        """Helper Test: Invalid account name"""
        AccountType('bad_data', 'bad_data').to_xml()

    def test_valid(self):
        """Helper Test: Valid account type xml"""
        a = AccountType('banking', 'checking')
        assert a.to_xml() == self.get_data('helper_account_type.xml')
