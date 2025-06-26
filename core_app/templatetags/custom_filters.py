# C:\entc\core_app\templatetags\custom_filters.py

from django import template

register = template.Library()

@register.filter
def sum_field(queryset, field_name):
    """
    Sums a specific field's value across all objects in a queryset.
    Usage: {{ my_queryset|sum_field:'my_field' }}
    """
    # Ensure all objects in the queryset have the specified field
    # and that the field's value is numeric.
    total = 0
    for obj in queryset:
        value = getattr(obj, field_name, None)
        if isinstance(value, (int, float)):
            total += value
        else:
            # Optionally log a warning if a non-numeric field is encountered
            # print(f"Warning: Field '{field_name}' on object {obj} is not numeric. Value: {value}")
            pass # Silently skip non-numeric values for robustness
    return total
