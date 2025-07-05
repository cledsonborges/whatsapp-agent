import google.generativeai as genai
from datetime import datetime, timedelta
import json
import re
from config.config import GEMINI_API_KEY
from dynamodb_service import DynamoDBService
from google_calendar_service import GoogleCalendarService

class SalonAIAgent:
    def __init__(self):
        # Configura o Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Inicializa serviços
        self.db_service = DynamoDBService()
        self.calendar_service = GoogleCalendarService()
        
        # Estados da conversa
        self.conversation_states = {
            'GREETING': 'greeting',
            'SERVICE_SELECTION': 'service_selection',
            'DATE_SELECTION': 'date_selection',
            'TIME_SELECTION': 'time_selection',
            'CONFIRMATION': 'confirmation',
            'COMPLETED': 'completed',
            'HELP': 'help'
        }
        
        # Prompt do sistema para o agente
        self.system_prompt = """
        Você é um assistente de IA para um salão de beleza. Seu objetivo é ajudar os clientes a agendar serviços de forma amigável e eficiente.

        SERVIÇOS DISPONÍVEIS:
        - Corte Feminino (60 min) - R$ 50,00
        - Corte Masculino (30 min) - R$ 25,00
        - Manicure (45 min) - R$ 20,00
        - Pedicure (60 min) - R$ 25,00
        - Hidratação (90 min) - R$ 40,00
        - Escova (45 min) - R$ 30,00

        HORÁRIO DE FUNCIONAMENTO:
        - Segunda a Sexta: 9h às 18h
        - Sábado: 9h às 16h
        - Domingo: Fechado

        INSTRUÇÕES:
        1. Seja sempre amigável e profissional
        2. Ajude o cliente a escolher o serviço desejado
        3. Sugira datas e horários disponíveis
        4. Confirme todos os detalhes antes de finalizar
        5. Se não entender algo, peça esclarecimentos
        6. Mantenha as respostas concisas mas informativas

        FORMATO DE RESPOSTA:
        Sempre responda em formato JSON com as seguintes chaves:
        {
            "message": "Sua resposta para o cliente",
            "action": "próxima ação a ser executada",
            "data": "dados relevantes para a ação"
        }

        AÇÕES POSSÍVEIS:
        - "show_services": Mostrar lista de serviços
        - "check_availability": Verificar disponibilidade
        - "create_appointment": Criar agendamento
        - "show_appointments": Mostrar agendamentos existentes
        - "cancel_appointment": Cancelar agendamento
        - "continue_conversation": Continuar conversa normal
        """
    
    def process_message(self, phone_number, message_text):
        """Processa uma mensagem do cliente e retorna a resposta"""
        try:
            # Obtém o contexto da conversa
            success, context = self.db_service.get_conversation_context(phone_number)
            if not success:
                context = {'state': self.conversation_states['GREETING'], 'data': {}}
            
            # Obtém informações do cliente
            client_success, client_info = self.db_service.get_client(phone_number)
            if client_success:
                context['client_info'] = client_info
            
            # Gera resposta usando IA
            response = self.generate_ai_response(message_text, context)
            
            # Processa a ação solicitada
            result = self.process_action(phone_number, response, context)
            
            # Salva o contexto atualizado
            self.db_service.save_conversation_context(phone_number, context)
            
            return result
        
        except Exception as e:
            print(f"Erro ao processar mensagem: {str(e)}")
            return {
                "message": "Desculpe, ocorreu um erro. Tente novamente em alguns instantes.",
                "buttons": None
            }
    
    def generate_ai_response(self, message_text, context):
        """Gera resposta usando o modelo Gemini"""
        try:
            # Constrói o prompt com contexto
            prompt = f"""
            {self.system_prompt}
            
            CONTEXTO DA CONVERSA:
            Estado atual: {context.get('state', 'greeting')}
            Dados da conversa: {json.dumps(context.get('data', {}), ensure_ascii=False)}
            
            MENSAGEM DO CLIENTE: "{message_text}"
            
            Responda em formato JSON válido.
            """
            
            response = self.model.generate_content(prompt)
            
            # Tenta extrair JSON da resposta
            response_text = response.text
            
            # Remove markdown se presente
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            # Parse do JSON
            try:
                ai_response = json.loads(response_text.strip())
            except json.JSONDecodeError:
                # Se não conseguir fazer parse, cria resposta padrão
                ai_response = {
                    "message": response_text.strip(),
                    "action": "continue_conversation",
                    "data": {}
                }
            
            return ai_response
        
        except Exception as e:
            print(f"Erro ao gerar resposta IA: {str(e)}")
            return {
                "message": "Olá! Como posso ajudá-lo hoje? Gostaria de agendar um serviço?",
                "action": "continue_conversation",
                "data": {}
            }
    
    def process_action(self, phone_number, ai_response, context):
        """Processa a ação solicitada pela IA"""
        action = ai_response.get('action', 'continue_conversation')
        message = ai_response.get('message', '')
        data = ai_response.get('data', {})
        
        result = {
            "message": message,
            "buttons": None
        }
        
        if action == "show_services":
            result = self.show_services(message)
        
        elif action == "check_availability":
            result = self.check_availability(message, data)
        
        elif action == "create_appointment":
            result = self.create_appointment(phone_number, message, data, context)
        
        elif action == "show_appointments":
            result = self.show_appointments(phone_number, message)
        
        elif action == "cancel_appointment":
            result = self.cancel_appointment(phone_number, message, data)
        
        # Atualiza o contexto se necessário
        if 'state' in data:
            context['state'] = data['state']
        if 'conversation_data' in data:
            context['data'].update(data['conversation_data'])
        
        return result
    
    def show_services(self, message):
        """Mostra os serviços disponíveis com botões"""
        success, services = self.db_service.get_all_services()
        
        if not success:
            return {
                "message": "Desculpe, não consegui carregar os serviços no momento. Tente novamente.",
                "buttons": None
            }
        
        # Cria botões para os serviços
        buttons = []
        for service in services[:3]:  # Máximo 3 botões por mensagem no WhatsApp
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"service_{service['service_id']}",
                    "title": f"{service['name']} - R$ {service['price']:.2f}"
                }
            })
        
        return {
            "message": message,
            "buttons": buttons
        }
    
    def check_availability(self, message, data):
        """Verifica disponibilidade para uma data específica"""
        try:
            date_str = data.get('date')
            service_id = data.get('service_id')
            
            if not date_str or not service_id:
                return {
                    "message": "Por favor, me informe a data e o serviço desejado.",
                    "buttons": None
                }
            
            # Converte string para data
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Obtém informações do serviço
            success, service = self.db_service.get_service(service_id)
            if not success:
                return {
                    "message": "Serviço não encontrado.",
                    "buttons": None
                }
            
            # Obtém slots disponíveis
            available_slots = self.calendar_service.get_available_slots(
                date_obj, 
                duration_minutes=service['duration_minutes']
            )
            
            if not available_slots:
                return {
                    "message": f"Infelizmente não temos horários disponíveis para {date_str}. Gostaria de tentar outra data?",
                    "buttons": None
                }
            
            # Cria botões com horários disponíveis (máximo 3)
            buttons = []
            for slot in available_slots[:3]:
                buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": f"time_{slot['start'].strftime('%H:%M')}",
                        "title": slot['formatted']
                    }
                })
            
            return {
                "message": f"{message}\n\nHorários disponíveis para {date_str}:",
                "buttons": buttons
            }
        
        except Exception as e:
            print(f"Erro ao verificar disponibilidade: {str(e)}")
            return {
                "message": "Erro ao verificar disponibilidade. Tente novamente.",
                "buttons": None
            }
    
    def create_appointment(self, phone_number, message, data, context):
        """Cria um novo agendamento"""
        try:
            service_id = data.get('service_id')
            date_str = data.get('date')
            time_str = data.get('time')
            client_name = data.get('client_name')
            
            if not all([service_id, date_str, time_str]):
                return {
                    "message": "Informações incompletas para o agendamento. Vamos começar novamente?",
                    "buttons": None
                }
            
            # Cria agendamento no banco de dados
            success, appointment_id = self.db_service.create_appointment(
                phone_number=phone_number,
                service_id=service_id,
                appointment_date=date_str,
                appointment_time=time_str,
                client_name=client_name
            )
            
            if not success:
                return {
                    "message": "Erro ao criar agendamento. Tente novamente.",
                    "buttons": None
                }
            
            # Obtém informações do serviço
            success, service = self.db_service.get_service(service_id)
            
            # Cria evento no Google Calendar
            start_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            end_datetime = start_datetime + timedelta(minutes=service['duration_minutes'])
            
            calendar_success, calendar_event = self.calendar_service.create_appointment(
                summary=f"{service['name']} - {client_name or 'Cliente'}",
                start_time=start_datetime,
                end_time=end_datetime,
                description=f"Cliente: {phone_number}\nServiço: {service['name']}\nPreço: R$ {service['price']:.2f}"
            )
            
            if calendar_success:
                # Salva o ID do evento do Google Calendar no agendamento
                # (Aqui você poderia atualizar o registro no DynamoDB com o event_id)
                pass
            
            # Limpa o contexto da conversa
            context['state'] = self.conversation_states['COMPLETED']
            context['data'] = {}
            
            return {
                "message": f"{message}\n\n✅ Agendamento confirmado!\n\n📅 Data: {date_str}\n🕐 Horário: {time_str}\n💇 Serviço: {service['name']}\n💰 Valor: R$ {service['price']:.2f}\n\nAguardamos você! 😊",
                "buttons": None
            }
        
        except Exception as e:
            print(f"Erro ao criar agendamento: {str(e)}")
            return {
                "message": "Erro ao finalizar agendamento. Tente novamente.",
                "buttons": None
            }
    
    def show_appointments(self, phone_number, message):
        """Mostra agendamentos existentes do cliente"""
        success, appointments = self.db_service.get_appointments_by_phone(phone_number)
        
        if not success or not appointments:
            return {
                "message": "Você não possui agendamentos no momento.",
                "buttons": None
            }
        
        # Filtra apenas agendamentos futuros e ativos
        future_appointments = [
            apt for apt in appointments 
            if apt.get('status') == 'scheduled' and 
            datetime.strptime(apt['appointment_date'], '%Y-%m-%d').date() >= datetime.now().date()
        ]
        
        if not future_appointments:
            return {
                "message": "Você não possui agendamentos futuros.",
                "buttons": None
            }
        
        appointments_text = "Seus agendamentos:\n\n"
        for apt in future_appointments:
            appointments_text += f"📅 {apt['appointment_date']} às {apt['appointment_time']}\n"
            appointments_text += f"💇 {apt['service_name']}\n"
            appointments_text += f"💰 R$ {apt['price']:.2f}\n\n"
        
        return {
            "message": f"{message}\n\n{appointments_text}",
            "buttons": None
        }
    
    def cancel_appointment(self, phone_number, message, data):
        """Cancela um agendamento"""
        # Implementação simplificada - na prática, você precisaria de mais lógica
        # para identificar qual agendamento cancelar
        return {
            "message": "Para cancelar um agendamento, entre em contato conosco pelo telefone (11) 99999-9999.",
            "buttons": None
        }

# Exemplo de uso
if __name__ == "__main__":
    agent = SalonAIAgent()
    
    # Simula uma conversa
    phone = "5511999999999"
    
    # Primeira mensagem
    response = agent.process_message(phone, "Olá, gostaria de agendar um corte")
    print("Resposta 1:", response)
    
    # Segunda mensagem
    response = agent.process_message(phone, "Corte feminino")
    print("Resposta 2:", response)

