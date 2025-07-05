import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_agent import SalonAIAgent

class TestSalonAIAgent(unittest.TestCase):
    def setUp(self):
        """Configura o ambiente de teste"""
        # Mock dos serviços externos
        with patch('ai_agent.DynamoDBService'), \
             patch('ai_agent.GoogleCalendarService'), \
             patch('ai_agent.genai.configure'):
            
            self.agent = SalonAIAgent()
            
            # Mock do modelo Gemini
            self.agent.model = Mock()
            
            # Mock dos serviços
            self.agent.db_service = Mock()
            self.agent.calendar_service = Mock()
    
    def test_process_message_greeting(self):
        """Testa o processamento de mensagem de saudação"""
        # Configura mocks
        self.agent.db_service.get_conversation_context.return_value = (False, {})
        self.agent.db_service.get_client.return_value = (False, {})
        self.agent.db_service.save_conversation_context.return_value = (True, "")
        
        # Mock da resposta do Gemini
        mock_response = Mock()
        mock_response.text = '''
        {
            "message": "Olá! Bem-vindo ao nosso salão! Como posso ajudá-lo hoje?",
            "action": "show_services",
            "data": {}
        }
        '''
        self.agent.model.generate_content.return_value = mock_response
        
        # Mock dos serviços disponíveis
        self.agent.db_service.get_all_services.return_value = (True, [
            {"service_id": "corte_feminino", "name": "Corte Feminino", "price": 50.0},
            {"service_id": "manicure", "name": "Manicure", "price": 20.0}
        ])
        
        # Testa o processamento
        result = self.agent.process_message("5511999999999", "Olá")
        
        # Verifica o resultado
        self.assertIn("message", result)
        self.assertIsInstance(result["message"], str)
        self.assertTrue(len(result["message"]) > 0)
    
    def test_show_services(self):
        """Testa a exibição de serviços"""
        # Mock dos serviços
        mock_services = [
            {"service_id": "corte_feminino", "name": "Corte Feminino", "price": 50.0},
            {"service_id": "manicure", "name": "Manicure", "price": 20.0},
            {"service_id": "pedicure", "name": "Pedicure", "price": 25.0}
        ]
        self.agent.db_service.get_all_services.return_value = (True, mock_services)
        
        # Testa a função
        result = self.agent.show_services("Aqui estão nossos serviços:")
        
        # Verifica o resultado
        self.assertIn("message", result)
        self.assertIn("buttons", result)
        self.assertIsNotNone(result["buttons"])
        self.assertEqual(len(result["buttons"]), 3)  # Máximo 3 botões
    
    def test_check_availability_success(self):
        """Testa verificação de disponibilidade com sucesso"""
        # Mock do serviço
        mock_service = {
            "service_id": "corte_feminino",
            "name": "Corte Feminino",
            "duration_minutes": 60,
            "price": 50.0
        }
        self.agent.db_service.get_service.return_value = (True, mock_service)
        
        # Mock dos slots disponíveis
        tomorrow = datetime.now() + timedelta(days=1)
        mock_slots = [
            {
                "start": tomorrow.replace(hour=10, minute=0),
                "end": tomorrow.replace(hour=11, minute=0),
                "formatted": "10:00 - 11:00"
            },
            {
                "start": tomorrow.replace(hour=14, minute=0),
                "end": tomorrow.replace(hour=15, minute=0),
                "formatted": "14:00 - 15:00"
            }
        ]
        self.agent.calendar_service.get_available_slots.return_value = mock_slots
        
        # Dados de teste
        data = {
            "date": "2024-01-15",
            "service_id": "corte_feminino"
        }
        
        # Testa a função
        result = self.agent.check_availability("Verificando disponibilidade...", data)
        
        # Verifica o resultado
        self.assertIn("message", result)
        self.assertIn("buttons", result)
        self.assertIsNotNone(result["buttons"])
        self.assertTrue(len(result["buttons"]) > 0)
    
    def test_check_availability_no_slots(self):
        """Testa verificação de disponibilidade sem horários"""
        # Mock do serviço
        mock_service = {
            "service_id": "corte_feminino",
            "name": "Corte Feminino",
            "duration_minutes": 60,
            "price": 50.0
        }
        self.agent.db_service.get_service.return_value = (True, mock_service)
        
        # Mock sem slots disponíveis
        self.agent.calendar_service.get_available_slots.return_value = []
        
        # Dados de teste
        data = {
            "date": "2024-01-15",
            "service_id": "corte_feminino"
        }
        
        # Testa a função
        result = self.agent.check_availability("Verificando disponibilidade...", data)
        
        # Verifica o resultado
        self.assertIn("message", result)
        self.assertIn("não temos horários disponíveis", result["message"])
        self.assertIsNone(result["buttons"])
    
    def test_create_appointment_success(self):
        """Testa criação de agendamento com sucesso"""
        # Mock do agendamento no banco
        self.agent.db_service.create_appointment.return_value = (True, "appointment_123")
        
        # Mock do serviço
        mock_service = {
            "service_id": "corte_feminino",
            "name": "Corte Feminino",
            "duration_minutes": 60,
            "price": 50.0
        }
        self.agent.db_service.get_service.return_value = (True, mock_service)
        
        # Mock do Google Calendar
        self.agent.calendar_service.create_appointment.return_value = (True, {"id": "calendar_event_123"})
        
        # Dados de teste
        data = {
            "service_id": "corte_feminino",
            "date": "2024-01-15",
            "time": "14:00",
            "client_name": "João Silva"
        }
        
        context = {"state": "confirmation", "data": {}}
        
        # Testa a função
        result = self.agent.create_appointment("5511999999999", "Criando agendamento...", data, context)
        
        # Verifica o resultado
        self.assertIn("message", result)
        self.assertIn("confirmado", result["message"])
        self.assertIn("✅", result["message"])
    
    def test_create_appointment_missing_data(self):
        """Testa criação de agendamento com dados incompletos"""
        # Dados incompletos
        data = {
            "service_id": "corte_feminino",
            "date": "2024-01-15"
            # Falta o time
        }
        
        context = {"state": "confirmation", "data": {}}
        
        # Testa a função
        result = self.agent.create_appointment("5511999999999", "Criando agendamento...", data, context)
        
        # Verifica o resultado
        self.assertIn("message", result)
        self.assertIn("incompletas", result["message"])
    
    def test_show_appointments_with_appointments(self):
        """Testa exibição de agendamentos existentes"""
        # Usa datas futuras para o teste
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        future_date2 = (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d')
        
        # Mock dos agendamentos
        mock_appointments = [
            {
                "appointment_id": "apt_1",
                "appointment_date": future_date,
                "appointment_time": "14:00",
                "service_name": "Corte Feminino",
                "price": 50.0,
                "status": "scheduled"
            },
            {
                "appointment_id": "apt_2",
                "appointment_date": future_date2,
                "appointment_time": "10:00",
                "service_name": "Manicure",
                "price": 20.0,
                "status": "scheduled"
            }
        ]
        self.agent.db_service.get_appointments_by_phone.return_value = (True, mock_appointments)
        
        # Testa a função
        result = self.agent.show_appointments("5511999999999", "Seus agendamentos:")
        
        # Verifica o resultado
        self.assertIn("message", result)
        self.assertIn("agendamentos", result["message"])
        self.assertIn(future_date, result["message"])
        self.assertIn("Corte Feminino", result["message"])
    
    def test_show_appointments_no_appointments(self):
        """Testa exibição quando não há agendamentos"""
        # Mock sem agendamentos
        self.agent.db_service.get_appointments_by_phone.return_value = (True, [])
        
        # Testa a função
        result = self.agent.show_appointments("5511999999999", "Seus agendamentos:")
        
        # Verifica o resultado
        self.assertIn("message", result)
        self.assertIn("não possui agendamentos", result["message"])

if __name__ == '__main__':
    unittest.main()

