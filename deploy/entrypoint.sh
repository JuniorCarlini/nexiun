#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log com cores
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner de inicialização
echo -e "${BLUE}"
echo "=========================================="
echo "🚀 NEXIUN - Sistema Multi-Tenant"
echo "🌐 Inicializando aplicação Django..."
echo "=========================================="
echo -e "${NC}"

# Aguardar banco de dados PostgreSQL
log_info "Aguardando banco de dados PostgreSQL..."
if [ "$DB_HOST" ] && [ "$DB_PORT" ] && [ "$DB_USER" ]; then
    log_info "Conectando em $DB_HOST:$DB_PORT como $DB_USER..."
    while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
        log_warning "Banco de dados não está pronto. Tentando novamente em 3 segundos..."
        sleep 3
    done
    log_success "Banco de dados PostgreSQL conectado!"
else
    log_warning "Variáveis DB_HOST, DB_PORT, DB_USER não definidas - pulando verificação de conexão"
fi

# Executar migrações
log_info "Executando migrações do banco de dados..."
python manage.py migrate --noinput
if [ $? -eq 0 ]; then
    log_success "Migrações executadas com sucesso!"
else
    log_error "Falha nas migrações!"
    exit 1
fi

# Coletar arquivos estáticos
log_info "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput
if [ $? -eq 0 ]; then
    log_success "Arquivos estáticos coletados!"
else
    log_warning "Falha ao coletar arquivos estáticos (continuando...)"
fi

# Criar superusuário se não existir
log_info "Verificando superusuário..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    if '$DJANGO_SUPERUSER_EMAIL' and '$DJANGO_SUPERUSER_PASSWORD':
        User.objects.create_superuser('admin', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
        print('Superusuário criado!')
    else:
        print('Variáveis DJANGO_SUPERUSER_EMAIL e DJANGO_SUPERUSER_PASSWORD não configuradas')
else:
    print('Superusuário já existe')
"

# Criar empresas de exemplo (apenas em desenvolvimento)
if [ "$DEBUG" = "True" ]; then
    log_info "Criando empresas de exemplo..."
    python manage.py shell -c "
from enterprises.models import Enterprise
from users.models import User

# Criar empresas se não existirem
enterprises_data = [
    {'name': 'Agro Capital', 'subdomain': 'agro-capital'},
    {'name': 'Teste Sistema', 'subdomain': 'testesistema'},
]

for enterprise_data in enterprises_data:
    enterprise, created = Enterprise.objects.get_or_create(
        subdomain=enterprise_data['subdomain'],
        defaults={'name': enterprise_data['name']}
    )
    if created:
        print(f'Empresa {enterprise.name} criada!')
    else:
        print(f'Empresa {enterprise.name} já existe')
"
    log_success "Empresas de exemplo verificadas!"
fi

# Verificar saúde do sistema
log_info "Verificando configurações do sistema..."
python manage.py check --deploy 2>/dev/null || python manage.py check

log_success "Sistema pronto!"
echo -e "${GREEN}"
echo "=========================================="
echo "✅ Aplicação Django iniciada com sucesso!"
echo "🌐 Domínios configurados:"
echo "   • https://nexiun.com.br"
echo "   • https://*.nexiun.com.br"
echo "=========================================="
echo -e "${NC}"

# Executar comando passado como argumento
exec "$@" 