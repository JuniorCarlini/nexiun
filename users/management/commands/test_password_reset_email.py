from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()

class Command(BaseCommand):
    help = 'Testa o envio de email de recuperação de senha com as novas funcionalidades'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email do usuário para teste')
        parser.add_argument('--domain', type=str, default='localhost:8000', help='Domínio para teste')

    def handle(self, *args, **options):
        email = options['email']
        domain = options['domain']
        
        try:
            # Busca o usuário
            user = User.objects.get(email=email)
            self.stdout.write(f"Usuário encontrado: {user.name} ({user.email})")
            
            # Obtém a empresa do usuário
            enterprise = user.enterprise
            if enterprise:
                self.stdout.write(f"Empresa: {enterprise.name}")
                self.stdout.write(f"Cores: {enterprise.primary_color}, {enterprise.secondary_color}")
                self.stdout.write(f"Logo: {enterprise.get_logo_light_url()}")
            else:
                self.stdout.write("Usuário não possui empresa vinculada")
            
            # Contexto para o email
            context = {
                'email': user.email,
                'domain': domain,
                'site_name': enterprise.name if enterprise else 'Nexiun',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': default_token_generator.make_token(user),
                'protocol': 'http',
                'enterprise': enterprise,
            }
            
            # Carrega os templates
            subject_template = loader.get_template('password_reset/password_reset_subject.txt')
            html_template = loader.get_template('password_reset/password_reset_email_html.html')
            
            # Renderiza o assunto e conteúdo
            subject = subject_template.render(context)
            subject = ''.join(subject.splitlines())
            html_body = html_template.render(context)
            
            self.stdout.write(f"\n=== ASSUNTO ===")
            self.stdout.write(subject)
            
            self.stdout.write(f"\n=== CORPO DO EMAIL (HTML) ===")
            self.stdout.write("Template HTML carregado com sucesso!")
            self.stdout.write(f"Tamanho: {len(html_body)} caracteres")
            
            # Salva o HTML em um arquivo para visualização
            with open('/tmp/test_email.html', 'w', encoding='utf-8') as f:
                f.write(html_body)
            self.stdout.write("HTML salvo em: /tmp/test_email.html")
            
            # Define o remetente
            from_email = settings.DEFAULT_FROM_EMAIL  # Usar sempre o email configurado no sistema
            # Comentado temporariamente devido a restrições SMTP:
            # from_email = f"no-reply@{enterprise.get_full_domain()}" if enterprise else settings.DEFAULT_FROM_EMAIL
            self.stdout.write(f"\nRemetente: {from_email}")
            
            # Se não estiver em modo DEBUG, oferece opção de enviar
            if not settings.DEBUG:
                confirm = input("\nDeseja realmente enviar o email? (s/N): ")
                if confirm.lower() == 's':
                    try:
                        from django.core.mail import EmailMessage
                        email_message = EmailMessage(
                            subject=subject,
                            body=html_body,
                            from_email=from_email,
                            to=[user.email]
                        )
                        
                        # Define como HTML
                        email_message.content_subtype = "html"
                        
                        email_message.send()
                        self.stdout.write(self.style.SUCCESS("Email HTML enviado com sucesso!"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Erro ao enviar email: {e}"))
                else:
                    self.stdout.write("Email não enviado.")
            else:
                self.stdout.write(f"\nModo DEBUG ativo - email será exibido no console")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Usuário com email '{email}' não encontrado"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro: {e}")) 