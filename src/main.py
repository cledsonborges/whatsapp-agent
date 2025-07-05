from flask import Flask, request, jsonify
import sys
import os

# Adiciona o diretório src ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whatsapp_webhook import app as webhook_app
from ai_agent import SalonAIAgent
from config.config import WA_BUSINESS_API_TOKEN, WA_BUSINESS_API_PHONE_ID, WA_BUSINESS_API_VERIFY_TOKEN
import requests
import json

# Inicializa o agente de IA
ai_agent = SalonAIAgent()

def send_whatsapp_message(phone_number, message_text):
    """Envia mensagem via WhatsApp Business API"""
    try:
        url = f"https://graph.facebook.com/v18.0/{WA_BUSINESS_API_PHONE_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {WA_BUSINESS_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"Mensagem enviada com sucesso para {phone_number}")
            return True
        else:
            print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Erro ao enviar mensagem WhatsApp: {str(e)}")
        return False

def send_whatsapp_buttons(phone_number, body_text, buttons):
    """Envia mensagem com botões interativos"""
    try:
        url = f"https://graph.facebook.com/v18.0/{WA_BUSINESS_API_PHONE_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {WA_BUSINESS_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": buttons
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"Mensagem com botões enviada com sucesso para {phone_number}")
            return True
        else:
            print(f"Erro ao enviar mensagem com botões: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Erro ao enviar mensagem com botões: {str(e)}")
        return False

# Sobrescreve a função process_message do webhook para usar o agente de IA
def process_message_with_ai(message, value):
    """Processa uma mensagem individual do WhatsApp usando IA"""
    try:
        # Extrai informações da mensagem
        phone_number = message['from']
        message_type = message['type']
        
        if message_type == 'text':
            text_content = message['text']['body']
            print(f"Mensagem de texto de {phone_number}: {text_content}")
            
            # Usa o agente de IA para gerar resposta
            ai_response = ai_agent.process_message(phone_number, text_content)
            
            # Envia resposta
            if ai_response.get('buttons'):
                send_whatsapp_buttons(phone_number, ai_response['message'], ai_response['buttons'])
            else:
                send_whatsapp_message(phone_number, ai_response['message'])
        
        elif message_type == 'interactive':
            # Processa mensagens interativas (botões, listas)
            interactive_data = message['interactive']
            print(f"Mensagem interativa de {phone_number}: {interactive_data}")
            
            # Extrai a seleção do usuário
            if interactive_data['type'] == 'button_reply':
                button_id = interactive_data['button_reply']['id']
                button_title = interactive_data['button_reply']['title']
                
                # Processa a seleção como uma mensagem de texto
                user_selection = f"Selecionei: {button_title}"
                ai_response = ai_agent.process_message(phone_number, user_selection)
                
                # Envia resposta
                if ai_response.get('buttons'):
                    send_whatsapp_buttons(phone_number, ai_response['message'], ai_response['buttons'])
                else:
                    send_whatsapp_message(phone_number, ai_response['message'])
    
    except Exception as e:
        print(f"Erro ao processar mensagem individual: {str(e)}")
        # Envia mensagem de erro para o usuário
        send_whatsapp_message(phone_number, "Desculpe, ocorreu um erro. Tente novamente em alguns instantes.")

# Substitui a função original do webhook
import whatsapp_webhook
whatsapp_webhook.process_message = process_message_with_ai

# Adiciona rota de status
@webhook_app.route('/status', methods=['GET'])
def status():
    """Endpoint para verificar o status do serviço"""
    return jsonify({
        "status": "online",
        "service": "WhatsApp Salon Agent",
        "version": "1.0.0"
    })

# Adiciona rota para testar o agente
@webhook_app.route('/test', methods=['POST'])
def test_agent():
    """Endpoint para testar o agente de IA"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '5511999999999')
        message = data.get('message', 'Olá')
        
        response = ai_agent.process_message(phone_number, message)
        
        return jsonify({
            "success": True,
            "response": response
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🤖 Iniciando Agente de Agendamento para Salão de Beleza...")
    print("📱 WhatsApp Business API configurada")
    print("🧠 Agente de IA inicializado")
    print("📅 Google Calendar integrado")
    print("🗄️ DynamoDB configurado")
    print("\n✅ Serviço pronto para receber mensagens!")
    
    webhook_app.run(host='0.0.0.0', port=5000, debug=True)

