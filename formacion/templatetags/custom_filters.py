from django import template

register = template.Library()

@register.filter
def times(value, multiplier):
    return value * multiplier