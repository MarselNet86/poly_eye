from django import template

register = template.Library()


@register.filter
def getattribute(obj, attr):
    """Get an attribute from an object dynamically."""
    return getattr(obj, attr, None)
