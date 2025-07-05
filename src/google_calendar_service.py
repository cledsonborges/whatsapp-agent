import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config.config import GOOGLE_CALENDAR_CREDENTIALS_FILE, GOOGLE_CALENDAR_TOKEN_FILE

# Escopos necessários para ler e escrever no Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService:
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Autentica com a Google Calendar API"""
        creds = None
        
        # O arquivo token.json armazena os tokens de acesso e atualização do usuário.
        if os.path.exists(GOOGLE_CALENDAR_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(GOOGLE_CALENDAR_TOKEN_FILE, SCOPES)
        
        # Se não há credenciais válidas disponíveis, permite ao usuário fazer login.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_CALENDAR_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Salva as credenciais para a próxima execução
            with open(GOOGLE_CALENDAR_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            print("Autenticação com Google Calendar realizada com sucesso!")
        except HttpError as error:
            print(f"Erro ao autenticar com Google Calendar: {error}")
    
    def get_calendar_list(self):
        """Obtém a lista de calendários disponíveis"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            print("Calendários disponíveis:")
            for calendar in calendars:
                print(f"- {calendar['summary']} (ID: {calendar['id']})")
            
            return calendars
        except HttpError as error:
            print(f"Erro ao obter lista de calendários: {error}")
            return []
    
    def check_availability(self, start_time, end_time, calendar_id='primary'):
        """Verifica disponibilidade em um período específico"""
        try:
            # Converte strings para objetos datetime se necessário
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            # Busca eventos no período especificado
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Se não há eventos, o horário está disponível
            if not events:
                return True, "Horário disponível"
            else:
                return False, f"Horário ocupado. {len(events)} evento(s) encontrado(s)"
        
        except HttpError as error:
            print(f"Erro ao verificar disponibilidade: {error}")
            return False, f"Erro ao verificar disponibilidade: {error}"
    
    def get_available_slots(self, date, duration_minutes=60, start_hour=9, end_hour=18, calendar_id='primary'):
        """Obtém slots disponíveis em uma data específica"""
        try:
            # Define o início e fim do dia
            start_of_day = datetime.combine(date, datetime.min.time().replace(hour=start_hour))
            end_of_day = datetime.combine(date, datetime.min.time().replace(hour=end_hour))
            
            # Busca todos os eventos do dia
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_of_day.isoformat() + 'Z',
                timeMax=end_of_day.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Cria lista de horários ocupados
            busy_times = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Converte para datetime se necessário
                if 'T' in start:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    busy_times.append((start_dt, end_dt))
            
            # Gera slots disponíveis
            available_slots = []
            current_time = start_of_day
            slot_duration = timedelta(minutes=duration_minutes)
            
            while current_time + slot_duration <= end_of_day:
                slot_end = current_time + slot_duration
                
                # Verifica se o slot não conflita com eventos existentes
                is_available = True
                for busy_start, busy_end in busy_times:
                    # Remove informações de timezone para comparação
                    busy_start = busy_start.replace(tzinfo=None)
                    busy_end = busy_end.replace(tzinfo=None)
                    
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        'start': current_time,
                        'end': slot_end,
                        'formatted': f"{current_time.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                    })
                
                # Avança para o próximo slot (a cada 30 minutos)
                current_time += timedelta(minutes=30)
            
            return available_slots
        
        except HttpError as error:
            print(f"Erro ao obter slots disponíveis: {error}")
            return []
    
    def create_appointment(self, summary, start_time, end_time, description="", calendar_id='primary'):
        """Cria um novo agendamento no calendário"""
        try:
            # Converte strings para objetos datetime se necessário
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 dia antes
                        {'method': 'popup', 'minutes': 60},       # 1 hora antes
                    ],
                },
            }
            
            event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
            print(f"Evento criado: {event.get('htmlLink')}")
            
            return True, event
        
        except HttpError as error:
            print(f"Erro ao criar agendamento: {error}")
            return False, str(error)
    
    def update_appointment(self, event_id, summary=None, start_time=None, end_time=None, description=None, calendar_id='primary'):
        """Atualiza um agendamento existente"""
        try:
            # Obtém o evento atual
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            
            # Atualiza os campos fornecidos
            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                event['start']['dateTime'] = start_time.isoformat()
            if end_time:
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time)
                event['end']['dateTime'] = end_time.isoformat()
            
            updated_event = self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
            print(f"Evento atualizado: {updated_event.get('htmlLink')}")
            
            return True, updated_event
        
        except HttpError as error:
            print(f"Erro ao atualizar agendamento: {error}")
            return False, str(error)
    
    def delete_appointment(self, event_id, calendar_id='primary'):
        """Cancela um agendamento"""
        try:
            self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            print(f"Evento {event_id} cancelado com sucesso")
            
            return True, "Agendamento cancelado com sucesso"
        
        except HttpError as error:
            print(f"Erro ao cancelar agendamento: {error}")
            return False, str(error)

# Exemplo de uso
if __name__ == "__main__":
    calendar_service = GoogleCalendarService()
    
    # Testa a obtenção de calendários
    calendars = calendar_service.get_calendar_list()
    
    # Testa verificação de disponibilidade
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    tomorrow_11am = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
    
    is_available, message = calendar_service.check_availability(tomorrow_10am, tomorrow_11am)
    print(f"Disponibilidade para amanhã 10h-11h: {is_available} - {message}")
    
    # Testa obtenção de slots disponíveis
    available_slots = calendar_service.get_available_slots(tomorrow.date())
    print(f"Slots disponíveis para amanhã: {len(available_slots)}")
    for slot in available_slots[:5]:  # Mostra apenas os primeiros 5
        print(f"  - {slot['formatted']}")

