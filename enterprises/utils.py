from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import threading
from django.core.mail import EmailMessage
from django.template import loader
from django.conf import settings

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

def send_welcome_email_async(user, enterprise, request):
    """
    Envia email de boas-vindas de forma assíncrona quando uma empresa é criada
    """
    def send_email():
        try:
            # Contexto para o email
            context = {
                'user': user,
                'enterprise': enterprise,
                'protocol': 'https' if request.is_secure() else 'http',
                'domain': enterprise.get_full_domain() if enterprise else request.get_host(),
            }
            
            # Carrega o template HTML
            html_template = loader.get_template('emails/welcome_enterprise.html')
            html_body = html_template.render(context)
            
            # Assunto do email
            subject = f"🎉 Bem-vindo ao Nexiun - {enterprise.name}"
            
            # Cria o email
            email_message = EmailMessage(
                subject=subject,
                body=html_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            # Define como HTML
            email_message.content_subtype = "html"
            
            # Envia o email
            result = email_message.send()
            print(f"✅ Email de boas-vindas enviado para {user.email}! Resultado: {result}")
            
        except Exception as e:
            print(f"❌ Erro ao enviar email de boas-vindas para {user.email}: {e}")
    
    # Inicia thread para envio assíncrono
    email_thread = threading.Thread(target=send_email)
    email_thread.daemon = True  # Thread será fechada quando o processo principal terminar
    email_thread.start()

def send_new_team_member_email_async(new_user, enterprise, created_by, request):
    """
    Envia email de boas-vindas de forma assíncrona quando um novo usuário é adicionado à equipe
    """
    def send_email():
        try:
            # Contexto para o email
            context = {
                'new_user': new_user,
                'enterprise': enterprise,
                'created_by': created_by,
                'protocol': 'https' if request.is_secure() else 'http',
                'domain': enterprise.get_full_domain() if enterprise else request.get_host(),
            }
            
            # Carrega o template HTML
            html_template = loader.get_template('emails/new_team_member.html')
            html_body = html_template.render(context)
            
            # Assunto do email
            subject = f"👋 Bem-vindo à equipe {enterprise.name}!"
            
            # Cria o email
            email_message = EmailMessage(
                subject=subject,
                body=html_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[new_user.email]
            )
            
            # Define como HTML
            email_message.content_subtype = "html"
            
            # Envia o email
            result = email_message.send()
            print(f"✅ Email de novo membro enviado para {new_user.email}! Resultado: {result}")
            
        except Exception as e:
            print(f"❌ Erro ao enviar email de novo membro para {new_user.email}: {e}")
    
    # Inicia thread para envio assíncrono
    email_thread = threading.Thread(target=send_email)
    email_thread.daemon = True  # Thread será fechada quando o processo principal terminar
    email_thread.start()
