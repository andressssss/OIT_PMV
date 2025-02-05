from django import template

register = template.Library()

@register.filter
def traducir_tipo_contrato(value):
    opciones = {
        "terminoi": "Término Indefinido",
        "terminof": "Término Fijo",
        "otro": "Otro",
    }
    return opciones.get(value, "Desconocido")

@register.filter
def traducir_horario(value):
    opciones = {
        "tiempoc": "Tiempo completo",
        "terminof": "Término Fijo",
        "otro": "Otro",
    }
    return opciones.get(value, "Desconocido")
