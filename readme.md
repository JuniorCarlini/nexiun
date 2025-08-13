# 🌱 Nexiun - Sistema Multi-Tenant para Crédito Rural

> **Nexiun** é uma plataforma SaaS completa e moderna para gestão de escritórios especializados em projetos de crédito rural, desenvolvida com **Django 5.2** e arquitetura multi-tenant. Oferece uma solução centralizada para controlar processos, finanças e operações com alta performance e segurança.

<div align="center">

[![Django](https://img.shields.io/badge/Django-5.2.5-092E20?style=for-the-badge&logo=django)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## 🚀 Início Rápido

### 📋 Pré-requisitos
- Python 3.11+
- PostgreSQL 13+
- Docker (opcional, recomendado)

### ⚡ Instalação Local

```bash
# 1. Clone o repositório
git clone https://github.com/usuario/nexiun.git
cd nexiun

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# 5. Execute os comandos de configuração inicial
python manage.py setup_permissions
python manage.py migrate
python manage.py populate_banks_credits
python manage.py collectstatic --noinput

# 6. Crie um superusuário
python manage.py createsuperuser

# 7. Execute o servidor
python manage.py runserver
```

### 🐳 Deploy com Docker

```bash
# Build e execução
docker build -t nexiun .
docker run -p 8000:8000 --env-file .env nexiun

# Acesse: http://localhost:8000
```

---

## 🎯 Funcionalidades Principais

### 🏢 **Multi-Tenant Architecture**
- **Isolamento completo** de dados entre empresas
- **Subdomínios automáticos**: `empresa.nexiun.com.br`
- **Personalização** de marca por empresa
- **Escalabilidade** horizontal automática

### 📊 **Gestão de Processos**
- **Kanban interativo** para acompanhamento de projetos
- **Dashboard em tempo real** com métricas personalizadas
- **Fluxo de aprovação** configurável por empresa
- **Notificações automáticas** de vencimentos e prazos

### 💰 **Controle Financeiro Avançado**
- **Gestão multi-unidade** com consolidação automática
- **Relatórios financeiros** em tempo real
- **Previsão de receitas** baseada em projetos
- **Controle de comissões** por captador/projetista

### 🏦 **Gestão de Bancos e Linhas de Crédito**
- **Catálogo completo** de bancos e linhas de crédito rurais
- **Comparativo automático** de condições
- **Histórico de aprovações** por instituição
- **Métricas de performance** por banco

### 🔐 **Segurança Empresarial**
- **Sistema de permissões** granular por módulo
- **Cargos hierárquicos** configuráveis
- **Auditoria completa** de ações
- **Criptografia SSL/TLS** obrigatória

---

## 🛠️ Comandos de Management

### 📝 **Comandos Essenciais**

```bash
# Configuração inicial do sistema de permissões
python manage.py setup_permissions
# Cria módulos do sistema, permissões customizadas e cargos padrão

# Popular bancos e linhas de crédito
python manage.py populate_banks_credits
# Opções:
# --enterprise "Nome da Empresa"  # Para empresa específica

# Migrações do banco de dados
python manage.py makemigrations
python manage.py migrate

# Coleta de arquivos estáticos
python manage.py collectstatic --noinput

# Criar superusuário
python manage.py createsuperuser

# Verificar configurações
python manage.py check --deploy
```

### 🔧 **Comandos de Desenvolvimento**

```bash
# Executar servidor de desenvolvimento
python manage.py runserver

# Shell interativo do Django
python manage.py shell

# Limpar sessões expiradas
python manage.py clearsessions

# Verificar migrações pendentes
python manage.py showmigrations

# Executar testes
python manage.py test
```

### 📊 **Comandos de Produção**

```bash
# Verificar configurações de produção
python manage.py check --deploy

# Coletar arquivos estáticos (S3)
python manage.py collectstatic --noinput

# Executar com Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

---

## 🏗️ Arquitetura do Sistema

### 📁 **Estrutura de Apps**

```
nexiun/
├── 🏠 home/           # Página inicial e dashboards
├── 👥 users/          # Autenticação e gestão de usuários
├── 🏢 enterprises/    # Gestão multi-tenant
├── 🏬 units/          # Unidades de negócio
├── 📋 projects/       # Projetos de crédito rural
└── ⚙️  core/          # Configurações principais
```

### 🔗 **Módulos do Sistema**

| Módulo | Funcionalidades | Permissões |
|--------|----------------|------------|
| **👥 Usuários** | Gestão de usuários, cargos e permissões | `view_users`, `add_users`, `manage_roles_users` |
| **📋 Projetos** | Criação, aprovação e acompanhamento | `view_projects`, `approve_projects`, `finalize_projects` |
| **💰 Financeiro** | Controle de receitas, despesas e comissões | `view_financial`, `manage_transactions` |
| **🏬 Unidades** | Gestão de unidades de negócio | `view_units`, `manage_units` |
| **🏢 Empresas** | Configurações multi-tenant | `manage_enterprise`, `view_enterprise` |

---

## 🔧 Stack Tecnológica

### 🐍 **Backend**
- **Django 5.2.5** - Framework web robusto e seguro
- **Python 3.11+** - Linguagem moderna e performática
- **Django REST Framework** - APIs RESTful para integrações
- **Gunicorn 22.0** - Servidor WSGI para produção

### 🗄️ **Banco de Dados**
- **PostgreSQL** - Banco relacional principal
- **psycopg 3.2.3** - Driver PostgreSQL otimizado
- **Migrations automáticas** - Versionamento de schema

### ☁️ **Infraestrutura**
- **Docker** - Containerização e deploy
- **AWS S3** - Armazenamento de arquivos
- **Cloudflare** - CDN e proteção DDoS
- **SSL/TLS** - Criptografia obrigatória

### 🎨 **Frontend**
- **Bootstrap 5** - Framework CSS responsivo
- **JavaScript Vanilla** - Interatividade nativa
- **Chart.js** - Gráficos e dashboards
- **Progressive Web App** - Experiência mobile

### 🔒 **Segurança**
- **python-decouple** - Gestão segura de configurações
- **Django Security** - Proteções CSRF, XSS, SQL Injection
- **Pillow 11.1** - Processamento seguro de imagens
- **Auditoria completa** - Log de todas as ações

---

## 📈 Analytics e Relatórios

### 📊 **Dashboards Dinâmicos**

**Análise de Performance:**
- 🎯 **Captadores**: Número de clientes e valor total captado
- 👨‍💼 **Projetistas**: Projetos aprovados e valor em análise
- 🏬 **Unidades**: Performance por região e categoria
- 🏦 **Bancos**: Tempo de aprovação e taxa de sucesso

**Segmentação Inteligente:**
- 🏷️ **Por categoria**: Pequeno, médio e grande produtor
- 📍 **Por unidade**: Comparativo regional
- 📅 **Por período**: Análise temporal de tendências
- 💰 **Por tipo**: Custeio vs. Investimento

### 📋 **Relatórios Especializados**
- 📈 **Vencimento de operações** com alertas automáticos
- 📞 **Carteira de contatos** segmentada por unidade
- 💼 **Pipeline de projetos** em tempo real
- 🎯 **Metas vs. Realizadas** por período

---

## 🌐 Configuração Multi-Tenant

### 🏢 **Domínios Configurados**
- **Principal**: `nexiun.com.br`
- **Wildcard**: `*.nexiun.com.br`
- **Desenvolvimento**: `*.nexiun.local`

### ⚙️ **Configuração de Produção**

```bash
# Variáveis de ambiente obrigatórias
SECRET_KEY=sua_chave_secreta_super_segura
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:port/db
AWS_ACCESS_KEY_ID=sua_chave_aws
AWS_SECRET_ACCESS_KEY=sua_chave_secreta_aws
AWS_STORAGE_BUCKET_NAME=seu_bucket_s3
```

---

## 📚 Documentação Avançada

### 🐳 **Deploy e DevOps**
- [`deploy/README.md`](deploy/README.md) - Guia completo de deploy
- [`deploy/DOCKER_SETUP.md`](deploy/DOCKER_SETUP.md) - Configuração Docker
- [`deploy/CLOUDFLARE_SETUP.md`](deploy/CLOUDFLARE_SETUP.md) - Integração Cloudflare

### 🔧 **Desenvolvimento**
- **Tests**: `python manage.py test` - Suite de testes automatizados
- **Linting**: Seguindo PEP 8 e Django best practices
- **Git Hooks**: Validação automática pre-commit

---

## 🤝 Contribuição

```bash
# Fork o projeto
git clone https://github.com/seu-usuario/nexiun.git

# Crie uma branch para sua feature
git checkout -b feature/nova-funcionalidade

# Faça suas alterações e commit
git commit -m "feat: adiciona nova funcionalidade X"

# Push para sua branch
git push origin feature/nova-funcionalidade

# Abra um Pull Request
```

### 📝 **Padrões de Commit**
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação
- `refactor:` - Refatoração
- `test:` - Testes

---

## 📞 Suporte e Contato

<div align="center">

### 💬 **Canais de Suporte**

| Canal | Descrição | Resposta |
|-------|-----------|----------|
| 📧 **Email** | [suporte@nexiun.com.br](mailto:suporte@nexiun.com.br) | 24h |
| 🐛 **Issues** | [GitHub Issues](https://github.com/usuario/nexiun/issues) | 48h |
| 📖 **Documentação** | [Wiki do Projeto](https://github.com/usuario/nexiun/wiki) | - |

</div>

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<div align="center">

**Desenvolvido com ❤️ para o Agronegócio Brasileiro**

[![Made with Django](https://img.shields.io/badge/Made%20with-Django-092E20?style=for-the-badge&logo=django)](https://djangoproject.com/)
[![Powered by Python](https://img.shields.io/badge/Powered%20by-Python-3776AB?style=for-the-badge&logo=python)](https://python.org/)

</div>
