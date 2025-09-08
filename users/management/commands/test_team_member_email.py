from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.template import loader
from django.core.mail import EmailMessage
from django.conf import settings
from enterprises.models import Enterprise

User = get_user_model()

class Command(BaseCommand):
    help = 'Testa o envio de email para novo membro da equipe'

    def add_arguments(self, parser):
        parser.add_argument('new_user_email', type=str, help='Email do novo usuário')
        parser.add_argument('--created-by', type=str, help='Email de quem criou o usuário', default=None)
        parser.add_argument('--domain', type=str, default='localhost:8000', help='Domínio para teste')

    def handle(self, *args, **options):
        new_user_email = options['new_user_email']
        created_by_email = options['created_by']
        domain = options['domain']
        
        try:
            # Busca o novo usuário
            new_user = User.objects.get(email=new_user_email)
            self.stdout.write(f"Novo usuário encontrado: {new_user.name} ({new_user.email})")
            
            # Busca quem criou (se especificado)
            created_by = None
            if created_by_email:
                try:
                    created_by = User.objects.get(email=created_by_email)
                    self.stdout.write(f"Criado por: {created_by.name} ({created_by.email})")
                except User.DoesNotExist:
                    self.stdout.write(f"Usuário criador '{created_by_email}' não encontrado")
            
            # Obtém a empresa do usuário
            enterprise = new_user.enterprise
            if enterprise:
                self.stdout.write(f"Empresa: {enterprise.name}")
                self.stdout.write(f"Cores: {enterprise.primary_color}, {enterprise.secondary_color}")
                self.stdout.write(f"Logo: {enterprise.get_logo_dark_url()}")
                self.stdout.write(f"Domínio: {enterprise.get_full_domain()}")
            else:
                self.stdout.write("Usuário não possui empresa vinculada")
                return
            
            # Mostra roles do usuário
            if new_user.roles.exists():
                roles = [role.name for role in new_user.roles.all()]
                self.stdout.write(f"Cargos: {', '.join(roles)}")
            
            # Contexto para o email
            context = {
                'new_user': new_user,
                'enterprise': enterprise,
                'created_by': created_by,
                'protocol': 'http',
                'domain': enterprise.get_full_domain() if enterprise else domain,
            }
            
            # Carrega o template HTML
            html_template = loader.get_template('emails/new_team_member.html')
            html_body = html_template.render(context)
            
            # Assunto do email
            subject = f"👋 Bem-vindo à equipe {enterprise.name}!"
            
            self.stdout.write(f"\n=== ASSUNTO ===")
            self.stdout.write(subject)
            
            self.stdout.write(f"\n=== CORPO DO EMAIL (HTML) ===")
            self.stdout.write("Template HTML de novo membro carregado com sucesso!")
            self.stdout.write(f"Tamanho: {len(html_body)} caracteres")
            
            # Salva o HTML em um arquivo para visualização
            with open('/tmp/test_team_member_email.html', 'w', encoding='utf-8') as f:
                f.write(html_body)
            self.stdout.write("HTML salvo em: /tmp/test_team_member_email.html")
            
            # Define o remetente
            from_email = settings.DEFAULT_FROM_EMAIL
            self.stdout.write(f"\nRemetente: {from_email}")
            
            # Se não estiver em modo DEBUG, oferece opção de enviar
            if not settings.DEBUG:
                confirm = input("\nDeseja realmente enviar o email? (s/N): ")
                if confirm.lower() == 's':
                    try:
                        email_message = EmailMessage(
                            subject=subject,
                            body=html_body,
                            from_email=from_email,
                            to=[new_user.email]
                        )
                        
                        # Define como HTML
                        email_message.content_subtype = "html"
                        
                        email_message.send()
                        self.stdout.write(self.style.SUCCESS("Email de novo membro enviado com sucesso!"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Erro ao enviar email: {e}"))
                else:
                    self.stdout.write("Email não enviado.")
            else:
                self.stdout.write(f"\nModo DEBUG ativo - email será exibido no console")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Usuário com email '{new_user_email}' não encontrado"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro: {e}")) 