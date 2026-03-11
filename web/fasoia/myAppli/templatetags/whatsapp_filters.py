from django import template
from urllib.parse import quote

register = template.Library()

@register.filter
def urlencode(value):
    """Encode une chaîne pour une URL"""
    return quote(value)