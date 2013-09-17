Currently finding an institution is somewhat of a manual process. Soon, there will be a helper method on the client that will have a better search. Patches welcome ;). This example searches for an institution that contains "chase" in any of the XML elements::

    from aggcat import AggcatClient
    from lxml import etree
    from aggcat.utils import remove_namespaces

    client = AggcatClient(
        'oauth_consumer_key',
        'oauth_consumer_secret',
        'saml_identity_provider_id',
        'customer_id',
        '/path/to/x509/appname.key'
    )

    search_string = 'Chase'
    institutions = client.get_institutions()

    xml = etree.fromstring(institutions.content.to_xml())
    xml = etree.fromstring(remove_namespaces(xml))

    for element in xml.xpath('./institution[contains(., "chase")]'):
        id = element.xpath('./institutionId')[0].text
        name = element.xpath('./institutionName')[0].text
        print id, name

::

    13278 JP Morgan Chase Bank
    13640 Quicken Visa
    14554 Chase Bank Credit Card (Amazon.com)
    14910 Chase e-Funds Card
    14777 Fox Chase Bank - Business Banking
    13718 Fox Chase Bank
    14484 Chevy Chase Bank - Web Cash Manager
    ...

.. note ::

    This query will take a very long time depending on your internet connection. It returns 18000+ institutions in XML format. Sux :(