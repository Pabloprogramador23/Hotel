from django import template
from django.template.defaultfilters import floatformat
from decimal import Decimal

register = template.Library()

@register.filter
def currency(value, decimal_places=2):
    """
    Formata um valor como moeda brasileira (R$)
    Exemplo: {{ value|currency }} -> R$ 1.234,56
    """
    if not value:
        return 'R$ 0,00'
    
    if isinstance(value, str):
        try:
            value = float(value)
        except (ValueError, TypeError):
            return value
    
    # Formata o número com as casas decimais especificadas e substitui ponto por vírgula
    formatted = floatformat(value, decimal_places)
    formatted = formatted.replace('.', ',')
    
    # Adiciona separador de milhar
    parts = formatted.split(',')
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else '00'
    
    result = ''
    for i, char in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            result = '.' + result
        result = char + result
    
    # Adiciona prefixo R$
    return f'R$ {result},{decimal_part}'

@register.filter
def absolute_value(value):
    """
    Retorna o valor absoluto de um número
    Exemplo: {{ value|absolute_value }} -> valor sem sinal
    """
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value, total):
    """
    Calcula a porcentagem de um valor em relação ao total
    Exemplo: {{ value|percentage:total }} -> 42.5
    """
    if not total:
        return 0
    
    try:
        percentage = (float(value) / float(total)) * 100
        return floatformat(percentage, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0