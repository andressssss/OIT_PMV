from django import template

register = template.Library()

@register.filter
def add_class(value, class_name):
    """Filtro para agregar clases a los campos de formulario."""
    return value.as_widget(attrs={'class': class_name})