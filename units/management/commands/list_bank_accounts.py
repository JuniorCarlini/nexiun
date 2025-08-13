from django.core.management.base import BaseCommand
from units.models import BankAccount


class Command(BaseCommand):
    help = 'Lista todas as contas bancárias disponíveis com seus IDs e estatísticas'

    def handle(self, *args, **options):
        accounts = BankAccount.objects.filter(is_active=True).order_by('id')
        
        if not accounts.exists():
            self.stdout.write(
                self.style.ERROR('Nenhuma conta bancária ativa encontrada.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'🏦 Contas bancárias ativas ({accounts.count()} total):')
        )
        self.stdout.write('')
        
        for account in accounts:
            # Calcular estatísticas da conta
            saldo_atual = account.get_current_balance()
            total_entradas = account.get_total_entradas()
            total_saidas = account.get_total_saidas()
            total_transacoes = account.transactions.filter(is_active=True).count()
            
            # Determinar cor do saldo
            if saldo_atual > 0:
                saldo_color = self.style.SUCCESS
            elif saldo_atual < 0:
                saldo_color = self.style.ERROR
            else:
                saldo_color = self.style.WARNING
            
            self.stdout.write(
                f'ID {account.id:2d}: {account.bank_name} - {account.name}'
            )
            self.stdout.write(f'      🏢 Unidade: {account.unit.name}')
            self.stdout.write(f'      💰 Saldo: {saldo_color(f"R$ {saldo_atual:,.2f}")}')
            self.stdout.write(f'      📊 Transações: {total_transacoes}')
            if total_transacoes > 0:
                self.stdout.write(f'         💚 Entradas: R$ {total_entradas:,.2f}')
                self.stdout.write(f'         💸 Saídas: R$ {total_saidas:,.2f}')
            self.stdout.write('')
        
        # Comando de exemplo
        self.stdout.write('💡 Exemplo de uso:')
        if accounts.exists():
            primeira_conta = accounts.first()
            self.stdout.write(
                f'   python manage.py populate_transactions {primeira_conta.id} --quantidade 30 --meses 3 --entradas 70'
            )
        self.stdout.write('')
        self.stdout.write('📝 Parâmetros disponíveis:')
        self.stdout.write('   --quantidade: Número de transações para gerar (padrão: 50)')
        self.stdout.write('   --meses: Período em meses (padrão: 6)')
        self.stdout.write('   --entradas: Porcentagem de entradas (padrão: 60)') 