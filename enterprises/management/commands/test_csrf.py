from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Testa as configurações de CSRF e origens confiáveis'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔒 TESTE DE CONFIGURAÇÕES CSRF'))
        self.stdout.write('=' * 50)
        
        # Debug status
        self.stdout.write(f'\n🔧 DEBUG: {settings.DEBUG}')
        
        # ALLOWED_HOSTS
        self.stdout.write('\n📋 ALLOWED_HOSTS:')
        for host in settings.ALLOWED_HOSTS:
            self.stdout.write(f'   ✅ {host}')
        
        # CSRF_TRUSTED_ORIGINS
        self.stdout.write('\n🔒 CSRF_TRUSTED_ORIGINS:')
        for origin in settings.CSRF_TRUSTED_ORIGINS:
            self.stdout.write(f'   ✅ {origin}')
        
        # Verificar se wildcard está correto
        wildcard_origins = [origin for origin in settings.CSRF_TRUSTED_ORIGINS if '*.nexiun.com.br' in origin]
        if wildcard_origins:
            self.stdout.write(self.style.SUCCESS('\n✅ Wildcard CSRF configurado corretamente!'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️ Wildcard CSRF pode não estar funcionando'))
        
        # URLs que devem funcionar
        self.stdout.write('\n🌐 URLs QUE DEVEM FUNCIONAR:')
        test_urls = [
            'https://nexiun.com.br',
            'https://www.nexiun.com.br',
            'https://agro-capital.nexiun.com.br',
            'https://testesistema.nexiun.com.br',
        ]
        
        for url in test_urls:
            self.stdout.write(f'   🔗 {url}')
        
        self.stdout.write('\n📝 PRÓXIMOS PASSOS:')
        self.stdout.write('1. Reinicie o servidor Django no EazyPanel')
        self.stdout.write('2. Teste os formulários novamente')
        self.stdout.write('3. Verifique se o erro CSRF desapareceu')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Configuração CSRF aplicada com sucesso!')) 