from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User, Role
from enterprises.models import Enterprise

class Command(BaseCommand):
    help = 'Cria um novo usuário CEO com empresa'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email do CEO')
        parser.add_argument('name', type=str, help='Nome do CEO')
        parser.add_argument('enterprise_name', type=str, help='Nome da empresa')
        parser.add_argument('--password', type=str, default='123456', help='Senha (padrão: 123456)')
        parser.add_argument('--cnpj', type=str, default='12345678901', help='CNPJ da empresa')

    def handle(self, *args, **options):
        email = options['email']
        name = options['name']
        enterprise_name = options['enterprise_name']
        password = options['password']
        cnpj = options['cnpj']
        
        self.stdout.write(self.style.SUCCESS(f'Criando CEO {name} para empresa {enterprise_name}...'))
        
        try:
            with transaction.atomic():
                # Criar usuário
                user = User.objects.create(
                    email=email,
                    name=name,
                    is_active=True
                )
                user.set_password(password)
                user.save()
                
                # Criar empresa
                enterprise = Enterprise.objects.create(
                    name=enterprise_name,
                    cnpj_or_cpf=cnpj,
                    primary_color='#05677D',
                    secondary_color='#FFB845',
                    text_icons_color='#FFFFFF'
                )
                
                # Associar usuário à empresa
                user.enterprise = enterprise
                user.save()
                
                # Atribuir role CEO
                ceo_role = Role.objects.get(code='ceo', is_active=True)
                user.roles.add(ceo_role)
                
                self.stdout.write(self.style.SUCCESS('✅ CEO criado com sucesso!'))
                self.stdout.write(f'   Email: {email}')
                self.stdout.write(f'   Senha: {password}')
                self.stdout.write(f'   Empresa: {enterprise_name}')
                self.stdout.write(f'   Permissões: {len(user.get_all_permissions())}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao criar CEO: {str(e)}')) 