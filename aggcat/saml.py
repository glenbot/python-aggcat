import base64
import re
from datetime import datetime
from datetime import timedelta
from uuid import uuid4
from hashlib import sha1

import M2Crypto

# replace newlines before encrypting
pattern = re.compile(r'>[\n\s]+<', re.I | re.M)

SAML_ASSERTION = """
<saml2:Assertion xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" ID="_%(assertion_id)s" IssueInstant="%(iso_now)s" Version="2.0">
  <saml2:Issuer>%(saml_identity_provider_id)s</saml2:Issuer>%(signature)s<saml2:Subject>
    <saml2:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified">%(customer_id)s</saml2:NameID>
    <saml2:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer"></saml2:SubjectConfirmation>
  </saml2:Subject>
  <saml2:Conditions NotBefore="%(iso_not_before)s" NotOnOrAfter="%(iso_not_after)s">
    <saml2:AudienceRestriction>
      <saml2:Audience>%(saml_identity_provider_id)s</saml2:Audience>
    </saml2:AudienceRestriction>
  </saml2:Conditions>
  <saml2:AuthnStatement AuthnInstant="%(iso_now)s" SessionIndex="_%(assertion_id)s">
    <saml2:AuthnContext>
      <saml2:AuthnContextClassRef>urn:oasis:names:tc:SAML:2.0:ac:classes:unspecified</saml2:AuthnContextClassRef>
    </saml2:AuthnContext>
  </saml2:AuthnStatement>
</saml2:Assertion>
"""
SAML_ASSERTION = re.sub(pattern, '><', SAML_ASSERTION).strip()

SAML_SIGNED_INFO = """
<ds:SignedInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"></ds:CanonicalizationMethod>
    <ds:SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"></ds:SignatureMethod>
    <ds:Reference URI="#_%(assertion_id)s">
        <ds:Transforms>
            <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"></ds:Transform>
            <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"></ds:Transform>
        </ds:Transforms>
        <ds:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"></ds:DigestMethod>
        <ds:DigestValue>%(signed_digest_value)s</ds:DigestValue>
    </ds:Reference>
</ds:SignedInfo>
"""
SAML_SIGNED_INFO = re.sub(pattern, '><', SAML_SIGNED_INFO).strip()

SAML_SIGNATURE = """
<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    <ds:SignedInfo>
        <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
        <ds:SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
        <ds:Reference URI="#_%(assertion_id)s">
            <ds:Transforms>
                <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
                <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
            </ds:Transforms>
            <ds:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
                <ds:DigestValue>%(signed_digest_value)s</ds:DigestValue>
        </ds:Reference>
    </ds:SignedInfo>
    <ds:SignatureValue>%(signed_signature_value)s</ds:SignatureValue>
</ds:Signature>
"""
SAML_SIGNATURE = re.sub(pattern, '><', SAML_SIGNATURE).strip()


class SAML(object):
    """Create authentication assertions using SAML format"""
    def __init__(self, private_key, saml_identity_provider_id, customer_id):
        # RSA key file to use for signing
        self.rsa = M2Crypto.RSA.load_key(private_key)
        self.now = datetime.utcnow()
        self.iso_now = '%sZ' % self.now.isoformat()
        self.assertion_id = uuid4().hex
        self.saml_identity_provider_id = saml_identity_provider_id

        # customer id must be the same for a customer accessing the API
        # You should use a unique username, primary key, or uuid for this
        self.customer_id = customer_id

        # authentication url
        self.saml_url = 'https://oauth.intuit.com/oauth/v1/get_access_token_by_saml'

    def _signed_digest_value(self):
        """Get the digest value of the SAML assertion"""
        assertion = SAML_ASSERTION % {
            'assertion_id': self.assertion_id,
            'iso_now': self.iso_now,
            'saml_identity_provider_id': self.saml_identity_provider_id,
            'customer_id': self.customer_id,
            'iso_not_before': '%sZ' % (self.now - timedelta(minutes=5)).isoformat(),
            'iso_not_after': '%sZ' % (self.now + timedelta(minutes=10)).isoformat(),
            'signature': '',
        }
        return base64.b64encode(sha1(assertion).digest()).strip()

    def _signed_signature_value(self, signed_digest_value):
        """Get the signature value for the SAML signature"""
        signed_info = SAML_SIGNED_INFO % {
            'assertion_id': self.assertion_id,
            'signed_digest_value': signed_digest_value,
        }
        return base64.b64encode(self.rsa.sign(sha1(signed_info).digest(), 'sha1'))

    def refresh(self):
        """Refresh the values to generate another assertion"""
        self.now = datetime.utcnow()
        self.iso_now = '%sZ' % self.now.isoformat()
        self.assertion_id = uuid4().hex

    def assertion(self):
        """Generate and return a SAML assertion"""
        signed_digest_value = self._signed_digest_value()
        signed_signature_value = self._signed_signature_value(signed_digest_value)

        # add the signed value to the signature
        signature = SAML_SIGNATURE % {
            'signed_signature_value': signed_signature_value,
            'signed_digest_value': signed_digest_value,
            'assertion_id': self.assertion_id
        }

        # return the complete saml assertion
        b64_assertion = base64.b64encode(SAML_ASSERTION % {
            'assertion_id': self.assertion_id,
            'iso_now': self.iso_now,
            'saml_identity_provider_id': self.saml_identity_provider_id,
            'customer_id': self.customer_id,
            'iso_not_before': '%sZ' % (self.now - timedelta(minutes=5)).isoformat(),
            'iso_not_after': '%sZ' % (self.now + timedelta(minutes=10)).isoformat(),
            'signature': signature,
        })

        return b64_assertion
