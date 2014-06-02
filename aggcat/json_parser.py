from __future__ import absolute_import

import json

from .parser import ObjectifyBase

__all__ = ['JsonObjectify']

def _repr(self):
    if hasattr(self, '_list'):
        ls = [repr(l) for l in self._list[:2]]
        return '<{} object [{} ...] @ {}>'.format(self._name, ','.join(ls), hex(id(self)))
    else:
        return '<{} object @ {}>'.format(self._name, hex(id(self)))

def _objectify_getattr(self, name):
    
    if name in self.__dict__:
        return self.__dict__[name]
    
    if name in self._keys:
        tree = self._tree.pop(self._keys[name])
        
        if isinstance(tree, (list, tuple)):
            obj = self.__parent__._create_list_object(name, tree)
            name = obj._name
        elif isinstance(tree, dict):
            obj = self.__parent__._create_object(name, tree)
            name = obj._name
        else:
            obj = tree
        
        self.__dict__[name] = obj
        return obj
        
    return getattr(super(type(self), self), name)

def _objectify_getitem(self, idx):
        obj = self._list[idx]
        if not hasattr(obj, '_name'):
            name = '{}item'.format(self.__class__.__name__.lower())
            
            if isinstance(obj, (list, tuple)):
                obj = self.__parent__._create_list_object(name, obj)
            else:
                obj = self.__parent__._create_object(name, obj)
            
            self._list[idx] = obj
        return obj

class JsonObjectify(ObjectifyBase):
    application_type = 'application/json'
    error_type = ValueError
    
    def __init__(self, json_str):
        json_data = json.loads(json_str) #: :type json_data: dict
        
        assert len(json_data.keys()) == 1, "There can be only one (root)"
        
        root_tag, tree = json_data.popitem()
        
        if isinstance(tree, (list, tuple)):
            self.obj = self._create_list_object(root_tag, tree)
        else:
            self.obj = self._create_object(root_tag, tree = tree)
    
    def _create_object(self, name, tree = None, attributes = None, bases = None):
        name = self.clean_tag_name(name)
        
        if attributes is None:
            attributes = {}
        
        if bases is None:
            bases = (object,)
        
        attributes.update({
            '__parent__' : self,
            '_name' : name,
            '__repr__' : _repr,
            '__getattr__' : _objectify_getattr,
            '_keys' : [],
            '_tree' : tree
        })
        
        if tree is not None:
            attributes['_keys'] = {
                self.clean_tag_name(k) : k for k in tree.keys()
            }
        
        return type(str(name.capitalize()), bases, attributes)()
    
    def _create_list_object(self, name, list_objects = None):
        if list_objects is None:
            list_objects = []
        
        obj = self._create_object(name, attributes = {
            '__parent__' : self,
            '_list' : [],
            '__len__' : lambda this: len(this._list),
            '__iter__' : lambda this: iter(this._list),
            '__getitem__' : _objectify_getitem
        }, bases = (list,))
        
        obj._list = list_objects
        return obj
        
    
    def get_object(self):
        return self.obj
        
