from django.core.management.base import BaseCommand
from django.conf import settings
from enterprises.models import Enterprise
import os


class Command(BaseCommand):
    help = 'Verifica a configuração Docker e ambiente'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🐳 VERIFICAÇÃO DO AMBIENTE DOCKER'))
        self.stdout.write('=' * 60)
        
        # Verificar variáveis de ambiente
        self.stdout.write('\n📋 VARIÁVEIS DE AMBIENTE:')
        env_vars = [
            ('DEBUG', 'DEBUG'),
            ('SECRET_KEY', 'SECRET_KEY'),
            ('DATABASE_URL', 'DATABASE_URL'),
            ('ALLOWED_HOSTS', 'ALLOWED_HOSTS'),
            ('CSRF_TRUSTED_ORIGINS', 'CSRF_TRUSTED_ORIGINS'),
        ]
        
        for env_name, setting_name in env_vars:
            env_value = os.getenv(env_name, 'Não definida')
            setting_value = getattr(settings, setting_name, 'Não definida')
            
            if env_value != 'Não definida':
                self.stdout.write(f'   ✅ {env_name}: {env_value[:50]}...')
            else:
                self.stdout.write(f'   ⚠️  {env_name}: Usando padrão do settings.py')
        
        # Verificar banco de dados
        self.stdout.write('\n🗄️ BANCO DE DADOS:')
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write('   ✅ Conexão com banco de dados: OK')
                
            # Verificar tabelas
            from django.core.management import execute_from_command_line
            tables = connection.introspection.table_names()
            if 'enterprises_enterprise' in tables:
                self.stdout.write('   ✅ Tabela enterprises_enterprise: Existe')
            else:
                self.stdout.write('   ❌ Tabela enterprises_enterprise: Não existe')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Erro no banco de dados: {e}')
        
        # Verificar migrações
        self.stdout.write('\n🔄 MIGRAÇÕES:')
        try:
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connection
            
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                self.stdout.write(f'   ⚠️  Migrações pendentes: {len(plan)}')
                for migration in plan:
                    self.stdout.write(f'      • {migration[0]}.{migration[1]}')
            else:
                self.stdout.write('   ✅ Todas as migrações aplicadas')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao verificar migrações: {e}')
        
        # Verificar empresas
        self.stdout.write('\n🏢 EMPRESAS CADASTRADAS:')
        try:
            enterprises = Enterprise.objects.all()
            if enterprises:
                for enterprise in enterprises:
                    self.stdout.write(f'   ✅ {enterprise.name}: {enterprise.subdomain}.nexiun.com.br')
            else:
                self.stdout.write('   ⚠️  Nenhuma empresa cadastrada')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Erro ao verificar empresas: {e}')
        
        # Verificar arquivos estáticos
        self.stdout.write('\n📁 ARQUIVOS ESTÁTICOS:')
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root and os.path.exists(static_root):
            files_count = sum([len(files) for r, d, files in os.walk(static_root)])
            self.stdout.write(f'   ✅ STATIC_ROOT: {static_root} ({files_count} arquivos)')
        else:
            self.stdout.write('   ⚠️  STATIC_ROOT não configurado ou não existe')
        
        # Verificar saúde geral
        self.stdout.write('\n🎯 COMANDOS ÚTEIS:')
        commands = [
            'docker-compose up -d  # Iniciar serviços',
            'docker-compose logs web  # Ver logs da aplicação',
            'docker-compose exec web python manage.py migrate  # Executar migrações',
            'docker-compose exec web python manage.py collectstatic  # Coletar estáticos',
            'docker-compose exec web python manage.py createsuperuser  # Criar superusuário',
            'docker-compose down  # Parar serviços',
        ]
        
        for cmd in commands:
            self.stdout.write(f'   {cmd}')
        
        # Status final
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 Verificação concluída!'))
        
        # URLs de teste
        self.stdout.write('\n🌐 TESTAR EM:')
        test_urls = [
            'http://localhost:8000',
            'http://localhost:8000/admin/',
            'http://localhost:8000/users/login/',
        ]
        
        for url in test_urls:
            self.stdout.write(f'   🔗 {url}') 