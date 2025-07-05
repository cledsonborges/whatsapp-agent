from flask import Flask, request, jsonify
import requests
import json
import os
from config.config import WA_BUSINESS_API_TOKEN, WA_BUSINESS_API_PHONE_ID, WA_BUSINESS_API_VERIFY_TOKEN

app = Flask(__name__)

# Webhook para verificação do WhatsApp
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verifica o webhook do WhatsApp Business API"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == WA_BUSINESS_API_VERIFY_TOKEN:
        print("Webhook verificado com sucesso!")
        return challenge
    else:
        return "Falha na verificação", 403

# Webhook para receber mensagens do WhatsApp
@app.route('/webhook', methods=['POST'])
def receive_message():
    """Recebe mensagens do WhatsApp Business API"""
    try:
        data = request.get_json()
        print(f"Dados recebidos: {json.dumps(data, indent=2)}")
        
        # Verifica se há mensagens na requisição
        if 'entry' in data:
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if 'value' in change and 'messages' in change['value']:
                            messages = change['value']['messages']
                            for message in messages:
                                # Processa cada mensagem
                                process_message(message, change['value'])
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        print(f"Erro ao processar mensagem: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def process_message(message, value):
    """Processa uma mensagem individual do WhatsApp"""
    try:
        # Extrai informações da mensagem
        phone_number = message['from']
        message_type = message['type']
        
        if message_type == 'text':
            text_content = message['text']['body']
            print(f"Mensagem de texto de {phone_number}: {text_content}")
            
            # Aqui será integrada a lógica do agente de IA
            response_text = generate_ai_response(text_content, phone_number)
            
            # Envia resposta
            send_whatsapp_message(phone_number, response_text)
        
        elif message_type == 'interactive':
            # Processa mensagens interativas (botões, listas)
            interactive_data = message['interactive']
            print(f"Mensagem interativa de {phone_number}: {interactive_data}")
            
            # Processa a resposta interativa
            response_text = process_interactive_response(interactive_data, phone_number)
            send_whatsapp_message(phone_number, response_text)
    
    except Exception as e:
        print(f"Erro ao processar mensagem individual: {str(e)}")

def generate_ai_response(user_message, phone_number):
    """Gera resposta usando IA (placeholder - será implementado na próxima fase)"""
    # Por enquanto, uma resposta simples
    return f"Olá! Recebi sua mensagem: '{user_message}'. Em breve nosso agente de IA estará funcionando completamente!"

def process_interactive_response(interactive_data, phone_number):
    """Processa respostas de elementos interativos"""
    # Implementar lógica para botões e listas
    return "Obrigado pela sua seleção! Em breve processaremos sua escolha."

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
        else:
            print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"Erro ao enviar mensagem WhatsApp: {str(e)}")

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
        else:
            print(f"Erro ao enviar mensagem com botões: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"Erro ao enviar mensagem com botões: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

