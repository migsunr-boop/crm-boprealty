from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """Split a string by delimiter"""
    if value:
        return [item.strip() for item in value.split(delimiter) if item.strip()]
    return []

@register.filter
def strip(value):
    """Strip whitespace from a string"""
    if value:
        return value.strip()
    return value

@register.filter
def replace(value, args):
    """Replace occurrences of old with new in value"""
    if not value or not args:
        return value
    
    try:
        old, new = args.split(',', 1)
        return value.replace(old, new)
    except ValueError:
        return value

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0