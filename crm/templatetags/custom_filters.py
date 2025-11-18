from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup dictionary values by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def get_item(dictionary, key):
    """Alternative filter name for dictionary lookup"""
    return lookup(dictionary, key)