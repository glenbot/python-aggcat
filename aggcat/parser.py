import re

__all__ = ['ObjectifyBase']

tag_pattern = re.compile("(?!^)(401[kK]|[A-Z]+)")

class ObjectifyBase(object):
    
    application_type = ''
    error_type = Exception
    
    def get_object(self):
        raise NotImplementedError()
    
    def clean_tag_name(self, tag_name):
        """Convert the CamelCase format of tag name to
        a camel_case format"""
        return re.sub(tag_pattern, r'_\1', tag_name).lower()
