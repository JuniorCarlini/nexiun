from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.utils import timezone
from enterprises.models import Client, Enterprise
from users.models import User
from units.models import Unit
from projects.models import Project, CreditLine, Bank
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Apaga tudo e popula o sistema completo com dados de exemplo'

    def handle(self, *args, **options):
        
        self.stdout.write(
            self.style.WARNING('🗑️  LIMPANDO DADOS EXISTENTES...')
        )
        
        # Limpar dados (manter empresa principal e CEOs)
        from users.models import Role
        
        # Sempre preservar superusers (CEOs)
        User.objects.filter(is_superuser=False, is_staff=False).delete()
            
        Client.objects.all().delete()
        Project.objects.all().delete()
        Unit.objects.all().delete()
        CreditLine.objects.all().delete()
        Bank.objects.all().delete()
        
        # Preservar role CEO se existir
        Role.objects.exclude(code='ceo').delete()
        
        # Buscar ou criar empresa principal
        enterprise = Enterprise.objects.first()
        if not enterprise:
            self.stdout.write('\n🏢 CRIANDO EMPRESA...')
            enterprise = Enterprise.objects.create(
                name='Agro Capital',
                cnpj_or_cpf='12345678000123',
                primary_color='#05667C',
                secondary_color='#FFB837',
                text_icons_color='#EDE4D'
            )
            self.stdout.write(f'  ✅ Empresa criada: {enterprise.name}')
            
        self.stdout.write(f'🏢 Empresa: {enterprise.name}')
        
        # 1. CRIAR UNIDADES
        self.stdout.write('\n📍 CRIANDO UNIDADES...')
        unidades_data = [
            {'name': 'Matriz', 'location': 'Av. Central, 100, Centro Empresarial'},
            {'name': 'Filial Norte', 'location': 'Av. Norte, 456, Zona Norte'},
            {'name': 'Filial Sul', 'location': 'Rua Sul, 789, Zona Sul'},
            {'name': 'Filial Centro', 'location': 'Rua Principal, 123, Centro'},
            {'name': 'Filial Oeste', 'location': 'Av. Oeste, 321, Zona Oeste'},
            {'name': 'Saldus Jipa', 'location': 'Rua Jipa, 500, Saldus'},
        ]
        
        unidades = []
        for unit_data in unidades_data:
            unit = Unit.objects.create(
                name=unit_data['name'],
                location=unit_data['location'],
                enterprise=enterprise
            )
            unidades.append(unit)
            self.stdout.write(f'  ✅ {unit.name}')
        
        # 2. CRIAR ROLES/CARGOS
        self.stdout.write('\n🎭 CRIANDO CARGOS...')
        from users.models import Role
        
        roles_data = [
            {'name': 'CEO', 'code': 'ceo'},
            {'name': 'Sócio Unidade', 'code': 'socio_unidade'},
            {'name': 'Gerente', 'code': 'gerente'},
            {'name': 'Supervisor', 'code': 'supervisor'},
            {'name': 'Consultor', 'code': 'consultor'},
            {'name': 'Consultora', 'code': 'consultora'},
        ]
        
        roles = {}
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults={'name': role_data['name']}
            )
            roles[role_data['code']] = role
            if created:
                self.stdout.write(f'  ✅ {role.name}')
            else:
                self.stdout.write(f'  ✅ {role.name} (já existia)')
        
        # 3. CRIAR USUÁRIOS/FUNCIONÁRIOS
        self.stdout.write('\n👥 CRIANDO USUÁRIOS...')
        usuarios_data = [
            {'name': 'Junior Silva', 'email': 'junior@saldus.com', 'role_code': 'socio_unidade', 'unit': 'Saldus Jipa'},
            {'name': 'Maria Santos', 'email': 'maria@Nexiun.com', 'role_code': 'gerente', 'unit': 'Matriz'},
            {'name': 'João Oliveira', 'email': 'joao@Nexiun.com', 'role_code': 'consultor', 'unit': 'Filial Norte'},
            {'name': 'Ana Costa', 'email': 'ana@Nexiun.com', 'role_code': 'consultora', 'unit': 'Filial Sul'},
            {'name': 'Carlos Lima', 'email': 'carlos@Nexiun.com', 'role_code': 'supervisor', 'unit': 'Filial Centro'},
            {'name': 'Fernanda Rocha', 'email': 'fernanda@Nexiun.com', 'role_code': 'consultora', 'unit': 'Filial Oeste'},
        ]
        
        usuarios = []
        for user_data in usuarios_data:
            unit = Unit.objects.get(name=user_data['unit'], enterprise=enterprise)
            user = User.objects.create_user(
                email=user_data['email'],
                password='123456',
                name=user_data['name'],
                phone=f"11{random.randint(900000000, 999999999)}",
                enterprise=enterprise,
                unit=unit
            )
            
            # Associar role
            role = roles[user_data['role_code']]
            user.roles.add(role)
            
            # Adicionar permissões
            permissions = Permission.objects.filter(
                codename__in=['view_clients', 'view_all_clients', 'add_clients', 'change_clients']
            )
            user.user_permissions.add(*permissions)
            
            usuarios.append(user)
            self.stdout.write(f'  ✅ {user.name} - {role.name} ({unit.name})')
        
        # 3.1. VERIFICAR/CRIAR CEO
        ceo_users = User.objects.filter(is_superuser=True, enterprise=enterprise)
        if not ceo_users.exists():
            self.stdout.write('\n👑 CRIANDO CEO...')
            matriz = Unit.objects.get(name='Matriz', enterprise=enterprise)
            ceo = User.objects.create_superuser(
                email='admin@Nexiun.com',
                password='123456',
                name='Admin CEO',
                phone=f"11{random.randint(900000000, 999999999)}",
                enterprise=enterprise,
                unit=matriz
            )
            ceo.roles.add(roles['ceo'])
            self.stdout.write(f'  ✅ {ceo.name} - CEO (Matriz)')
        else:
            self.stdout.write('\n👑 CEO JÁ EXISTE:')
            for ceo in ceo_users:
                # Garantir que o CEO tenha o role CEO
                if not ceo.roles.filter(code='ceo').exists():
                    ceo.roles.add(roles['ceo'])
                self.stdout.write(f'  ✅ {ceo.name} - CEO ({ceo.unit.name if ceo.unit else "Sem unidade"})')
        
        # 4. CRIAR BANCOS E LINHAS DE CRÉDITO
        self.stdout.write('\n🏦 CRIANDO BANCOS E LINHAS DE CRÉDITO...')
        
        bancos_data = [
            'Banco do Brasil', 'Caixa Econômica Federal', 'Itaú', 'Bradesco', 
            'Santander', 'Banco do Nordeste', 'BNDES', 'Sicredi'
        ]
        
        bancos = []
        for banco_name in bancos_data:
            banco = Bank.objects.create(
                name=banco_name,
                description=f'Banco {banco_name}',
                enterprise=enterprise
            )
            bancos.append(banco)
            self.stdout.write(f'  ✅ {banco.name}')
        
        # Linhas de crédito
        linhas_credito = [
            {'name': 'PRONAF Custeio', 'description': 'Financiamento para custeio agrícola'},
            {'name': 'PRONAF Investimento', 'description': 'Financiamento para investimentos rurais'},
            {'name': 'FCO Rural', 'description': 'Fundo Constitucional do Centro-Oeste'},
            {'name': 'MODERAGRO', 'description': 'Modernização da Agricultura e Conservação'},
            {'name': 'ABC Cerrado', 'description': 'Agricultura de Baixo Carbono'},
            {'name': 'PROCEDER', 'description': 'Programa de Incentivo à Irrigação'},
        ]
        
        credit_lines = []
        for linha_data in linhas_credito:
            credit_line = CreditLine.objects.create(
                name=linha_data['name'],
                description=linha_data['description'],
                enterprise=enterprise
            )
            credit_lines.append(credit_line)
            self.stdout.write(f'  ✅ {credit_line.name}')
        
        # 5. CRIAR CLIENTES
        self.stdout.write('\n👤 CRIANDO CLIENTES...')
        
        nomes_clientes = [
            'Fazenda São João - Antonio Silva', 'Sítio Boa Vista - Maria Fernandes',
            'Rancho Verde - José Santos', 'Fazenda Esperança - Pedro Oliveira',
            'Estância Feliz - Ana Rodrigues', 'Fazenda Progresso - Carlos Mendes',
            'Sítio Bela Vista - Lucia Costa', 'Rancho Alegre - Roberto Lima',
            'Fazenda Prosperidade - Helena Souza', 'Estância Dourada - Fernando Alves',
            'Fazenda Nova Era - Mariana Torres', 'Sítio Recanto - Paulo Cardoso',
            'Rancho Esperança - Isabel Martins', 'Fazenda Vitória - Rodrigo Pereira',
            'Estância Bonita - Carmen Ribeiro', 'Fazenda Horizonte - Miguel Barbosa',
            'Sítio Paraíso - Teresa Gomes', 'Rancho Felicidade - Eduardo Dias',
            'Fazenda Sucesso - Beatriz Morais', 'Estância Real - Francisco Cunha',
            'Fazenda Liberdade - Sophia Araújo', 'Sítio Harmonia - Gabriel Freitas',
            'Rancho Família - Juliana Lopes', 'Fazenda Futuro - Ricardo Barros',
            'Estância Moderna - Patricia Silva', 'Fazenda União - Alexandre Costa',
            'Sítio Amizade - Camila Santos', 'Rancho Tradição - Leonardo Reis',
            'Fazenda Conquista - Larissa Fernandes', 'Estância Nobre - Bruno Carvalho'
        ]
        
        cidades = [
            'Campo Grande', 'Dourados', 'Três Lagoas', 'Corumbá', 'Ponta Porã',
            'Aquidauana', 'Naviraí', 'Nova Andradina', 'Coxim', 'Maracaju',
            'Sidrolândia', 'Bonito', 'Miranda', 'Jardim', 'Anastácio'
        ]
        
        status_choices = ['INATIVO', 'INTERESSADO', 'EM_NEGOCIACAO', 'ATIVO']
        
        clientes = []
        for i, nome in enumerate(nomes_clientes):
            user_criador = random.choice(usuarios)
            unidade = random.choice(unidades)
            
            status = random.choice(status_choices)
            retorno_ate = None
            if status == 'EM_NEGOCIACAO':
                retorno_ate = date.today() + timedelta(days=random.randint(1, 5))
            
            client = Client.objects.create(
                name=nome,
                email=f"cliente{i+1}@fazenda{i+1}.com.br",
                phone=f"{random.choice(['65', '67', '66'])}{random.randint(900000000, 999999999)}",
                address=f"Zona Rural, Lote {random.randint(1, 999)}",
                city=random.choice(cidades),
                status=status,
                retorno_ate=retorno_ate,
                enterprise=enterprise,
                created_by=user_criador,
                is_active=random.choice([True, True, True, False])  # 75% ativos
            )
            
            # Associar a 1-2 unidades
            num_units = random.choices([1, 2], weights=[0.8, 0.2])[0]
            selected_units = random.sample(unidades, min(num_units, len(unidades)))
            client.units.set(selected_units)
            
            clientes.append(client)
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f'  ✅ {i + 1} clientes criados...')
        
        self.stdout.write(f'  ✅ Total: {len(clientes)} clientes')
        
        # 6. CRIAR PROJETOS
        self.stdout.write('\n📋 CRIANDO PROJETOS...')
        
        project_status = ['AC', 'PE', 'AN', 'AP', 'AF', 'FM', 'LB', 'RC']
        
        projetos = []
        # Criar projetos para alguns clientes (40% dos clientes)
        clientes_com_projetos = random.sample(clientes, int(len(clientes) * 0.4))
        
        for client in clientes_com_projetos:
            # Cada cliente pode ter 1-3 projetos
            num_projetos = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            
            for _ in range(num_projetos):
                project = Project.objects.create(
                    client=client,
                    credit_line=random.choice(credit_lines),
                    bank=random.choice(bancos),
                    unit=random.choice(list(client.units.all())),
                    value=random.randint(50000, 2000000),
                    installments=random.choice([5, 10, 15, 20]),
                    payment_grace=random.choice([1, 2, 3]),
                    fees=random.uniform(3.5, 12.5),
                    status=random.choice(project_status),
                    enterprise=enterprise,
                    project_manager=random.choice(usuarios)
                )
                projetos.append(project)
        
        self.stdout.write(f'  ✅ Total: {len(projetos)} projetos')
        
        # 7. ESTATÍSTICAS FINAIS
        self.stdout.write('\n📊 ESTATÍSTICAS FINAIS:')
        self.stdout.write(f'  🏢 Empresa: {enterprise.name}')
        self.stdout.write(f'  📍 Unidades: {Unit.objects.filter(enterprise=enterprise).count()}')
        total_users = User.objects.filter(enterprise=enterprise).count()
        ceo_count = User.objects.filter(enterprise=enterprise, is_superuser=True).count()
        regular_users = total_users - ceo_count
        self.stdout.write(f'  👥 Usuários: {total_users} ({ceo_count} CEO + {regular_users} funcionários)')
        self.stdout.write(f'  👤 Clientes: {Client.objects.filter(enterprise=enterprise).count()}')
        self.stdout.write(f'  🏦 Bancos: {Bank.objects.filter(enterprise=enterprise).count()}')
        self.stdout.write(f'  💳 Linhas de Crédito: {CreditLine.objects.filter(enterprise=enterprise).count()}')
        self.stdout.write(f'  📋 Projetos: {Project.objects.filter(enterprise=enterprise).count()}')
        
        # Distribuição de clientes por status
        self.stdout.write('\n📈 CLIENTES POR STATUS:')
        for status_code, status_label in Client.objects.model._meta.get_field('status').choices:
            count = Client.objects.filter(enterprise=enterprise, status=status_code).count()
            self.stdout.write(f'  {status_label}: {count}')
        
        # Distribuição de projetos por status
        self.stdout.write('\n📊 PROJETOS POR STATUS:')
        status_names = {
            'AC': 'Acolhimento', 'PE': 'Pendência', 'AN': 'Análise', 'AP': 'Aprovado',
            'AF': 'Formalização', 'FM': 'Formalizado', 'LB': 'Liberado', 'RC': 'Receita'
        }
        for status_code, status_name in status_names.items():
            count = Project.objects.filter(enterprise=enterprise, status=status_code).count()
            self.stdout.write(f'  {status_name}: {count}')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 SISTEMA POPULADO COM SUCESSO!')
        )
        self.stdout.write('💡 Todos os usuários têm senha: 123456')
        self.stdout.write('👑 CEOs existentes são sempre preservados')
        self.stdout.write('📧 Email do CEO criado: admin@Nexiun.com') 