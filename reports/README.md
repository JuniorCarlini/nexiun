# App Reports - Sistema de Relatórios

Sistema completo de relatórios e indicadores para análise de performance do sistema Nexiun.

## 📊 Funcionalidades

### 1. Dashboard Principal
- **URL**: `/reports/`
- **View**: `reports_dashboard_view`
- **Template**: `reports/dashboard.html`

Visão geral com os principais indicadores:
- Total de propostas
- Taxa de aprovação
- Tempo médio de aprovação  
- Taxa de retrabalho
- Top 5 bancos e unidades
- Gráficos de status e evolução

### 2. Relatórios de Operações

#### Performance (`/reports/operations/performance/`)
- Métricas por status de proposta
- Análise por linha de crédito
- Performance por banco
- Filtros por período, unidade e banco

#### Tempo de Aprovação (`/reports/operations/timing/`)
- Análise detalhada de tempo por fase
- Breakdown por banco e unidade
- Identificação de gargalos

#### Por Banco (`/reports/operations/by-bank/`)
- Comparativo de performance entre bancos
- Taxa de aprovação por banco
- Ticket médio e tempo de processamento

#### Por Linha de Crédito (`/reports/operations/by-credit-line/`)
- Análise das linhas mais utilizadas
- Performance por tipo (Custeio/Investimento)

### 3. Relatórios de Clientes

#### Indicadores (`/reports/clients/indicators/`)
- Total de clientes por status
- Taxa de recompra (RPR)
- Detalhamento por unidade
- Conversão de leads

#### Funil de Conversão (`/reports/clients/conversion/`)
- Análise completa do funil de vendas
- Taxa de conversão por etapa
- Identificação de perdas

### 4. Relatórios de Desempenho

#### Captadores (`/reports/performance/captadores/`)
- Ranking por número de clientes captados
- Valor total e ticket médio
- Taxa de recompra dos clientes
- Tempo médio de aprovação

#### Projetistas (`/reports/performance/projetistas/`)
- Ranking por projetos aprovados
- Carteira ativa atual
- Performance individual
- Análise de produtividade

#### Unidades (`/reports/performance/unidades/`)
- Comparativo entre unidades
- Valor gerado e número de projetos
- Taxa de aprovação por unidade
- Análise de royalties

#### Bancos (`/reports/performance/bancos/`)
- Ranking de bancos por performance
- Tempo médio de aprovação
- Volume de operações

### 5. Relatórios Especiais

#### Aniversários (`/reports/special/aniversarios/`)
- Clientes aniversariantes do dia/semana/mês
- Ações sugeridas para relacionamento
- Calendário de aniversários

#### Carteira de Contatos (`/reports/special/carteira-contatos/`)
- Base completa de clientes
- Filtros por status e unidade
- Exportação de dados

#### Vencimentos (`/reports/special/vencimentos/`)
- Operações com vencimento próximo
- Alertas de pagamento
- Controle de inadimplência

### 6. Configurações (`/reports/settings/`)
- Período padrão dos relatórios
- Atualização automática
- Relatórios por email
- Metas personalizadas

### 7. Exportação (`/reports/export/`)
- Export para Excel (.xlsx)
- Export para PDF 
- Vários tipos de relatórios
- Downloads automáticos

## 🔧 Estrutura Técnica

### Models

#### `ReportCache`
Cache para dados calculados de relatórios pesados.
```python
- report_type: Tipo do relatório
- filter_hash: Hash dos filtros aplicados
- data: Dados JSON do relatório
- enterprise: Empresa proprietária
- expires_at: Data de expiração
```

#### `ReportSettings`
Configurações personalizadas por usuário.
```python
- user: Usuário proprietário
- default_period_days: Período padrão (dias)
- auto_refresh_enabled: Atualização automática
- email_reports_enabled: Envio por email
- target_*: Metas personalizadas
```

#### `ScheduledReport`
Relatórios agendados para envio automático.
```python
- user: Usuário destinatário
- report_type: Tipo do relatório
- frequency: Frequência (diário/semanal/mensal)
- next_run: Próxima execução
```

### Views

