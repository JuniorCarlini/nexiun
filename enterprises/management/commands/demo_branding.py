from django.core.management.base import BaseCommand
from enterprises.models import Enterprise


class Command(BaseCommand):
    help = 'Demonstra a personalização de marca (logo e cores) por empresa'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🎨 SISTEMA DE PERSONALIZAÇÃO DE MARCA POR EMPRESA'))
        self.stdout.write('=' * 70)
        
        # Listar empresas e suas personalizações
        enterprises = Enterprise.objects.all()
        
        if not enterprises:
            self.stdout.write(self.style.WARNING('❌ Nenhuma empresa encontrada.'))
            return
        
        for enterprise in enterprises:
            self.stdout.write(f'\n🏢 {enterprise.name}')
            self.stdout.write(f'   Subdomínio: {enterprise.subdomain}')
            
            # Logo
            if enterprise.logo:
                self.stdout.write(f'   🖼️  Logo: {enterprise.logo.url}')
            else:
                self.stdout.write(f'   🖼️  Logo: Padrão (Nexiun)')
            
            # Favicon
            if enterprise.favicon:
                self.stdout.write(f'   🔗 Favicon: {enterprise.favicon.url}')
            else:
                self.stdout.write(f'   🔗 Favicon: Padrão (Nexiun)')
            
            # Cores
            self.stdout.write(f'   🎨 Cores:')
            self.stdout.write(f'      • Primária: {enterprise.primary_color}')
            self.stdout.write(f'      • Secundária: {enterprise.secondary_color}')
            self.stdout.write(f'      • Texto/Ícones: {enterprise.text_icons_color}')
        
        self.stdout.write('\n🎨 FUNCIONALIDADES DE PERSONALIZAÇÃO:')
        self.stdout.write('-' * 50)
        
        features = [
            {
                'title': '1. Logo Personalizado',
                'description': 'Cada empresa pode ter seu próprio logo',
                'screens': 'Login, Recuperação de Senha, Dashboard'
            },
            {
                'title': '2. Favicon Personalizado',
                'description': 'Ícone personalizado na aba do navegador',
                'screens': 'Todas as páginas da empresa'
            },
            {
                'title': '3. Cores Personalizadas',
                'description': 'Esquema de cores único por empresa',
                'screens': 'Login, Botões, Links, Elementos de UI'
            },
            {
                'title': '4. Branding Contextual',
                'description': 'Marca aparece baseada no subdomínio acessado',
                'screens': 'Automático em todas as telas'
            }
        ]
        
        for feature in features:
            self.stdout.write(f'\n📋 {feature["title"]}:')
            self.stdout.write(f'   Descrição: {feature["description"]}')
            self.stdout.write(f'   Aplicado em: {feature["screens"]}')
        
        self.stdout.write('\n🧪 COMO TESTAR:')
        self.stdout.write('-' * 20)
        
        self.stdout.write('\n1. Teste via Headers HTTP:')
        for enterprise in enterprises:
            self.stdout.write(f'   curl -H "Host: {enterprise.subdomain}.nexiun.com.br" http://127.0.0.1:8000/users/login/')
        
        self.stdout.write('\n2. URLs para navegador (após configurar /etc/hosts):')
        for enterprise in enterprises:
            self.stdout.write(f'   http://{enterprise.subdomain}.nexiun.local:8000/users/login/')
        
        self.stdout.write('\n3. Teste de Recuperação de Senha:')
        for enterprise in enterprises:
            self.stdout.write(f'   http://{enterprise.subdomain}.nexiun.local:8000/password-reset/')
        
        self.stdout.write('\n📊 COMPARAÇÃO VISUAL:')
        self.stdout.write('-' * 25)
        
        self.stdout.write('\n🌐 Portal Principal (Nexiun):')
        self.stdout.write('   Logo: Nexiun padrão')
        self.stdout.write('   Cores: Laranja/Azul padrão')
        self.stdout.write('   Título: "Login", "Recuperar Senha"')
        
        for enterprise in enterprises:
            self.stdout.write(f'\n🏢 {enterprise.name}:')
            self.stdout.write(f'   Logo: {"Personalizado" if enterprise.logo else "Padrão"}')
            self.stdout.write(f'   Cores: {enterprise.primary_color}/{enterprise.secondary_color}')
            self.stdout.write(f'   Título: "Login - {enterprise.name}", "Recuperar Senha - {enterprise.name}"')
        
        self.stdout.write('\n✨ BENEFÍCIOS DA PERSONALIZAÇÃO:')
        self.stdout.write('-' * 40)
        benefits = [
            '🎯 Experiência de marca consistente',
            '🏢 Identidade visual única por empresa',
            '💼 Aparência profissional personalizada',
            '🔒 Usuários reconhecem facilmente sua empresa',
            '📱 Favicon personalizado no navegador',
            '🎨 Cores da empresa em toda interface',
            '⚡ Automático baseado no subdomínio'
        ]
        
        for benefit in benefits:
            self.stdout.write(f'   {benefit}')
        
        self.stdout.write('\n🔧 CONFIGURAÇÃO:')
        self.stdout.write('-' * 15)
        
        self.stdout.write('\n1. Via Interface Admin:')
        self.stdout.write('   - Acesse formulário de criação/edição de empresa')
        self.stdout.write('   - Faça upload do logo personalizado')
        self.stdout.write('   - Configure as cores da empresa')
        self.stdout.write('   - Adicione favicon personalizado')
        
        self.stdout.write('\n2. Via Django Admin:')
        self.stdout.write('   - Acesse /admin/enterprises/enterprise/')
        self.stdout.write('   - Edite a empresa desejada')
        self.stdout.write('   - Configure logo, favicon e cores')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Sistema de personalização por empresa funcionando perfeitamente!')) 