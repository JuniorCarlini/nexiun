from django import template
from decimal import Decimal
import re

register = template.Library()

@register.filter
def div(value, arg):
    """Divide o valor pelo argumento"""
    try:
        if value is None or arg is None or arg == 0:
            return 0
        return Decimal(value) / Decimal(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def whatsapp_phone(value):
    """Formata o telefone para uso no WhatsApp (remove caracteres especiais e adiciona código do país)"""
    if not value:
        return ''
    
    # Remove todos os caracteres que não são dígitos
    phone_digits = re.sub(r'\D', '', str(value))
    
    # Se o número não tem código do país, adiciona o código do Brasil (55)
    if len(phone_digits) == 10:  # Telefone fixo (11) 9999-9999 -> 11999999999
        phone_digits = '55' + phone_digits
    elif len(phone_digits) == 11:  # Celular (11) 99999-9999 -> 5511999999999
        phone_digits = '55' + phone_digits
    elif len(phone_digits) == 13 and phone_digits.startswith('55'):  # Já tem código do país
        pass  # Mantém como está
    else:
        # Se não conseguir determinar o formato, tenta adicionar 55 na frente
        if not phone_digits.startswith('55'):
            phone_digits = '55' + phone_digits
    
    return phone_digits 