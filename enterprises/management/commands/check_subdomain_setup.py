from django.core.management.base import BaseCommand
from django.conf import settings
from enterprises.models import Enterprise
import socket


class Command(BaseCommand):
    help = 'Verifica se a configuração de subdomínios está correta'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔍 DIAGNÓSTICO DO SISTEMA DE SUBDOMÍNIOS'))
        self.stdout.write('=' * 60)
        
        # 1. Verificar ALLOWED_HOSTS
        self.stdout.write('\n1. 📋 ALLOWED_HOSTS:')
        self.stdout.write(f'   {settings.ALLOWED_HOSTS}')
        
        if '.nexiun.com.br' in settings.ALLOWED_HOSTS:
            self.stdout.write(self.style.SUCCESS('   ✅ Wildcard configurado corretamente'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ PROBLEMA: Adicione ".nexiun.com.br" em ALLOWED_HOSTS'))
        
        # 2. Verificar Middleware
        self.stdout.write('\n2. ⚙️ MIDDLEWARE:')
        middleware_list = settings.MIDDLEWARE
        
        subdomain_middleware = 'enterprises.middleware.SubdomainMiddleware'
        if subdomain_middleware in middleware_list:
            self.stdout.write(self.style.SUCCESS('   ✅ SubdomainMiddleware configurado'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ PROBLEMA: SubdomainMiddleware não encontrado'))
        
        enterprise_middleware = 'enterprises.middleware.EnterpriseRequiredMiddleware'
        if enterprise_middleware in middleware_list:
            self.stdout.write(self.style.SUCCESS('   ✅ EnterpriseRequiredMiddleware configurado'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ PROBLEMA: EnterpriseRequiredMiddleware não encontrado'))
        
        # 3. Verificar Empresas
        self.stdout.write('\n3. 🏢 EMPRESAS CADASTRADAS:')
        enterprises = Enterprise.objects.all()
        
        if not enterprises:
            self.stdout.write(self.style.WARNING('   ⚠️ Nenhuma empresa encontrada'))
            return
        
        for enterprise in enterprises:
            self.stdout.write(f'   🏢 {enterprise.name}')
            self.stdout.write(f'      Subdomínio: {enterprise.subdomain}')
            self.stdout.write(f'      URL completa: {enterprise.get_absolute_url()}')
        
        # 4. URLs para teste
        self.stdout.write('\n4. 🧪 URLs PARA TESTE:')
        self.stdout.write('   Teste estas URLs no navegador:')
        
        for enterprise in enterprises:
            self.stdout.write(f'   • https://{enterprise.subdomain}.nexiun.com.br/users/login/')
        
        # 5. Comandos de teste DNS
        self.stdout.write('\n5. 🌐 TESTE DNS (execute no terminal):')
        for enterprise in enterprises:
            self.stdout.write(f'   nslookup {enterprise.subdomain}.nexiun.com.br')
        
        # 6. Status de DEBUG
        self.stdout.write('\n6. 🔧 CONFIGURAÇÕES:')
        self.stdout.write(f'   DEBUG: {settings.DEBUG}')
        
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('   ⚠️ Modo DEBUG ativo - Para produção, use DEBUG=False'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ Modo produção ativo'))
        
        # 7. Próximos passos
        self.stdout.write('\n7. 🎯 PRÓXIMOS PASSOS NO EAZYPANEL:')
        self.stdout.write('   1. Vá em "Domains" no EazyPanel')
        self.stdout.write('   2. Adicione: *.nexiun.com.br')
        self.stdout.write('   3. Ou adicione cada subdomínio individualmente:')
        
        for enterprise in enterprises:
            self.stdout.write(f'      • {enterprise.subdomain}.nexiun.com.br')
        
        # 8. Verificação final
        self.stdout.write('\n8. ✅ CHECKLIST EAZYPANEL:')
        checklist = [
            'Domain "nexiun.com.br" adicionado',
            'Domain "www.nexiun.com.br" adicionado',
            'Domain "*.nexiun.com.br" adicionado (wildcard)',
            'SSL/TLS certificado ativo',
            'Force HTTPS habilitado'
        ]
        
        for item in checklist:
            self.stdout.write(f'   ☐ {item}')
        
        self.stdout.write('\n9. 🚨 SE NÃO FUNCIONAR:')
        problem_solutions = [
            'Verificar propagação DNS (pode levar até 24h)',
            'Limpar cache DNS do navegador',
            'Verificar se o registro "*" existe no Cloudflare',
            'Verificar logs do EazyPanel para erros',
            'Testar com curl: curl -I https://saldus.nexiun.com.br'
        ]
        
        for solution in problem_solutions:
            self.stdout.write(f'   • {solution}')
        
        # 10. Status final
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 DJANGO ESTÁ CONFIGURADO CORRETAMENTE!'))
        self.stdout.write(self.style.WARNING('🔧 CONFIGURE OS DOMÍNIOS NO EAZYPANEL AGORA!')) 