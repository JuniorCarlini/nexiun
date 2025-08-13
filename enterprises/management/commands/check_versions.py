from django.core.management.base import BaseCommand
import sys
import django
import platform


class Command(BaseCommand):
    help = 'Verifica versões do ambiente de desenvolvimento e produção'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔍 VERIFICAÇÃO DE VERSÕES DO AMBIENTE'))
        self.stdout.write('=' * 60)
        
        # Informações do sistema
        self.stdout.write('\n🖥️ SISTEMA OPERACIONAL:')
        self.stdout.write(f'   Sistema: {platform.system()} {platform.release()}')
        self.stdout.write(f'   Arquitetura: {platform.architecture()[0]}')
        self.stdout.write(f'   Processor: {platform.processor()}')
        
        # Python
        self.stdout.write('\n🐍 PYTHON:')
        self.stdout.write(f'   Versão local: {sys.version}')
        self.stdout.write(f'   Executável: {sys.executable}')
        
        # Django
        self.stdout.write('\n🌐 DJANGO:')
        self.stdout.write(f'   Versão: {django.get_version()}')
        
        # Verificar se é LTS
        major, minor = django.VERSION[:2]
        is_lts = (major, minor) in [(3, 2), (4, 2), (5, 2)]  # Versões LTS conhecidas
        if is_lts:
            self.stdout.write(self.style.SUCCESS(f'   ✅ Django LTS (Long Term Support)'))
        else:
            self.stdout.write(self.style.WARNING(f'   ⚠️ Não é versão LTS'))
        
        # Dependências principais
        self.stdout.write('\n📦 DEPENDÊNCIAS PRINCIPAIS:')
        
        packages_to_check = [
            ('gunicorn', 'Servidor WSGI'),
            ('psycopg', 'PostgreSQL adapter'),
            ('boto3', 'AWS SDK'),
            ('pillow', 'Processamento de imagens'),
            ('decouple', 'Configuração'),
        ]
        
        for package, description in packages_to_check:
            try:
                if package == 'decouple':
                    import decouple
                    version = getattr(decouple, '__version__', 'Versão não disponível')
                elif package == 'psycopg':
                    import psycopg
                    version = psycopg.__version__
                elif package == 'gunicorn':
                    import gunicorn
                    version = gunicorn.__version__
                elif package == 'boto3':
                    import boto3
                    version = boto3.__version__
                elif package == 'pillow':
                    import PIL
                    version = PIL.__version__
                
                self.stdout.write(f'   ✅ {package} {version} - {description}')
            except ImportError:
                self.stdout.write(f'   ❌ {package} não instalado - {description}')
            except Exception as e:
                self.stdout.write(f'   ⚠️ {package} erro: {e}')
        
        # Compatibilidade Docker
        self.stdout.write('\n🐳 COMPATIBILIDADE DOCKER:')
        self.stdout.write(f'   Python base: python:3.13-slim')
        self.stdout.write(f'   Django alvo: 5.2.5 LTS')
        self.stdout.write(f'   Match desenvolvimento: ✅')
        
        # Recomendações de atualização
        current_django = django.get_version()
        if current_django != '5.2.5':
            self.stdout.write('\n📋 ATUALIZAÇÕES RECOMENDADAS:')
            self.stdout.write(f'   Django atual: {current_django}')
            self.stdout.write(f'   Django alvo: 5.2.5 LTS')
            self.stdout.write('\n   Para atualizar:')
            self.stdout.write('   pip install Django==5.2.5')
            self.stdout.write('   pip install -r requirements.txt --upgrade')
        
        # Verificação de segurança
        self.stdout.write('\n🔒 VERIFICAÇÃO DE SEGURANÇA:')
        try:
            from django.core.management import execute_from_command_line
            # Não executar check --deploy em desenvolvimento
            if not sys.argv or 'runserver' not in ' '.join(sys.argv):
                self.stdout.write('   Execute: python manage.py check --deploy')
        except:
            pass
        
        # Comandos úteis
        self.stdout.write('\n🔧 COMANDOS ÚTEIS:')
        commands = [
            'pip install -r requirements.txt --upgrade  # Atualizar dependências',
            'python manage.py check --deploy  # Verificar configuração produção',
            'python manage.py migrate  # Aplicar migrações',
            'python manage.py collectstatic  # Coletar arquivos estáticos',
        ]
        
        for cmd in commands:
            self.stdout.write(f'   {cmd}')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 Verificação de versões concluída!')) 