from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User, Role

class Command(BaseCommand):
    help = 'Migra usuários existentes para o novo sistema de roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auto-assign',
            action='store_true',
            help='Atribui automaticamente role básico aos usuários sem roles',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando migração de usuários para roles...'))
        
        # Buscar usuários sem roles
        users_without_roles = User.objects.filter(roles__isnull=True, is_superuser=False).distinct()
        
        self.stdout.write(f'Encontrados {users_without_roles.count()} usuários sem roles')
        
        if users_without_roles.count() == 0:
            self.stdout.write(self.style.SUCCESS('Todos os usuários já possuem roles!'))
            return
        
        # Buscar role padrão (coordenador é um bom padrão)
        try:
            default_role = Role.objects.get(code='coordenador', is_active=True)
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('Role padrão "coordenador" não encontrado!'))
            self.stdout.write('Execute: python manage.py setup_permissions')
            return
        
        if options['auto_assign']:
            with transaction.atomic():
                count = 0
                for user in users_without_roles:
                    user.roles.add(default_role)
                    count += 1
                    self.stdout.write(f'✓ Atribuído role "{default_role.name}" para {user.email}')
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 {count} usuários migrados com sucesso!')
                )
        else:
            self.stdout.write('\nUsuários sem roles:')
            for user in users_without_roles:
                self.stdout.write(f'  - {user.email} ({user.name})')
            
            self.stdout.write(
                f'\nPara atribuir automaticamente o role "{default_role.name}" a todos:'
            )
            self.stdout.write(
                self.style.WARNING('python manage.py migrate_users_to_roles --auto-assign')
            )
            
            self.stdout.write('\nOu configure manualmente no Admin: /admin/users/user/') 