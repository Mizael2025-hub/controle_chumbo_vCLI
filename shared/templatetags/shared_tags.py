from django import template

register = template.Library()


@register.filter
def get_attr(obj, name):
    """Acessa atributo dinâmico; usa get_FOO_display quando existir (choices)."""
    display = getattr(obj, f"get_{name}_display", None)
    if callable(display):
        return display()
    return getattr(obj, name, "")
