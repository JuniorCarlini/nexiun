import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from enterprises.models import Client, Enterprise
from units.models import Unit
from users.models import User


class Command(BaseCommand):
    help = 'Importa clientes de um arquivo CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Caminho para o arquivo CSV'
        )
        parser.add_argument(
            '--enterprise-id',
            type=int,
            help='ID da empresa (opcional, usa a primeira se não especificado)'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID do usuário que está importando (opcional)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a importação sem salvar no banco'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # Verificar se arquivo existe
        if not os.path.exists(csv_file):
            raise CommandError(f'Arquivo não encontrado: {csv_file}')

        # Buscar empresa
        if options['enterprise_id']:
            try:
                enterprise = Enterprise.objects.get(id=options['enterprise_id'])
            except Enterprise.DoesNotExist:
                raise CommandError(f'Empresa com ID {options["enterprise_id"]} não encontrada')
        else:
            enterprise = Enterprise.objects.first()
            if not enterprise:
                raise CommandError('Nenhuma empresa encontrada. Crie uma empresa primeiro.')

        # Buscar usuário
        user = None
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
            except User.DoesNotExist:
                raise CommandError(f'Usuário com ID {options["user_id"]} não encontrado')

        self.stdout.write(f'Importando clientes para empresa: {enterprise.name}')
        if user:
            self.stdout.write(f'Usuário responsável: {user.name}')

        # Contadores
        total_rows = 0
        imported_count = 0
        skipped_count = 0
        error_count = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                # Detectar delimitador
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.reader(file, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, 1):
                    total_rows += 1
                    
                    # Pular linhas vazias
                    if not any(row) or len(row) < 6:
                        skipped_count += 1
                        continue

                    try:
                        # Extrair dados da linha
                        # Formato: Nome, Endereço, Telefone, Data Nascimento, CPF, Unidade, Projetista
                        name = row[0].strip() if len(row) > 0 else ''
                        address = row[1].strip() if len(row) > 1 else ''
                        phone = row[2].strip() if len(row) > 2 else ''
                        birth_date_str = row[3].strip() if len(row) > 3 else ''
                        cpf = row[4].strip() if len(row) > 4 else ''
                        unit_name = row[5].strip() if len(row) > 5 else ''
                        project_manager = row[6].strip() if len(row) > 6 else ''

                        # Validar campos obrigatórios
                        if not name:
                            self.stdout.write(
                                self.style.WARNING(f'Linha {row_num}: Nome vazio, pulando...')
                            )
                            skipped_count += 1
                            continue

                        # Processar CPF (remover formatação)
                        if cpf:
                            cpf = cpf.replace('.', '').replace('-', '').replace(' ', '')
                            if len(cpf) == 11 and cpf.isdigit():
                                cpf = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
                            else:
                                cpf = ''

                        # Processar telefone (limpar formatação)
                        if phone:
                            phone = phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
                            if phone.startswith('69'):
                                phone = f'({phone[:2]}) {phone[2:7]}-{phone[7:]}' if len(phone) == 11 else phone
                            elif phone.startswith('9') and len(phone) == 9:
                                phone = f'(69) {phone[:5]}-{phone[5:]}'

                        # Processar data de nascimento
                        birth_date = None
                        if birth_date_str:
                            try:
                                # Tentar diferentes formatos
                                for fmt in ['%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y']:
                                    try:
                                        birth_date = datetime.strptime(birth_date_str, fmt).date()
                                        break
                                    except ValueError:
                                        continue
                                
                                if not birth_date:
                                    self.stdout.write(
                                        self.style.WARNING(f'Linha {row_num}: Data inválida "{birth_date_str}", ignorando...')
                                    )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f'Linha {row_num}: Erro ao processar data: {e}')
                                )

                        # Buscar ou criar unidade
                        unit = None
                        if unit_name:
                            unit, created = Unit.objects.get_or_create(
                                name=unit_name,
                                enterprise=enterprise,
                                defaults={
                                    'location': 'Importado via CSV',
                                    'is_active': True
                                }
                            )
                            if created:
                                self.stdout.write(f'Unidade criada: {unit_name}')

                        # Verificar se cliente já existe (por CPF)
                        existing_client = None
                        if cpf:
                            existing_client = Client.objects.filter(cpf=cpf, enterprise=enterprise).first()
                        
                        if existing_client:
                            self.stdout.write(
                                self.style.WARNING(f'Linha {row_num}: Cliente já existe (CPF: {cpf}), pulando...')
                            )
                            skipped_count += 1
                            continue

                        if not options['dry_run']:
                            # Criar cliente
                            with transaction.atomic():
                                client = Client.objects.create(
                                    name=name,
                                    email=f'{name.lower().replace(" ", ".")}@importado.com',  # Email temporário
                                    cpf=cpf,
                                    phone=phone,
                                    address=address,
                                    date_of_birth=birth_date,
                                    enterprise=enterprise,
                                    created_by=user,
                                    status='INATIVO',
                                    is_active=True
                                )
                                
                                # Adicionar unidade se especificada
                                if unit:
                                    client.units.add(unit)
                                
                                # Adicionar observação sobre o projetista se especificado
                                if project_manager:
                                    client.observations = f'Projetista: {project_manager}'
                                    client.save()

                        imported_count += 1
                        
                        if options['dry_run']:
                            self.stdout.write(f'[DRY RUN] Linha {row_num}: {name} - {unit_name or "Sem unidade"}')
                        else:
                            self.stdout.write(f'✓ Linha {row_num}: {name} importado')

                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'Erro na linha {row_num}: {str(e)}')
                        )
                        continue

        except Exception as e:
            raise CommandError(f'Erro ao ler arquivo: {str(e)}')

        # Relatório final
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RELATÓRIO DE IMPORTAÇÃO')
        self.stdout.write('='*50)
        self.stdout.write(f'Total de linhas processadas: {total_rows}')
        self.stdout.write(f'Clientes importados: {imported_count}')
        self.stdout.write(f'Linhas puladas: {skipped_count}')
        self.stdout.write(f'Erros: {error_count}')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\nMODO DRY RUN - Nenhum dado foi salvo'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nImportação concluída! {imported_count} clientes importados.'))
