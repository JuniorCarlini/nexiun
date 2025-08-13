from django.core.management.base import BaseCommand
from django.db import transaction
from projects.models import Bank, CreditLine
from enterprises.models import Enterprise

class Command(BaseCommand):
    help = 'Popula bancos e linhas de crédito no sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enterprise',
            type=str,
            help='Nome ou ID da empresa específica (opcional, se não especificado, cria para todas)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏦 Populando bancos e linhas de crédito...'))
        
        # Determinar empresas para processar
        enterprise_filter = options.get('enterprise')
        if enterprise_filter:
            try:
                # Tentar buscar por ID primeiro, depois por nome
                if enterprise_filter.isdigit():
                    enterprises = Enterprise.objects.filter(id=int(enterprise_filter))
                else:
                    enterprises = Enterprise.objects.filter(name__icontains=enterprise_filter)
                
                if not enterprises.exists():
                    self.stdout.write(self.style.ERROR(f'❌ Empresa não encontrada: {enterprise_filter}'))
                    return
                    
                self.stdout.write(f'📋 Processando empresa(s): {[e.name for e in enterprises]}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erro ao buscar empresa: {str(e)}'))
                return
        else:
            enterprises = Enterprise.objects.all()
            if not enterprises.exists():
                self.stdout.write(self.style.ERROR('❌ Nenhuma empresa encontrada no sistema'))
                return
            self.stdout.write(f'📋 Processando todas as empresas ({enterprises.count()})')
        
        try:
            with transaction.atomic():
                # Bancos
                banks_data = [
                    {
                        'name': 'Banco do Brasil',
                        'description': 'Fundado em 1808, é o banco mais antigo do Brasil e um dos maiores da América Latina. Possui participação acionária majoritária do governo federal e forte atuação no agronegócio, varejo, câmbio, seguros e gestão de ativos.',
                        'is_active': True
                    },
                    {
                        'name': 'Banco da Amazônia',
                        'description': 'Banco público federal criado em 1942, com foco no desenvolvimento econômico e social da região Norte. Opera principalmente com recursos do Fundo Constitucional de Financiamento do Norte (FNO).',
                        'is_active': True
                    },
                    {
                        'name': 'Bradesco',
                        'description': 'Fundado em 1943 em Marília (SP), é um dos maiores bancos privados do Brasil, com mais de 70 milhões de clientes. Foi pioneiro em internet banking e em serviços de autoatendimento.',
                        'is_active': True
                    },
                    {
                        'name': 'Caixa Econômica Federal',
                        'description': 'Criada em 1861, é um banco público com forte papel em políticas habitacionais, gestão do FGTS, programas sociais (como Bolsa Família) e loterias federais.',
                        'is_active': True
                    },
                    {
                        'name': 'Cresol',
                        'description': 'Sistema de cooperativas de crédito fundado em 1995, com foco no financiamento rural e desenvolvimento local, especialmente para agricultores familiares.',
                        'is_active': True
                    },
                    {
                        'name': 'Sicoob',
                        'description': 'Maior sistema cooperativo de crédito do Brasil, com mais de 7 milhões de cooperados. Atua no crédito rural, financiamentos pessoais e empresariais, cartões e seguros.',
                        'is_active': True
                    },
                    {
                        'name': 'Santander Brasil',
                        'description': 'Subsidiária do grupo espanhol Santander, presente no Brasil desde 1982. É o terceiro maior banco privado do país, atendendo cerca de 70 milhões de clientes.',
                        'is_active': True
                    },
                    {
                        'name': 'CrediSis',
                        'description': 'Sistema cooperativo de crédito com atuação regional, oferecendo conta corrente, empréstimos, financiamentos e linhas de crédito rural.',
                        'is_active': True
                    }
                ]

                # Criar bancos para cada empresa
                total_banks_created = 0
                for enterprise in enterprises:
                    self.stdout.write(f'\n🏢 Processando empresa: {enterprise.name}')
                    
                    banks_created = 0
                    for bank_data in banks_data:
                        bank, created = Bank.objects.get_or_create(
                            name=bank_data['name'],
                            enterprise=enterprise,
                            defaults={
                                'description': bank_data['description'],
                                'is_active': bank_data['is_active']
                            }
                        )
                        if created:
                            banks_created += 1
                            total_banks_created += 1
                            self.stdout.write(f'  ✅ Banco criado: {bank.name}')
                        else:
                            self.stdout.write(f'  📄 Banco já existe: {bank.name}')
                    
                    self.stdout.write(f'  📊 Bancos criados para {enterprise.name}: {banks_created}')

                # Linhas de Crédito
                credit_lines_data = [
                    {
                        'name': 'Pronaf Custeio',
                        'description': 'Linha do Programa Nacional de Fortalecimento da Agricultura Familiar voltada para financiar despesas de produção agrícola e pecuária de agricultores familiares.',
                        'is_active': True,
                        'type_credit': 'CUS'
                    },
                    {
                        'name': 'Custeio Agropecuário',
                        'description': 'Crédito para financiar a produção agropecuária, cobrindo despesas como insumos, sementes, ração e defensivos agrícolas. Disponível para produtores de diversos portes.',
                        'is_active': True,
                        'type_credit': 'CUS'
                    },
                    {
                        'name': 'Pronamp Custeio',
                        'description': 'Linha do Programa Nacional de Apoio ao Médio Produtor Rural, destinada a financiar despesas de custeio de safra e criação animal.',
                        'is_active': True,
                        'type_credit': 'CUS'
                    },
                    {
                        'name': 'BB CPR',
                        'description': 'Crédito vinculado à Cédula de Produto Rural (CPR), que permite antecipar recursos com base na entrega futura da produção.',
                        'is_active': True,
                        'type_credit': 'OTH'
                    },
                    {
                        'name': 'Pronaf Mais Alimentos',
                        'description': 'Linha do Pronaf voltada ao investimento na modernização da produção e melhoria da infraestrutura da propriedade.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'Pronaf Mulher',
                        'description': 'Linha exclusiva para mulheres agricultoras familiares, com condições diferenciadas de financiamento.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'Pronamp Investimento',
                        'description': 'Crédito para financiar bens e serviços destinados à modernização e ampliação da atividade agropecuária de médio porte.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'Investe Agro',
                        'description': 'Linha para investimentos no setor agropecuário, incluindo aquisição de máquinas, equipamentos e melhoria de infraestrutura.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'PCA (Programa para Construção e Ampliação de Armazéns)',
                        'description': 'Crédito destinado à construção, ampliação, modernização e reforma de armazéns para produtos agropecuários.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'RenovAgro',
                        'description': 'Linha que financia práticas agrícolas sustentáveis, recuperação de pastagens e integração lavoura-pecuária-floresta.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'InovAgro',
                        'description': 'Crédito para adoção de inovações tecnológicas no setor agropecuário, como agricultura de precisão e automação.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'ModerFrota',
                        'description': 'Programa para financiar a aquisição de tratores, colheitadeiras e máquinas agrícolas novas.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'ProIrriga',
                        'description': 'Linha de crédito para sistemas de irrigação e armazenagem de água para uso agropecuário.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'FNO Rural (Custeio)',
                        'description': 'Crédito do Fundo Constitucional de Financiamento do Norte para custeio e investimento na produção agropecuária na região Norte.',
                        'is_active': True,
                        'type_credit': 'CUS'
                    },
                    {
                        'name': 'FNO Rural (Investimento)',
                        'description': 'Crédito do Fundo Constitucional de Financiamento do Norte para custeio e investimento na produção agropecuária na região Norte.',
                        'is_active': True,
                        'type_credit': 'INV'
                    },
                    {
                        'name': 'Cresol Agro',
                        'description': 'Linha de crédito rural da Cresol para custeio, investimento e comercialização da produção agropecuária.',
                        'is_active': True,
                        'type_credit': 'OTH'
                    }
                ]

                # Criar linhas de crédito para cada empresa
                total_credits_created = 0
                for enterprise in enterprises:
                    self.stdout.write(f'\n💳 Processando linhas de crédito para: {enterprise.name}')
                    
                    credits_created = 0
                    for credit_data in credit_lines_data:
                        credit, created = CreditLine.objects.get_or_create(
                            name=credit_data['name'],
                            enterprise=enterprise,
                            defaults={
                                'description': credit_data['description'],
                                'is_active': credit_data['is_active'],
                                'type_credit': credit_data['type_credit']
                            }
                        )
                        if created:
                            credits_created += 1
                            total_credits_created += 1
                            self.stdout.write(f'  ✅ Linha de crédito criada: {credit.name} (Tipo: {credit.get_type_credit_display()})')
                        else:
                            self.stdout.write(f'  📄 Linha de crédito já existe: {credit.name}')
                    
                    self.stdout.write(f'  📊 Linhas criadas para {enterprise.name}: {credits_created}')

                # Resumo
                self.stdout.write(self.style.SUCCESS('\n📊 RESUMO FINAL:'))
                self.stdout.write(f'  🏢 Empresas processadas: {enterprises.count()}')
                self.stdout.write(f'  🏦 Total de bancos criados: {total_banks_created}')
                self.stdout.write(f'  💳 Total de linhas de crédito criadas: {total_credits_created}')
                self.stdout.write(f'  📋 Total de bancos no sistema: {Bank.objects.count()}')
                self.stdout.write(f'  📋 Total de linhas de crédito no sistema: {CreditLine.objects.count()}')
                
                self.stdout.write(self.style.SUCCESS('\n🎉 Bancos e linhas de crédito populados com sucesso!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao popular dados: {str(e)}'))
            raise e 