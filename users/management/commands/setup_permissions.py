from django.core.management.base import BaseCommand
from django.db import transaction
from users.permissions import create_custom_permissions, create_system_modules, create_default_roles

class Command(BaseCommand):
    help = 'Configura permissões customizadas, módulos e roles do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Recria todos os dados (use com cuidado)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando configuração do sistema de permissões...'))
        
        try:
            with transaction.atomic():
                # Cria módulos do sistema
                self.stdout.write('Criando módulos do sistema...')
                modules = create_system_modules()
                if modules:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {len(modules)} módulos criados: {[m.name for m in modules]}')
                    )
                else:
                    self.stdout.write('• Módulos já existem')

                # Cria permissões customizadas
                self.stdout.write('Criando permissões customizadas...')
                permissions = create_custom_permissions()
                if permissions:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {len(permissions)} permissões criadas')
                    )
                else:
                    self.stdout.write('• Permissões já existem')

                # Cria roles padrão
                self.stdout.write('Criando cargos padrão...')
                roles = create_default_roles()
                if roles:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {len(roles)} cargos criados: {[r.name for r in roles]}')
                    )
                else:
                    self.stdout.write('• Cargos já existem (permissões atualizadas)')

                self.stdout.write(
                    self.style.SUCCESS('\n🎉 Sistema de permissões configurado com sucesso!')
                )
                self.stdout.write(
                    self.style.WARNING('📝 Agora você pode executar as migrações: python manage.py migrate')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao configurar sistema de permissões: {str(e)}')
            )
            raise 