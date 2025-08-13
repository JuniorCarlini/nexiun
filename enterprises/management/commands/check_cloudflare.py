import socket
import subprocess
import ssl
from datetime import datetime
from django.core.management.base import BaseCommand
from enterprises.models import Enterprise


class Command(BaseCommand):
    help = 'Verifica configuração DNS e conectividade para Cloudflare'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Testar domínio específico',
        )
        parser.add_argument(
            '--check-ssl',
            action='store_true',
            help='Verificar certificados SSL',
        )
        parser.add_argument(
            '--check-dns',
            action='store_true',
            help='Verificar resolução DNS',
        )

    def handle(self, *args, **options):
        if options['domain']:
            self.check_specific_domain(options['domain'])
        else:
            self.check_all_domains()
        
        if options['check_ssl']:
            self.check_ssl_certificates()
        
        if options['check_dns']:
            self.check_dns_resolution()

    def check_specific_domain(self, domain):
        """Verifica um domínio específico"""
        self.stdout.write(self.style.SUCCESS(f'\n🔍 VERIFICANDO DOMÍNIO: {domain}'))
        self.stdout.write('=' * 60)
        
        self._check_dns_record(domain)
        self._check_http_response(domain)
        self._check_ssl_cert(domain)

    def check_all_domains(self):
        """Verifica todos os domínios/subdomínios das empresas"""
        self.stdout.write(self.style.SUCCESS('\n🌐 VERIFICAÇÃO GERAL DE DOMÍNIOS'))
        self.stdout.write('=' * 60)
        
        # Domínios principais
        main_domains = ['nexiun.com.br', 'www.nexiun.com.br']
        
        self.stdout.write('\n📋 DOMÍNIOS PRINCIPAIS:')
        for domain in main_domains:
            self._check_domain_basic(domain)
        
        # Subdomínios das empresas
        enterprises = Enterprise.objects.all()
        if enterprises:
            self.stdout.write('\n🏢 SUBDOMÍNIOS DAS EMPRESAS:')
            for enterprise in enterprises:
                domain = enterprise.get_full_domain()
                self._check_domain_basic(domain)
        else:
            self.stdout.write('\n⚠️ Nenhuma empresa encontrada.')

    def check_ssl_certificates(self):
        """Verifica certificados SSL"""
        self.stdout.write(self.style.SUCCESS('\n🔒 VERIFICAÇÃO SSL'))
        self.stdout.write('=' * 60)
        
        domains = ['nexiun.com.br']
        enterprises = Enterprise.objects.all()
        domains.extend([e.get_full_domain() for e in enterprises])
        
        for domain in domains:
            self._check_ssl_cert(domain)

    def check_dns_resolution(self):
        """Verifica resolução DNS"""
        self.stdout.write(self.style.SUCCESS('\n🌐 VERIFICAÇÃO DNS'))
        self.stdout.write('=' * 60)
        
        # Teste wildcard
        test_subdomains = ['teste123.nexiun.com.br', 'verificacao.nexiun.com.br']
        
        for domain in test_subdomains:
            self._check_dns_record(domain)

    def _check_domain_basic(self, domain):
        """Verificação básica de domínio"""
        try:
            # Resolução DNS
            ip = socket.gethostbyname(domain)
            status = '✅'
        except socket.gaierror:
            ip = 'NÃO RESOLVE'
            status = '❌'
        
        self.stdout.write(f'  {status} {domain:<30} → {ip}')

    def _check_dns_record(self, domain):
        """Verifica registro DNS usando dig"""
        self.stdout.write(f'\n🔍 DNS: {domain}')
        
        try:
            # Tenta usar dig se disponível
            result = subprocess.run(['dig', '+short', domain], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                ips = result.stdout.strip().split('\n')
                for ip in ips:
                    if ip:
                        self.stdout.write(f'  ✅ IP: {ip}')
            else:
                # Fallback para socket
                ip = socket.gethostbyname(domain)
                self.stdout.write(f'  ✅ IP: {ip}')
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # dig não disponível, usar socket
            try:
                ip = socket.gethostbyname(domain)
                self.stdout.write(f'  ✅ IP: {ip}')
            except socket.gaierror:
                self.stdout.write(f'  ❌ Não resolve')
        except socket.gaierror:
            self.stdout.write(f'  ❌ Não resolve')

    def _check_http_response(self, domain):
        """Verifica resposta HTTP"""
        self.stdout.write(f'\n🌐 HTTP: {domain}')
        
        try:
            import urllib.request
            
            # Teste HTTPS
            try:
                url = f'https://{domain}'
                response = urllib.request.urlopen(url, timeout=10)
                self.stdout.write(f'  ✅ HTTPS: {response.code}')
            except Exception as e:
                self.stdout.write(f'  ❌ HTTPS: {str(e)[:50]}')
            
            # Teste HTTP
            try:
                url = f'http://{domain}'
                response = urllib.request.urlopen(url, timeout=10)
                self.stdout.write(f'  ✅ HTTP: {response.code}')
            except Exception as e:
                self.stdout.write(f'  ❌ HTTP: {str(e)[:50]}')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Erro: {str(e)}')

    def _check_ssl_cert(self, domain):
        """Verifica certificado SSL"""
        self.stdout.write(f'\n🔒 SSL: {domain}')
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Informações do certificado
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    # Data de expiração
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.now()).days
                    
                    self.stdout.write(f'  ✅ Válido para: {subject.get("commonName", "N/A")}')
                    self.stdout.write(f'  ✅ Emissor: {issuer.get("organizationName", "N/A")}')
                    self.stdout.write(f'  ✅ Expira em: {days_until_expiry} dias')
                    
                    # Verificar SANs (Subject Alternative Names)
                    if 'subjectAltName' in cert:
                        sans = [name[1] for name in cert['subjectAltName'] if name[0] == 'DNS']
                        if any('*' in san for san in sans):
                            self.stdout.write(f'  ✅ Wildcard suportado')
                        else:
                            self.stdout.write(f'  ⚠️ Sem wildcard')
                    
                    # Alerta se próximo do vencimento
                    if days_until_expiry < 30:
                        self.stdout.write(f'  ⚠️ ATENÇÃO: Certificado expira em {days_until_expiry} dias!')
                        
        except socket.timeout:
            self.stdout.write(f'  ❌ Timeout na conexão SSL')
        except ssl.SSLError as e:
            self.stdout.write(f'  ❌ Erro SSL: {str(e)}')
        except Exception as e:
            self.stdout.write(f'  ❌ Erro: {str(e)}')

    def check_cloudflare_status(self):
        """Verifica se está usando Cloudflare"""
        self.stdout.write(self.style.SUCCESS('\n☁️ VERIFICAÇÃO CLOUDFLARE'))
        self.stdout.write('=' * 60)
        
        try:
            # Verificar headers Cloudflare
            import urllib.request
            
            url = 'https://nexiun.com.br'
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=10)
            
            headers = dict(response.headers)
            
            # Headers típicos do Cloudflare
            cf_headers = ['cf-ray', 'cf-cache-status', 'server']
            
            cloudflare_detected = False
            for header in cf_headers:
                if header.lower() in [h.lower() for h in headers.keys()]:
                    cloudflare_detected = True
                    self.stdout.write(f'  ✅ {header}: {headers.get(header, "N/A")}')
            
            if cloudflare_detected:
                self.stdout.write('  ✅ Cloudflare detectado!')
            else:
                self.stdout.write('  ❌ Cloudflare não detectado')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Erro ao verificar: {str(e)}')

    def show_configuration_summary(self):
        """Mostra resumo da configuração necessária"""
        self.stdout.write(self.style.SUCCESS('\n📝 RESUMO DA CONFIGURAÇÃO'))
        self.stdout.write('=' * 60)
        
        self.stdout.write('\n🌐 CLOUDFLARE DNS:')
        self.stdout.write('  @ (root)     A    [IP_DO_SERVIDOR]')
        self.stdout.write('  www          A    [IP_DO_SERVIDOR]')
        self.stdout.write('  *            A    [IP_DO_SERVIDOR]  ⭐ WILDCARD')
        
        self.stdout.write('\n🔒 SSL/TLS:')
        self.stdout.write('  Modo: Full (strict)')
        self.stdout.write('  Origin Certificate: nexiun.com.br, *.nexiun.com.br')
        
        self.stdout.write('\n⚙️ EAZYPANEL:')
        self.stdout.write('  Domain: nexiun.com.br')
        self.stdout.write('  Alias: www.nexiun.com.br')
        self.stdout.write('  ALLOWED_HOSTS: .nexiun.com.br')

# Adicionar verificação de Cloudflare ao comando principal
def enhanced_handle(self, *args, **options):
    """Handle method aprimorado"""
    # Código original...
    
    # Verificações adicionais
    self.check_cloudflare_status()
    self.show_configuration_summary()
    
    self.stdout.write(self.style.SUCCESS('\n✅ VERIFICAÇÃO COMPLETA!'))
    self.stdout.write('\n💡 Para resolver problemas:')
    self.stdout.write('1. Verifique nameservers no registrador')
    self.stdout.write('2. Aguarde propagação DNS (2-24h)')
    self.stdout.write('3. Configure SSL no Cloudflare')
    self.stdout.write('4. Teste conectividade regularmente') 