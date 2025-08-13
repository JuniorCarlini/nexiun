from django.core.management.base import BaseCommand
from django.conf import settings
from enterprises.models import Enterprise


class Command(BaseCommand):
    help = 'Configura e exibe informações sobre subdomínios das empresas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista todas as empresas e seus subdomínios',
        )
        parser.add_argument(
            '--dns-config',
            action='store_true',
            help='Mostra configuração DNS necessária',
        )
        parser.add_argument(
            '--test-urls',
            action='store_true',
            help='Gera URLs de teste para todas as empresas',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_enterprises()
        
        if options['dns_config']:
            self.show_dns_config()
        
        if options['test_urls']:
            self.show_test_urls()
        
        if not any([options['list'], options['dns_config'], options['test_urls']]):
            self.show_all()

    def list_enterprises(self):
        """Lista todas as empresas e seus subdomínios"""
        self.stdout.write(self.style.SUCCESS('\n📋 EMPRESAS E SUBDOMÍNIOS:'))
        self.stdout.write('=' * 60)
        
        enterprises = Enterprise.objects.all()
        
        if not enterprises:
            self.stdout.write(self.style.WARNING('❌ Nenhuma empresa encontrada.'))
            return
        
        for enterprise in enterprises:
            self.stdout.write(f'\n🏢 {enterprise.name}')
            self.stdout.write(f'   Subdomínio: {enterprise.subdomain}')
            self.stdout.write(f'   Domínio completo: {enterprise.get_full_domain()}')
            self.stdout.write(f'   URL: {enterprise.get_absolute_url()}')

    def show_dns_config(self):
        """Mostra configuração DNS necessária"""
        self.stdout.write(self.style.SUCCESS('\n🌐 CONFIGURAÇÃO DNS NECESSÁRIA:'))
        self.stdout.write('=' * 60)
        
        self.stdout.write('\n1. REGISTRO A PRINCIPAL:')
        self.stdout.write('   nexiun.com.br        A    [SEU_IP_SERVIDOR]')
        self.stdout.write('   www.nexiun.com.br    A    [SEU_IP_SERVIDOR]')
        
        self.stdout.write('\n2. REGISTRO WILDCARD PARA SUBDOMÍNIOS:')
        self.stdout.write('   *.nexiun.com.br      A    [SEU_IP_SERVIDOR]')
        
        self.stdout.write('\n3. CONFIGURAÇÃO NGINX (exemplo):')
        nginx_config = '''
server {
    listen 80;
    server_name nexiun.com.br www.nexiun.com.br *.nexiun.com.br;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}'''
        self.stdout.write(nginx_config)
        
        self.stdout.write('\n4. TESTE LOCAL (adicione ao /etc/hosts):')
        enterprises = Enterprise.objects.all()
        for enterprise in enterprises:
            self.stdout.write(f'   127.0.0.1    {enterprise.get_full_domain()}')

    def show_test_urls(self):
        """Gera URLs de teste para todas as empresas"""
        self.stdout.write(self.style.SUCCESS('\n🧪 URLS DE TESTE:'))
        self.stdout.write('=' * 60)
        
        enterprises = Enterprise.objects.all()
        
        if not enterprises:
            self.stdout.write(self.style.WARNING('❌ Nenhuma empresa encontrada.'))
            return
        
        for enterprise in enterprises:
            self.stdout.write(f'\n🏢 {enterprise.name}:')
            self.stdout.write(f'   🌐 {enterprise.get_absolute_url()}')
            self.stdout.write(f'   📊 {enterprise.get_absolute_url()}/dashboard')
            self.stdout.write(f'   👥 {enterprise.get_absolute_url()}/users')
            self.stdout.write(f'   🏭 {enterprise.get_absolute_url()}/units')

    def show_all(self):
        """Mostra todas as informações"""
        self.list_enterprises()
        self.show_dns_config()
        self.show_test_urls()
        
        self.stdout.write(self.style.SUCCESS('\n✅ SISTEMA DE SUBDOMÍNIOS CONFIGURADO!'))
        self.stdout.write('\n📝 PRÓXIMOS PASSOS:')
        self.stdout.write('1. Configure DNS conforme mostrado acima')
        self.stdout.write('2. Configure seu servidor web (Nginx/Apache)')
        self.stdout.write('3. Teste os subdomínios criados')
        self.stdout.write('4. Para desenvolvimento local, adicione entradas ao /etc/hosts') 