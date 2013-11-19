

class AccountType(object):
    """Create an account update XML used to update account
    types from account name and type"""
    def __init__(self, account_name, account_type):
        self.account_name = account_name.lower()
        self.account_type = account_type.lower()

        self._types = {
            'banking': [
                'CHECKING',
                'SAVINGS',
                'MONEYMRKT',
                'CD',
                'CASHMANAGEMENT',
                'OVERDRAFT'
            ],
            'credit': [
                'CREDITCARD',
                'LINEOFCREDIT',
                'OTHER'
            ],
            'loan': [
                'LOAN',
                'AUTO',
                'COMMERCIAL',
                'CONSTR',
                'CONSUMER',
                'HOMEEQUITY',
                'MILITARY',
                'MORTGAGE',
                'SMB',
                'STUDENT'
            ],
            'investment': [
                'TAXABLE',
                '401K',
                'BROKERAGE',
                'IRA',
                '403B',
                'KEOGH',
                'TRUST',
                'TDA',
                'SIMPLE',
                'NORMAL',
                'SARSEP',
                'UGMA',
                'OTHER'
            ]
        }

    def validate(self):
        """Validate the account name and type"""
        if self.account_name not in self._types.keys():
            raise ValueError('Account name could not be found. Please use on of the following values %s' % self._types.keys())

        if self.account_type.upper() not in self._types[self.account_name]:
            raise ValueError('Account type could not be found. Valid account types for "%s" are %s' % (self.account_name, self._types[self.account_name],))

    def to_xml(self):
        """Return the XML required to update account"""
        self.validate()
        xml = '<ns4:%sAccount xmlns:ns4="http://schema.intuit.com/platform/fdatafeed/%saccount/v1"><ns4:%sAccountType>%s</ns4:%sAccountType></ns4:%sAccount>' % (
            self.account_name.capitalize(),
            self.account_name,
            self.account_name,
            self.account_type,
            self.account_name,
            self.account_name.capitalize()
        )

        return xml
