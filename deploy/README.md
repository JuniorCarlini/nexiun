# 🚀 Deploy - Nexiun Multi-Tenant System

Esta pasta contém todos os arquivos relacionados ao deployment e configuração do sistema Nexiun.

## 📁 **ESTRUTURA DE ARQUIVOS:**

### **🐳 Docker & Containers:**
- `Dockerfile` - Configuração principal do container
- `.dockerignore` - Arquivos ignorados no build
- `entrypoint.sh` - Script de inicialização automática
- `nginx.conf` - Configuração Nginx para produção

### **📚 Documentação de Deploy:**
- `DOCKER_SETUP.md` - **PRINCIPAL** - Como usar Docker
- `CLOUDFLARE_EAZYPANEL_SETUP.md` - Configuração Cloudflare + EazyPanel
- `EASYPANEL_WILDCARD_OFICIAL.md` - Wildcard domains (oficial)
- `EAZYPANEL_SUBDOMAIN_CONFIG.md` - Configuração subdomínios manual
- `EAZYPANEL_WILDCARD_SETUP.md` - Configuração wildcard alternativa
- `EAZYPANEL_MIGRATE_FIX.md` - Correção de problemas de migração

## 🎯 **GUIA RÁPIDO DE DEPLOY:**

### **1. Deploy Automático (Recomendado):**
```bash
# Só fazer push - tudo automático!
git add .
git commit -m "deploy"
git push

# EazyPanel automaticamente:
# ✅ Build do Dockerfile
# ✅ Executa migrações
# ✅ Coleta arquivos estáticos
# ✅ Configura wildcard SSL
```

### **2. Teste Local:**
```bash
# Build e teste
docker build -t nexiun .
docker run -p 8000:8000 --env-file .env nexiun

# Testar: http://localhost:8000
```

## 🌐 **SISTEMA MULTI-TENANT:**

O sistema está configurado para:
- ✅ **Domain principal**: `nexiun.com.br`
- ✅ **Wildcard SSL**: `*.nexiun.com.br`
- ✅ **Subdomínios automáticos**: `empresa.nexiun.com.br`
- ✅ **Redirecionamento inteligente**
- ✅ **Personalização por empresa**

## 🔧 **CONFIGURAÇÕES APLICADAS:**

### **Dockerfile Features:**
- ✅ Migrações automáticas no startup
- ✅ Collectstatic automático
- ✅ Criação de superusuário automática
- ✅ Verificação de saúde do banco
- ✅ Logs coloridos e informativos
- ✅ Otimizado para PostgreSQL externo

### **Middleware Configurado:**
- ✅ SubdomainMiddleware (detecção automática)
- ✅ EnterpriseRequiredMiddleware (controle de acesso)
- ✅ CSRF_TRUSTED_ORIGINS configurado

### **DNS & SSL:**
- ✅ Cloudflare DNS wildcard
- ✅ SSL automático via Traefik
- ✅ Certificados renovados automaticamente

## 📋 **CHECKLIST DE PRODUÇÃO:**

### **EazyPanel:**
- [ ] Projeto criado com Dockerfile
- [ ] Variáveis de ambiente configuradas
- [ ] Wildcard domain `*.nexiun.com.br` configurado
- [ ] SSL/TLS habilitado

### **Cloudflare:**
- [ ] Domínio `nexiun.com.br` adicionado
- [ ] Registro A: `*` → `[IP_EAZYPANEL]`
- [ ] SSL mode: Full (strict)
- [ ] Proxy desabilitado para DNS challenge

### **Django:**
- [ ] ALLOWED_HOSTS configurado
- [ ] CSRF_TRUSTED_ORIGINS configurado
- [ ] Middleware de subdomínios ativo
- [ ] Banco PostgreSQL conectado

## 🚨 **TROUBLESHOOTING:**

### **Problema comum: "CSRF verification failed"**
- **Solução**: Verificar CSRF_TRUSTED_ORIGINS no settings.py

### **Problema comum: "no such table: enterprises_enterprise"**
- **Solução**: Executar migrações (automático no Dockerfile)

### **Problema comum: "Domain not accessible"**
- **Solução**: Verificar DNS wildcard e SSL no EazyPanel

## 📞 **COMANDOS ÚTEIS:**

```bash
# Verificar configurações
python manage.py check_subdomain_setup
python manage.py test_csrf
python manage.py check_docker_setup

# Deploy manual (se necessário)
docker build -t nexiun .
docker run --env-file .env nexiun python manage.py migrate
docker run --env-file .env nexiun python manage.py collectstatic --noinput
```

## 🎉 **STATUS ATUAL:**

```
✅ Sistema multi-tenant funcionando
✅ Wildcard domains configurados
✅ SSL automático ativo
✅ Migrações automáticas
✅ Deploy automático configurado
✅ Pronto para produção!
```

---

**📖 Para detalhes específicos, consulte os arquivos .md individuais nesta pasta.** 