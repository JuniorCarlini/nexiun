from django.core.management.base import BaseCommand
from enterprises.models import Client
import re


class Command(BaseCommand):
    help = 'Remove formatação dos telefones salvos no banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra quais telefones seriam alterados sem modificar o banco',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Modo DRY-RUN: Nenhuma alteração será feita no banco')
            )
        
        clients_with_formatted_phones = Client.objects.exclude(phone__isnull=True).exclude(phone='')
        total_clients = clients_with_formatted_phones.count()
        
        if total_clients == 0:
            self.stdout.write(
                self.style.SUCCESS('Nenhum cliente com telefone encontrado.')
            )
            return
        
        self.stdout.write(f'Encontrados {total_clients} clientes com telefone.')
        
        updated_count = 0
        
        for client in clients_with_formatted_phones:
            original_phone = client.phone
            
            # Remove todos os caracteres que não são dígitos
            clean_phone = re.sub(r'\D', '', str(original_phone))
            
            if original_phone != clean_phone:
                self.stdout.write(
                    f'Cliente: {client.name} | '
                    f'Original: "{original_phone}" → '
                    f'Limpo: "{clean_phone}"'
                )
                
                if not dry_run:
                    client.phone = clean_phone
                    client.save(update_fields=['phone'])
                
                updated_count += 1
            else:
                self.stdout.write(
                    f'Cliente: {client.name} | '
                    f'Telefone já está limpo: "{original_phone}"'
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY-RUN: {updated_count} telefones seriam atualizados.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Sucesso! {updated_count} telefones foram atualizados.')
            )
            
        if updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS('Todos os telefones já estavam no formato correto.')
            ) 