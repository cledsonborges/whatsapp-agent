import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
import json
import uuid
from config.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        self.create_tables()
    
    def create_tables(self):
        """Cria as tabelas necessárias no DynamoDB se não existirem"""
        try:
            # Tabela de agendamentos
            self.appointments_table = self.create_appointments_table()
            
            # Tabela de clientes
            self.clients_table = self.create_clients_table()
            
            # Tabela de serviços
            self.services_table = self.create_services_table()
            
            # Tabela de conversas (para manter contexto)
            self.conversations_table = self.create_conversations_table()
            
            print("Tabelas DynamoDB configuradas com sucesso!")
            
        except Exception as e:
            print(f"Erro ao configurar tabelas DynamoDB: {str(e)}")
    
    def create_appointments_table(self):
        """Cria a tabela de agendamentos"""
        table_name = 'salon_appointments'
        
        try:
            table = self.dynamodb.Table(table_name)
            table.load()
            print(f"Tabela {table_name} já existe")
            return table
        except:
            # Tabela não existe, criar
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'appointment_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'appointment_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'phone_number',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'appointment_date',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'phone-date-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'phone_number',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'appointment_date',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            # Aguarda a tabela ser criada
            table.wait_until_exists()
            print(f"Tabela {table_name} criada com sucesso")
            return table
    
    def create_clients_table(self):
        """Cria a tabela de clientes"""
        table_name = 'salon_clients'
        
        try:
            table = self.dynamodb.Table(table_name)
            table.load()
            print(f"Tabela {table_name} já existe")
            return table
        except:
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'phone_number',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'phone_number',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            table.wait_until_exists()
            print(f"Tabela {table_name} criada com sucesso")
            return table
    
    def create_services_table(self):
        """Cria a tabela de serviços"""
        table_name = 'salon_services'
        
        try:
            table = self.dynamodb.Table(table_name)
            table.load()
            print(f"Tabela {table_name} já existe")
            return table
        except:
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'service_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'service_id',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            table.wait_until_exists()
            print(f"Tabela {table_name} criada com sucesso")
            
            # Adiciona serviços padrão
            self.populate_default_services(table)
            return table
    
    def create_conversations_table(self):
        """Cria a tabela de conversas"""
        table_name = 'salon_conversations'
        
        try:
            table = self.dynamodb.Table(table_name)
            table.load()
            print(f"Tabela {table_name} já existe")
            return table
        except:
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'phone_number',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'phone_number',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            table.wait_until_exists()
            print(f"Tabela {table_name} criada com sucesso")
            return table
    
    def populate_default_services(self, table):
        """Popula a tabela de serviços com dados padrão"""
        default_services = [
            {
                'service_id': 'corte_feminino',
                'name': 'Corte Feminino',
                'duration_minutes': 60,
                'price': 50.00,
                'description': 'Corte de cabelo feminino'
            },
            {
                'service_id': 'corte_masculino',
                'name': 'Corte Masculino',
                'duration_minutes': 30,
                'price': 25.00,
                'description': 'Corte de cabelo masculino'
            },
            {
                'service_id': 'manicure',
                'name': 'Manicure',
                'duration_minutes': 45,
                'price': 20.00,
                'description': 'Manicure completa'
            },
            {
                'service_id': 'pedicure',
                'name': 'Pedicure',
                'duration_minutes': 60,
                'price': 25.00,
                'description': 'Pedicure completa'
            },
            {
                'service_id': 'hidratacao',
                'name': 'Hidratação',
                'duration_minutes': 90,
                'price': 40.00,
                'description': 'Hidratação capilar'
            },
            {
                'service_id': 'escova',
                'name': 'Escova',
                'duration_minutes': 45,
                'price': 30.00,
                'description': 'Escova progressiva'
            }
        ]
        
        for service in default_services:
            try:
                table.put_item(Item=service)
                print(f"Serviço {service['name']} adicionado")
            except Exception as e:
                print(f"Erro ao adicionar serviço {service['name']}: {str(e)}")
    
    # Métodos para gerenciar clientes
    def save_client(self, phone_number, name=None, email=None, preferences=None):
        """Salva ou atualiza informações do cliente"""
        try:
            item = {
                'phone_number': phone_number,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if name:
                item['name'] = name
            if email:
                item['email'] = email
            if preferences:
                item['preferences'] = preferences
            
            self.clients_table.put_item(Item=item)
            return True, "Cliente salvo com sucesso"
        
        except Exception as e:
            return False, f"Erro ao salvar cliente: {str(e)}"
    
    def get_client(self, phone_number):
        """Obtém informações do cliente"""
        try:
            response = self.clients_table.get_item(
                Key={'phone_number': phone_number}
            )
            
            if 'Item' in response:
                return True, response['Item']
            else:
                return False, "Cliente não encontrado"
        
        except Exception as e:
            return False, f"Erro ao buscar cliente: {str(e)}"
    
    # Métodos para gerenciar agendamentos
    def create_appointment(self, phone_number, service_id, appointment_date, appointment_time, client_name=None):
        """Cria um novo agendamento"""
        try:
            appointment_id = str(uuid.uuid4())
            
            # Obtém informações do serviço
            service_info = self.get_service(service_id)
            if not service_info[0]:
                return False, "Serviço não encontrado"
            
            service = service_info[1]
            
            item = {
                'appointment_id': appointment_id,
                'phone_number': phone_number,
                'service_id': service_id,
                'service_name': service['name'],
                'appointment_date': appointment_date,
                'appointment_time': appointment_time,
                'duration_minutes': service['duration_minutes'],
                'price': service['price'],
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if client_name:
                item['client_name'] = client_name
            
            self.appointments_table.put_item(Item=item)
            return True, appointment_id
        
        except Exception as e:
            return False, f"Erro ao criar agendamento: {str(e)}"
    
    def get_appointments_by_phone(self, phone_number):
        """Obtém agendamentos de um cliente"""
        try:
            response = self.appointments_table.query(
                IndexName='phone-date-index',
                KeyConditionExpression=Key('phone_number').eq(phone_number)
            )
            
            return True, response['Items']
        
        except Exception as e:
            return False, f"Erro ao buscar agendamentos: {str(e)}"
    
    def get_appointments_by_date(self, date):
        """Obtém todos os agendamentos de uma data específica"""
        try:
            response = self.appointments_table.scan(
                FilterExpression=Attr('appointment_date').eq(date)
            )
            
            return True, response['Items']
        
        except Exception as e:
            return False, f"Erro ao buscar agendamentos por data: {str(e)}"
    
    def update_appointment_status(self, appointment_id, status):
        """Atualiza o status de um agendamento"""
        try:
            self.appointments_table.update_item(
                Key={'appointment_id': appointment_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated_at': datetime.now().isoformat()
                }
            )
            
            return True, "Status atualizado com sucesso"
        
        except Exception as e:
            return False, f"Erro ao atualizar status: {str(e)}"
    
    # Métodos para gerenciar serviços
    def get_all_services(self):
        """Obtém todos os serviços disponíveis"""
        try:
            response = self.services_table.scan()
            return True, response['Items']
        
        except Exception as e:
            return False, f"Erro ao buscar serviços: {str(e)}"
    
    def get_service(self, service_id):
        """Obtém informações de um serviço específico"""
        try:
            response = self.services_table.get_item(
                Key={'service_id': service_id}
            )
            
            if 'Item' in response:
                return True, response['Item']
            else:
                return False, "Serviço não encontrado"
        
        except Exception as e:
            return False, f"Erro ao buscar serviço: {str(e)}"
    
    # Métodos para gerenciar conversas
    def save_conversation_context(self, phone_number, context):
        """Salva o contexto da conversa"""
        try:
            item = {
                'phone_number': phone_number,
                'context': json.dumps(context),
                'updated_at': datetime.now().isoformat()
            }
            
            self.conversations_table.put_item(Item=item)
            return True, "Contexto salvo com sucesso"
        
        except Exception as e:
            return False, f"Erro ao salvar contexto: {str(e)}"
    
    def get_conversation_context(self, phone_number):
        """Obtém o contexto da conversa"""
        try:
            response = self.conversations_table.get_item(
                Key={'phone_number': phone_number}
            )
            
            if 'Item' in response:
                context = json.loads(response['Item']['context'])
                return True, context
            else:
                return False, {}
        
        except Exception as e:
            return False, {}

# Exemplo de uso
if __name__ == "__main__":
    db_service = DynamoDBService()
    
    # Testa criação de cliente
    success, message = db_service.save_client(
        phone_number="5511999999999",
        name="João Silva",
        email="joao@email.com"
    )
    print(f"Criar cliente: {success} - {message}")
    
    # Testa busca de serviços
    success, services = db_service.get_all_services()
    if success:
        print(f"Serviços disponíveis: {len(services)}")
        for service in services:
            print(f"  - {service['name']}: R$ {service['price']}")
    
    # Testa criação de agendamento
    success, appointment_id = db_service.create_appointment(
        phone_number="5511999999999",
        service_id="corte_feminino",
        appointment_date="2024-01-15",
        appointment_time="14:00",
        client_name="João Silva"
    )
    print(f"Criar agendamento: {success} - {appointment_id}")

