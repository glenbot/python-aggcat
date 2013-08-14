from __future__ import absolute_import

import re
from lxml import etree

try:
    from collections import Counter
except ImportError:
    from .counter import Counter

from .utils import remove_namespaces


def _get_item(self, index):
    return self._list[index]


def _len(self):
    return len(self._list)


def _iter(self):
    return iter(self._list)


def _repr(self):
    if hasattr(self, '_list'):
        ls = [repr(l) for l in self._list[:2]]
        return '<%s object [%s ...] @ %s>' % (self._name, ','.join(ls), hex(id(self)))
    else:
        return '<%s object @ %s>' % (self._name, hex(id(self)))


class Objectify(object):
    """Take XML output and turn it into a Pythonic Object
    The goals are to:
       * Provide an object that resembles the XML structure
       * Have the ability to go back to XML from the object
    """
    def __init__(self, xml):
        # raw xml
        self.xml = xml

        # parse the tree with lxml
        self.tree = etree.fromstring(remove_namespaces(etree.XML(xml)))

        # regex pattern for tag name cleanup
        self.tag_pattern = re.compile("(?!^)([A-Z]+)")

        self.root_tag = self.tree.tag

        # create a base object wrapper
        self.obj = self._create_object('Objectified XML')

        # check to see this is only one node with no children
        # Ex. get_customer_accounts is empty
        if not self.tree.getchildren():
            self.obj = self._create_object(self.tree.tag)
        else:
            self._walk_and_objectify(self.tree, self.obj)

    def _create_object(self, name, attributes={}):
        """Dynamically create an object"""
        attributes.update({
            '_name': name.capitalize(),
            '__repr__': _repr
        })
        return type(name.capitalize(), (object,), attributes)()

    def _create_list_object(self, name):
        """Dynamically create an object that has list type functionality"""
        return self._create_object(name, {
            '_list': [],
            '__len__': _len,
            '__iter__': _iter,
            '__getitem__': _get_item
        })

    def _clean_tag_name(self, tag_name):
        """Convert the CamelCase format of tag name to
        a camel_case format"""
        return re.sub(self.tag_pattern, r'_\1', tag_name).lower()

    def _is_list_xml(self, element):
        """Detect if the next set of XML elements contain duplicates
        which means it is a listable set of elements"""
        tags = []
        for e in element.xpath('./*'):
            tags.append(e.tag)

        for count in Counter(tags).values():
            if count > 1:
                return True

        return False

    def _walk_and_objectify(self, element, obj):
        """Walk the XML tree recursively and make objects out of the structure"""
        if element.getchildren():
            # look ahead and create a list object instead
            needs_list_obj = self._is_list_xml(element)

            if needs_list_obj:
                new_obj = self._create_list_object(element.tag)
            else:
                new_obj = self._create_object(element.tag)

            obj_attr_value = getattr(obj, element.tag, None)
            has_list = hasattr(obj, '_list')

            if obj_attr_value is None and not has_list:
                setattr(obj, element.tag, new_obj)
            else:
                l = getattr(obj, '_list')
                l.append(new_obj)
                setattr(obj, '_list', l)

            for child in element.getchildren():
                self._walk_and_objectify(child, new_obj)
        else:
            setattr(obj, self._clean_tag_name(element.tag), element.text)

    def get_object(self):
        root_obj = self.obj

        if hasattr(self.obj, self.root_tag):
            root_obj = getattr(self.obj, self.root_tag)

        # sometimes there is only one attribute that is a converted object
        # return this one instead of the surrounding object. I am not
        # sure this is the desired result, but i'll leave it for now
        appended_attrs = [
            k for k
            in root_obj.__dict__.iterkeys()
            if not k.startswith('_') and not '_' in k
        ]
        if len(appended_attrs) == 1:
            root_obj = getattr(root_obj, appended_attrs.pop())

        # append the to_xml() attribute to you can easily get the xml from the root object
        root_obj.to_xml = lambda: self.xml

        return root_obj
