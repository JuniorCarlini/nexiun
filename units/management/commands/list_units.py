from django.core.management.base import BaseCommand
from units.models import Unit
from enterprises.models import Client


class Command(BaseCommand):
    help = 'Lista todas as unidades disponíveis com seus IDs e estatísticas'

    def handle(self, *args, **options):
        units = Unit.objects.all().order_by('id')
        
        if not units.exists():
            self.stdout.write(
                self.style.ERROR('Nenhuma unidade encontrada.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Unidades disponíveis ({units.count()} total):')
        )
        self.stdout.write('')
        
        for unit in units:
            # Contar clientes na unidade
            clients_count = Client.objects.filter(units=unit).count()
            
            # Status da unidade
            status = "Ativa" if unit.is_active else "Inativa"
            status_color = self.style.SUCCESS if unit.is_active else self.style.ERROR
            
            self.stdout.write(
                f'ID {unit.id:2d}: {unit.name} - {status_color(status)}'
            )
            self.stdout.write(f'      Localização: {unit.location}')
            self.stdout.write(f'      Clientes: {clients_count}')
            self.stdout.write('')
        
        # Estatísticas gerais
        total_clients = Client.objects.count()
        clients_with_units = Client.objects.filter(units__isnull=False).distinct().count()
        clients_without_units = total_clients - clients_with_units
        
        self.stdout.write('Estatísticas:')
        self.stdout.write(f'  - Total de clientes: {total_clients}')
        self.stdout.write(f'  - Clientes com unidades: {clients_with_units}')
        if clients_without_units > 0:
            self.stdout.write(
                self.style.WARNING(f'  - Clientes sem unidades: {clients_without_units}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('  - Todos os clientes têm unidades atribuídas')
            ) 