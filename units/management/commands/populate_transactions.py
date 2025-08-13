from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from units.models import BankAccount, Transaction, Unit
from users.models import User
import random
from datetime import datetime, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Popula transações de entrada e saída em uma conta bancária específica'

    def add_arguments(self, parser):
        parser.add_argument(
            'bank_account_id',
            type=int,
            help='ID da conta bancária para popular'
        )
        parser.add_argument(
            '--quantidade',
            type=int,
            default=50,
            help='Quantidade de transações para gerar - padrão 50'
        )
        parser.add_argument(
            '--meses',
            type=int,
            default=6,
            help='Período em meses para gerar transações - padrão 6 meses'
        )
        parser.add_argument(
            '--entradas',
            type=int,
            default=60,
            help='Porcentagem de entradas - padrão 60 porcento'
        )

    def handle(self, *args, **options):
        bank_account_id = options['bank_account_id']
        quantidade = options['quantidade']
        meses = options['meses']
        entradas_percent = options['entradas']
        
        # Validar conta bancária
        try:
            bank_account = BankAccount.objects.get(id=bank_account_id, is_active=True)
        except BankAccount.DoesNotExist:
            raise CommandError(f'Conta bancária com ID {bank_account_id} não encontrada ou inativa.')
        
        # Verificar se há usuários disponíveis
        user = User.objects.filter(is_active=True).first()
        if not user:
            raise CommandError('Nenhum usuário ativo encontrado para criar as transações.')
        
        self.stdout.write(f'Populando {quantidade} transações na conta: {bank_account}')
        self.stdout.write(f'Unidade: {bank_account.unit}')
        self.stdout.write(f'Período: {meses} meses')
        self.stdout.write(f'Distribuição: {entradas_percent}% entradas, {100-entradas_percent}% saídas')
        self.stdout.write('')
        
        # Calcular datas
        data_final = timezone.now().date()
        data_inicial = data_final - timedelta(days=meses * 30)
        
        # Definir categorias e descrições
        entradas_data = {
            'RECEITA': [
                'Receita de vendas', 'Faturamento mensal', 'Receita de serviços',
                'Comissão de vendas', 'Lucro operacional', 'Receita extra'
            ],
            'COMISSAO': [
                'Comissão de vendedor', 'Comissão de parcerias', 'Comissão especial',
                'Bônus por meta', 'Incentivo de vendas'
            ],
            'BONUS': [
                'Bônus de produtividade', 'Bônus trimestral', 'Prêmio por performance',
                'Bônus de equipe', 'Incentivo especial'
            ],
            'REEMBOLSO': [
                'Reembolso de despesas', 'Devolução de compra', 'Estorno de taxa',
                'Reembolso de viagem', 'Compensação financeira'
            ]
        }
        
        saidas_data = {
            'MATERIAL': [
                'Papel A4 e materiais', 'Canetas e lápis', 'Impressora e toner',
                'Pastas e organizadores', 'Material de limpeza'
            ],
            'TRANSPORTE': [
                'Passagem de ônibus', 'Taxi para reunião', 'Uber corporativo',
                'Passagem de avião', 'Aluguel de veículo'
            ],
            'ALIMENTACAO': [
                'Almoço executivo', 'Coffee break reunião', 'Jantar com cliente',
                'Lanche da equipe', 'Restaurante corporativo'
            ],
            'COMBUSTIVEL': [
                'Gasolina veículo empresa', 'Diesel caminhão', 'Etanol carro',
                'Abastecimento frota', 'Combustível viagem'
            ],
            'MANUTENCAO': [
                'Manutenção de equipamentos', 'Reparo de computador', 'Troca de peças',
                'Manutenção predial', 'Limpeza de ar condicionado'
            ],
            'MARKETING': [
                'Publicidade online', 'Material gráfico', 'Evento promocional',
                'Anúncio em jornal', 'Marketing digital'
            ],
            'TREINAMENTO': [
                'Curso de capacitação', 'Workshop técnico', 'Palestra motivacional',
                'Treinamento de vendas', 'Certificação profissional'
            ],
            'OUTROS': [
                'Despesa administrativa', 'Taxa bancária', 'Multa de trânsito',
                'Seguro empresarial', 'Licenciamento'
            ]
        }
        
        # Gerar transações
        transacoes_criadas = 0
        quantidade_entradas = int(quantidade * entradas_percent / 100)
        quantidade_saidas = quantidade - quantidade_entradas
        
        with transaction.atomic():
            # Gerar entradas
            for i in range(quantidade_entradas):
                categoria = random.choice(list(entradas_data.keys()))
                descricao = random.choice(entradas_data[categoria])
                valor = Decimal(random.uniform(100, 5000)).quantize(Decimal('0.01'))
                data_transacao = data_inicial + timedelta(
                    days=random.randint(0, (data_final - data_inicial).days)
                )
                
                Transaction.objects.create(
                    unit=bank_account.unit,
                    bank_account=bank_account,
                    transaction_type='ENTRADA',
                    category=categoria,
                    description=descricao,
                    amount=valor,
                    date=data_transacao,
                    notes=f'Transação gerada automaticamente - {descricao}',
                    created_by=user,
                    is_active=True
                )
                transacoes_criadas += 1
            
            # Gerar saídas
            for i in range(quantidade_saidas):
                categoria = random.choice(list(saidas_data.keys()))
                descricao = random.choice(saidas_data[categoria])
                
                # Valores mais realistas para cada categoria
                if categoria in ['MATERIAL', 'ALIMENTACAO']:
                    valor = Decimal(random.uniform(10, 500)).quantize(Decimal('0.01'))
                elif categoria in ['TRANSPORTE', 'COMBUSTIVEL']:
                    valor = Decimal(random.uniform(20, 800)).quantize(Decimal('0.01'))
                elif categoria in ['MANUTENCAO', 'MARKETING']:
                    valor = Decimal(random.uniform(100, 2000)).quantize(Decimal('0.01'))
                elif categoria == 'TREINAMENTO':
                    valor = Decimal(random.uniform(200, 3000)).quantize(Decimal('0.01'))
                else:  # OUTROS
                    valor = Decimal(random.uniform(50, 1500)).quantize(Decimal('0.01'))
                
                data_transacao = data_inicial + timedelta(
                    days=random.randint(0, (data_final - data_inicial).days)
                )
                
                Transaction.objects.create(
                    unit=bank_account.unit,
                    bank_account=bank_account,
                    transaction_type='SAIDA',
                    category=categoria,
                    description=descricao,
                    amount=valor,
                    date=data_transacao,
                    notes=f'Transação gerada automaticamente - {descricao}',
                    created_by=user,
                    is_active=True
                )
                transacoes_criadas += 1
        
        # Calcular estatísticas
        total_entradas = bank_account.get_total_entradas()
        total_saidas = bank_account.get_total_saidas()
        saldo_atual = bank_account.get_current_balance()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ {transacoes_criadas} transações criadas com sucesso!'))
        self.stdout.write('')
        self.stdout.write('📊 Estatísticas da conta:')
        self.stdout.write(f'   💚 Total de entradas: R$ {total_entradas:,.2f}')
        self.stdout.write(f'   💸 Total de saídas: R$ {total_saidas:,.2f}')
        self.stdout.write(f'   💰 Saldo atual: R$ {saldo_atual:,.2f}')
        self.stdout.write('')
        self.stdout.write(f'🏦 Conta: {bank_account.bank_name} - {bank_account.name}')
        self.stdout.write(f'🏢 Unidade: {bank_account.unit.name}')
        self.stdout.write(f'👤 Criado por: {user.name} ({user.email})') 