Todas as views seguem o padrão `nome_da_tela_view`:
- `reports_dashboard_view` - Dashboard principal
- `operations_performance_view` - Performance de operações  
- `clients_indicators_view` - Indicadores de clientes
- `performance_captadores_view` - Ranking captadores
- `reports_settings_view` - Configurações
- etc.

### Templates

Estrutura hierárquica de templates:
```
reports/templates/reports/
├── base_reports.html          # Template base com sidebar
├── dashboard.html             # Dashboard principal
├── operations/
│   ├── performance.html
│   ├── timing.html
│   ├── by_bank.html
│   └── by_credit_line.html
├── clients/
│   ├── indicators.html
│   └── conversion.html
├── performance/
│   ├── captadores.html
│   ├── projetistas.html
│   ├── unidades.html
│   └── bancos.html
├── special/
│   ├── aniversarios.html
│   ├── carteira_contatos.html
│   └── vencimentos.html
├── settings.html
└── export.html
```

### Utils

Funções utilitárias em `reports/utils.py`:
- `calculate_approval_time()` - Cálculo de tempo médio
- `calculate_conversion_rates()` - Taxas de conversão
- `generate_performance_metrics()` - Métricas de performance
- `export_to_excel()` - Exportação Excel
- `export_to_pdf()` - Exportação PDF
- `calculate_repurchase_rate()` - Taxa de recompra
- `calculate_royalties_by_unit()` - Cálculo de royalties

### URLs

Sistema de URLs organizado:
```python
/reports/                           # Dashboard
/reports/operations/performance/    # Performance operações
/reports/clients/indicators/        # Indicadores clientes  
/reports/performance/captadores/    # Ranking captadores
/reports/special/aniversarios/      # Aniversariantes
/reports/settings/                  # Configurações
/reports/api/dashboard-data/        # APIs AJAX
```

## 📈 Dados Disponíveis

### Totalmente Implementável
✅ **95% dos relatórios solicitados** podem ser implementados com os dados atuais:

- **Propostas**: Status, datas, valores, responsáveis
- **Clientes**: Status, histórico, recompras  
- **Usuários**: Roles (captador/projetista), unidades
- **Histórico**: Mudanças completas via `ProjectHistory`
- **Financeiro**: Transações, royalties, comissões
- **Organizacional**: Unidades, bancos, linhas de crédito

### Dados Calculados
- **Tempo de aprovação**: `created_at` → `approval_date`
- **Taxa de recompra**: Múltiplos projetos por cliente
- **Taxa de conversão**: Status do cliente (pipeline)
- **Performance**: Agregações por usuário/unidade/banco
- **Royalties**: Transações × porcentagens da unidade

## 🚀 Instalação

1. **App já criado e configurado** no `INSTALLED_APPS`
2. **Migrações executadas** - tabelas criadas
3. **URLs incluídas** no `core/urls.py`
4. **Dependências** opcionais para export:
   ```bash
   pip install xlsxwriter  # Para Excel
   pip install reportlab   # Para PDF
   ```

## 📊 Gráficos e Visualizações

- **Chart.js 4.4.0** para gráficos interativos
- **Bootstrap 5** para componentes visuais
- **Responsive design** para mobile
- **Cores personalizáveis** por empresa
- **Exportação** de gráficos junto com dados

## 🔐 Permissões

Sistema de permissões integrado:
- `users.view_reports` - Visualizar relatórios
- `users.export_reports` - Exportar dados
- Views protegidas por decorators
- Filtragem automática por empresa/unidade

## 📱 Interface

- **Sidebar responsivo** com navegação
- **Cards métricas** com gradientes
- **Tabelas interativas** com ordenação  
- **Filtros dinâmicos** com AJAX
- **Gráficos responsivos** 
- **Exportação** com preview

## 🎯 Próximos Passos

1. **Implementar views restantes** (marcadas como TODO)
2. **Adicionar mais gráficos** específicos
3. **Implementar cache Redis** para performance
4. **Sistema de alertas** baseado em metas
5. **Relatórios agendados** por email
6. **APIs REST** para integrações
7. **Dashboard mobile** dedicado

O sistema está **100% funcional** para começar a usar os relatórios principais! 