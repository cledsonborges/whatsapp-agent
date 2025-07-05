import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestDynamoDBService(unittest.TestCase):
    def setUp(self):
        """Configura o ambiente de teste"""
        # Mock do boto3
        with patch('dynamodb_service.boto3'):
            from dynamodb_service import DynamoDBService
            
            self.service = DynamoDBService()
            
            # Mock das tabelas
            self.service.appointments_table = Mock()
            self.service.clients_table = Mock()
            self.service.services_table = Mock()
            self.service.conversations_table = Mock()
    
    def test_save_client_success(self):
        """Testa salvamento de cliente com sucesso"""
        # Mock da resposta do DynamoDB
        self.service.clients_table.put_item.return_value = {}
        
        # Testa a função
        success, message = self.service.save_client(
            phone_number="5511999999999",
            name="João Silva",
            email="joao@email.com"
        )
        
        # Verifica o resultado
        self.assertTrue(success)
        self.assertIn("sucesso", message)
        self.service.clients_table.put_item.assert_called_once()
    
    def test_save_client_error(self):
        """Testa salvamento de cliente com erro"""
        # Mock de erro
        self.service.clients_table.put_item.side_effect = Exception("Erro de conexão")
        
        # Testa a função
        success, message = self.service.save_client(
            phone_number="5511999999999",
            name="João Silva"
        )
        
        # Verifica o resultado
        self.assertFalse(success)
        self.assertIn("Erro", message)
    
    def test_get_client_found(self):
        """Testa busca de cliente encontrado"""
        # Mock da resposta do DynamoDB
        mock_client = {
            "phone_number": "5511999999999",
            "name": "João Silva",
            "email": "joao@email.com",
            "created_at": "2024-01-01T10:00:00"
        }
        self.service.clients_table.get_item.return_value = {"Item": mock_client}
        
        # Testa a função
        success, client = self.service.get_client("5511999999999")
        
        # Verifica o resultado
        self.assertTrue(success)
        self.assertEqual(client["name"], "João Silva")
        self.assertEqual(client["phone_number"], "5511999999999")
    
    def test_get_client_not_found(self):
        """Testa busca de cliente não encontrado"""
        # Mock sem item
        self.service.clients_table.get_item.return_value = {}
        
        # Testa a função
        success, message = self.service.get_client("5511999999999")
        
        # Verifica o resultado
        self.assertFalse(success)
        self.assertIn("não encontrado", message)
    
    def test_create_appointment_success(self):
        """Testa criação de agendamento com sucesso"""
        # Mock do serviço
        mock_service = {
            "service_id": "corte_feminino",
            "name": "Corte Feminino",
            "duration_minutes": 60,
            "price": 50.0
        }
        self.service.services_table.get_item.return_value = {"Item": mock_service}
        
        # Mock da criação do agendamento
        self.service.appointments_table.put_item.return_value = {}
        
        # Testa a função
        success, appointment_id = self.service.create_appointment(
            phone_number="5511999999999",
            service_id="corte_feminino",
            appointment_date="2024-01-15",
            appointment_time="14:00",
            client_name="João Silva"
        )
        
        # Verifica o resultado
        self.assertTrue(success)
        self.assertIsInstance(appointment_id, str)
        self.assertTrue(len(appointment_id) > 0)
        self.service.appointments_table.put_item.assert_called_once()
    
    def test_create_appointment_service_not_found(self):
        """Testa criação de agendamento com serviço não encontrado"""
        # Mock sem serviço
        self.service.services_table.get_item.return_value = {}
        
        # Testa a função
        success, message = self.service.create_appointment(
            phone_number="5511999999999",
            service_id="servico_inexistente",
            appointment_date="2024-01-15",
            appointment_time="14:00"
        )
        
        # Verifica o resultado
        self.assertFalse(success)
        self.assertIn("não encontrado", message)
    
    def test_get_appointments_by_phone(self):
        """Testa busca de agendamentos por telefone"""
        # Mock dos agendamentos
        mock_appointments = [
            {
                "appointment_id": "apt_1",
                "phone_number": "5511999999999",
                "service_name": "Corte Feminino",
                "appointment_date": "2024-01-15",
                "appointment_time": "14:00",
                "status": "scheduled"
            },
            {
                "appointment_id": "apt_2",
                "phone_number": "5511999999999",
                "service_name": "Manicure",
                "appointment_date": "2024-01-16",
                "appointment_time": "10:00",
                "status": "scheduled"
            }
        ]
        self.service.appointments_table.query.return_value = {"Items": mock_appointments}
        
        # Testa a função
        success, appointments = self.service.get_appointments_by_phone("5511999999999")
        
        # Verifica o resultado
        self.assertTrue(success)
        self.assertEqual(len(appointments), 2)
        self.assertEqual(appointments[0]["service_name"], "Corte Feminino")
    
    def test_get_all_services(self):
        """Testa busca de todos os serviços"""
        # Mock dos serviços
        mock_services = [
            {
                "service_id": "corte_feminino",
                "name": "Corte Feminino",
                "duration_minutes": 60,
                "price": 50.0
            },
            {
                "service_id": "manicure",
                "name": "Manicure",
                "duration_minutes": 45,
                "price": 20.0
            }
        ]
        self.service.services_table.scan.return_value = {"Items": mock_services}
        
        # Testa a função
        success, services = self.service.get_all_services()
        
        # Verifica o resultado
        self.assertTrue(success)
        self.assertEqual(len(services), 2)
        self.assertEqual(services[0]["name"], "Corte Feminino")
        self.assertEqual(services[1]["name"], "Manicure")
    
    def test_update_appointment_status(self):
        """Testa atualização de status do agendamento"""
        # Mock da atualização
        self.service.appointments_table.update_item.return_value = {}
        
        # Testa a função
        success, message = self.service.update_appointment_status("apt_123", "cancelled")
        
        # Verifica o resultado
        self.assertTrue(success)
        self.assertIn("sucesso", message)
        self.service.appointments_table.update_item.assert_called_once()
    
    def test_save_conversation_context(self):
        """Testa salvamento do contexto da conversa"""
        # Mock do salvamento
        self.service.conversations_table.put_item.return_value = {}
        
        # Contexto de teste
        context = {
            "state": "service_selection",
            "data": {"selected_service": "corte_feminino"}
        }
        
        # Testa a função
        success, message = self.service.save_conversation_context("5511999999999", context)
        
        # Verifica o resultado
        self.assertTrue(success)
        self.assertIn("sucesso", message)
        self.service.conversations_table.put_item.assert_called_once()
    
    def test_get_conversation_context_found(self):
        """Testa busca de contexto da conversa encontrado"""
        # Mock do contexto
        mock_context = {
            "state": "service_selection",
            "data": {"selected_service": "corte_feminino"}
        }
        mock_item = {
            "phone_number": "5511999999999",
            "context": '{"state": "service_selection", "data": {"selected_service": "corte_feminino"}}',
            "updated_at": "2024-01-01T10:00:00"
        }
        self.service.conversations_table.get_item.return_value = {"Item": mock_item}
        
        # Testa a função
        success, context = self.service.get_conversation_context("5511999999999")
        
        # Verifica o resultado
        self.assertTrue(success)
        self.assertEqual(context["state"], "service_selection")
        self.assertEqual(context["data"]["selected_service"], "corte_feminino")
    
    def test_get_conversation_context_not_found(self):
        """Testa busca de contexto da conversa não encontrado"""
        # Mock sem item
        self.service.conversations_table.get_item.return_value = {}
        
        # Testa a função
        success, context = self.service.get_conversation_context("5511999999999")
        
        # Verifica o resultado
        self.assertFalse(success)
        self.assertEqual(context, {})

if __name__ == '__main__':
    unittest.main()

