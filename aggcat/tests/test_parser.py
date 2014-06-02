from __future__ import absolute_import

from ..xml_parser import XmlObjectify
from ..json_parser import JsonObjectify


class TestParser(object):
    """Test XML Objectification"""
    @classmethod
    def setup_class(self):
        self.o = None
        self.j = None
        with open('aggcat/tests/data/sample_xml.xml', 'r') as f:
            self.o = XmlObjectify(f.read()).get_object()
        
        with open('aggcat/tests/data/sample_json.json', 'r') as fp:
            self.j = JsonObjectify(fp.read()).get_object()

    def test_lists(self):
        """Parser Test: Lists object added are correct"""
        assert hasattr(self.o, '_list')
        assert isinstance(self.o._list, list) == True
        assert len(self.o) == 2
        assert len(self.o[0].ingredients) == 2
        assert len(self.o[1].ingredients) == 3
        
        assert hasattr(self.j, '_list')
        assert isinstance(self.j._list, list) == True
        assert len(self.j) == 2
        assert len(self.j[0].ingredients) == 2
        assert len(self.j[1].ingredients) == 3

    def test_attributes(self):
        """Parser Test: object attributes created have correct value"""
        assert hasattr(self.o[0], 'name')
        assert hasattr(self.o[0], 'ingredients')
        assert hasattr(self.o[0], 'cook_time')
        assert self.o[0].name == 'Fried Pickles'
        assert self.o[0].ingredients[0].name == 'Flour'
        assert self.o[1].name == 'Smoked Bacon'
        assert self.o[1].ingredients[0].name == 'Bacon'
        
        assert hasattr(self.j[0], 'name')
        assert hasattr(self.j[0], 'ingredients')
        assert hasattr(self.j[0], 'cook_time')
        assert self.j[0].name == 'Fried Pickles'
        assert self.j[0].ingredients[0].name == 'Flour'
        assert self.j[1].name == 'Smoked Bacon'
        assert self.j[1].ingredients[0].name == 'Bacon'
        
        try:
            self.j[0].bad_attr
            assert False
        except AttributeError:
            pass
        
        try:
            self.j[123]
            assert False
        except IndexError:
            pass
