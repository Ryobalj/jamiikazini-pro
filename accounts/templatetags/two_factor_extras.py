from django import template

register = template.Library()

@register.filter
def two_factor_enabled(user):
    return user.is_authenticated and user.staticdevice_set.exists()