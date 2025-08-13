from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta

def calculate_parcelas(projeto):
    """
    Calcula parcelas do financiamento com período anual
    """
    valor_inicial = Decimal(str(projeto.value))
    juros_anual = Decimal(str(projeto.fees)) / Decimal('100')
    anos_carencia = int(projeto.payment_grace)
    anos_pagamento = int(projeto.installments)
    data_base = projeto.approval_date
    
    fluxo_anual = []
    # Primeiro ano já começa com juros
    saldo_devedor = valor_inicial * (Decimal('1') + juros_anual)
    
    for ano in range(1, anos_carencia + anos_pagamento + 1):
        if ano <= anos_carencia:
            # Durante carência
            valor_parcela = Decimal('0')
            juros = saldo_devedor * juros_anual
            
            fluxo_anual.append({
                'ano': ano,
                'saldo_devedor': saldo_devedor,
                'valor_parcela': valor_parcela,
                'juros': juros,
                'data_vencimento': data_base + relativedelta(years=ano),
                'status': 'carencia'
            })
            
            # Atualiza saldo: adiciona juros
            saldo_devedor = saldo_devedor + juros
        else:
            # Durante pagamento
            juros = saldo_devedor * juros_anual
            # Calcula parcela com base no saldo atual
            parcelas_restantes = anos_carencia + anos_pagamento - ano + 1
            valor_parcela = saldo_devedor / Decimal(str(parcelas_restantes))
            
            fluxo_anual.append({
                'ano': ano,
                'saldo_devedor': saldo_devedor,
                'valor_parcela': valor_parcela,
                'juros': juros,
                'data_vencimento': data_base + relativedelta(years=ano),
                'status': 'pagamento'
            })
            
            # Atualiza saldo: primeiro subtrai parcela, depois adiciona juros
            saldo_devedor = (saldo_devedor - valor_parcela) * (Decimal('1') + juros_anual)
    
    total_juros = sum(periodo['juros'] for periodo in fluxo_anual)
    
    return {
        'valor_inicial': valor_inicial,
        'valor_juros': total_juros,
        'valor_total': valor_inicial + total_juros,
        'fluxo': fluxo_anual,
        'inicio_pagamento': projeto.approval_date + relativedelta(years=anos_carencia)
    }
