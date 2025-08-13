from django.core.management.base import BaseCommand
from enterprises.models import Enterprise
from users.models import User


class Command(BaseCommand):
    help = 'Demonstra como funciona o redirecionamento de subdomínios'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔄 SISTEMA DE REDIRECIONAMENTO AUTOMÁTICO'))
        self.stdout.write('=' * 70)
        
        # Listar empresas e seus usuários
        enterprises = Enterprise.objects.all()
        
        if not enterprises:
            self.stdout.write(self.style.WARNING('❌ Nenhuma empresa encontrada.'))
            return
        
        for enterprise in enterprises:
            users = User.objects.filter(enterprise=enterprise)
            
            self.stdout.write(f'\n🏢 {enterprise.name}')
            self.stdout.write(f'   Subdomínio: {enterprise.subdomain}')
            self.stdout.write(f'   URL Local: http://{enterprise.subdomain}.nexiun.local:8000')
            self.stdout.write(f'   URL Produção: https://{enterprise.subdomain}.nexiun.com.br')
            
            if users:
                self.stdout.write(f'   👥 Usuários ({users.count()}):')
                for user in users:
                    self.stdout.write(f'      • {user.name} ({user.email})')
            else:
                self.stdout.write(f'   👥 Usuários: Nenhum usuário vinculado')
        
        self.stdout.write('\n🔄 COMO FUNCIONA O REDIRECIONAMENTO:')
        self.stdout.write('-' * 50)
        
        # Cenários de redirecionamento
        scenarios = [
            {
                'title': '1. Login no Portal Principal',
                'scenario': 'Usuário acessa nexiun.com.br e faz login',
                'action': 'Sistema redireciona para empresa.nexiun.com.br'
            },
            {
                'title': '2. Login na Empresa Errada',
                'scenario': 'Usuário da Empresa A acessa empresa-b.nexiun.com.br',
                'action': 'Sistema redireciona para empresa-a.nexiun.com.br'
            },
            {
                'title': '3. Login na Empresa Correta',
                'scenario': 'Usuário da Empresa A acessa empresa-a.nexiun.com.br',
                'action': 'Sistema permite acesso normal'
            },
            {
                'title': '4. Usuário sem Empresa',
                'scenario': 'Usuário sem empresa faz login',
                'action': 'Sistema redireciona para criar empresa'
            }
        ]
        
        for scenario in scenarios:
            self.stdout.write(f'\n📋 {scenario["title"]}:')
            self.stdout.write(f'   Cenário: {scenario["scenario"]}')
            self.stdout.write(f'   Ação: {scenario["action"]}')
        
        self.stdout.write('\n🧪 PARA TESTAR LOCALMENTE:')
        self.stdout.write('-' * 30)
        
        self.stdout.write('\n1. Configurar /etc/hosts:')
        self.stdout.write('   sudo nano /etc/hosts')
        self.stdout.write('\n   Adicionar:')
        self.stdout.write('   127.0.0.1    nexiun.local')
        for enterprise in enterprises:
            self.stdout.write(f'   127.0.0.1    {enterprise.subdomain}.nexiun.local')
        
        self.stdout.write('\n2. URLs para teste:')
        self.stdout.write('   Portal: http://nexiun.local:8000')
        for enterprise in enterprises:
            self.stdout.write(f'   {enterprise.name}: http://{enterprise.subdomain}.nexiun.local:8000')
        
        self.stdout.write('\n3. Teste via curl (simular headers):')
        for enterprise in enterprises:
            self.stdout.write(f'   curl -H "Host: {enterprise.subdomain}.nexiun.com.br" http://127.0.0.1:8000')
        
        self.stdout.write('\n✅ BENEFÍCIOS DO REDIRECIONAMENTO:')
        self.stdout.write('-' * 40)
        benefits = [
            '🎯 Usuários sempre acessam sua empresa correta',
            '🔒 Isolamento automático de dados',
            '🌐 URLs amigáveis e profissionais',
            '⚡ Experiência de usuário otimizada',
            '🛡️ Segurança adicional por empresa'
        ]
        
        for benefit in benefits:
            self.stdout.write(f'   {benefit}')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Sistema de redirecionamento implementado e funcional!')) 