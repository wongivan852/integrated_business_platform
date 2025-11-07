"""
Custom template tags and filters for admin_panel
"""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Template filter to get item from dictionary.
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
