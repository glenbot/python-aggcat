from __future__ import absolute_import

from ..parser import Objectify


class TestParser(object):
    """Test XML Objectification"""
    @classmethod
    def setup_class(self):
        self.o = None
        with open('aggcat/tests/data/sample_xml.xml', 'r') as f:
            self.o = Objectify(f.read()).get_object()

    def test_lists(self):
        """Parser Test: Lists object added are correct"""
        assert hasattr(self.o, '_list')
        assert isinstance(self.o._list, list) == True
        assert len(self.o) == 2
        assert len(self.o[0].ingredients) == 2
        assert len(self.o[1].ingredients) == 3

    def test_attributes(self):
        """Parser Test: object attributes created have correct value"""
        assert hasattr(self.o[0], 'name')
        assert hasattr(self.o[0], 'ingredients')
        assert hasattr(self.o[0], 'cook_time')
        assert self.o[0].name == 'Fried Pickles'
        assert self.o[0].ingredients[0].name == 'Flour'
        assert self.o[1].name == 'Smoked Bacon'
        assert self.o[1].ingredients[0].name == 'Bacon'
