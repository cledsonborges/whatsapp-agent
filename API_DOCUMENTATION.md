# Documentação da API - Agente de Agendamento para Salão de Beleza

## Visão Geral

Esta API implementa um agente de IA para WhatsApp que permite aos clientes agendar serviços em um salão de beleza. O sistema integra WhatsApp Business API, Google Calendar e Amazon DynamoDB.

## Endpoints

### 1. Webhook do WhatsApp

#### GET /webhook
**Descrição:** Verifica o webhook do WhatsApp Business API

**Parâmetros de Query:**
- `hub.mode` (string): Modo de verificação
- `hub.verify_token` (string): Token de verificação
- `hub.challenge` (string): Desafio de verificação

**Resposta de Sucesso:**
- **Código:** 200
- **Conteúdo:** String com o challenge

**Resposta de Erro:**
- **Código:** 403
- **Conteúdo:** "Falha na verificação"

#### POST /webhook
**Descrição:** Recebe mensagens do WhatsApp Business API

**Corpo da Requisição:**
```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "from": "5511999999999",
                "type": "text",
                "text": {
                  "body": "Olá, gostaria de agendar um corte"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Resposta de Sucesso:**
- **Código:** 200
- **Conteúdo:** `{"status": "success"}`

### 2. Status do Serviço

#### GET /status
**Descrição:** Verifica o status do serviço

**Resposta:**
```json
{
  "status": "online",
  "service": "WhatsApp Salon Agent",
  "version": "1.0.0"
}
```

### 3. Teste do Agente

#### POST /test
**Descrição:** Testa o agente de IA diretamente

**Corpo da Requisição:**
```json
{
  "phone_number": "5511999999999",
  "message": "Olá, gostaria de agendar um serviço"
}
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "response": {
    "message": "Olá! Como posso ajudá-lo hoje? Aqui estão nossos serviços:",
    "buttons": [
      {
        "type": "reply",
        "reply": {
          "id": "service_corte_feminino",
          "title": "Corte Feminino - R$ 50,00"
        }
      }
    ]
  }
}
```

## Estrutura de Dados

### Serviços Disponíveis

```json
{
  "service_id": "corte_feminino",
  "name": "Corte Feminino",
  "duration_minutes": 60,
  "price": 50.00,
  "description": "Corte de cabelo feminino"
}
```

### Agendamento

```json
{
  "appointment_id": "uuid-string",
  "phone_number": "5511999999999",
  "service_id": "corte_feminino",
  "service_name": "Corte Feminino",
  "appointment_date": "2024-01-15",
  "appointment_time": "14:00",
  "duration_minutes": 60,
  "price": 50.00,
  "status": "scheduled",
  "client_name": "João Silva",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

### Cliente

```json
{
  "phone_number": "5511999999999",
  "name": "João Silva",
  "email": "joao@email.com",
  "preferences": {},
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

### Contexto da Conversa

```json
{
  "phone_number": "5511999999999",
  "context": {
    "state": "service_selection",
    "data": {
      "selected_service": "corte_feminino",
      "selected_date": "2024-01-15"
    }
  },
  "updated_at": "2024-01-01T10:00:00"
}
```

## Estados da Conversa

O agente mantém diferentes estados durante a conversa:

1. **GREETING** - Saudação inicial
2. **SERVICE_SELECTION** - Seleção do serviço
3. **DATE_SELECTION** - Seleção da data
4. **TIME_SELECTION** - Seleção do horário
5. **CONFIRMATION** - Confirmação dos dados
6. **COMPLETED** - Agendamento finalizado
7. **HELP** - Ajuda/suporte

## Fluxo de Agendamento

1. **Cliente inicia conversa** → Estado: GREETING
2. **Agente apresenta serviços** → Estado: SERVICE_SELECTION
3. **Cliente escolhe serviço** → Estado: DATE_SELECTION
4. **Cliente informa data** → Sistema verifica disponibilidade
5. **Agente mostra horários** → Estado: TIME_SELECTION
6. **Cliente escolhe horário** → Estado: CONFIRMATION
7. **Agente confirma dados** → Cliente confirma
8. **Sistema cria agendamento** → Estado: COMPLETED

## Integração com Google Calendar

O sistema integra com o Google Calendar para:
- Verificar disponibilidade de horários
- Criar eventos de agendamento
- Atualizar/cancelar agendamentos

### Configuração Necessária:
- Arquivo `credentials.json` com credenciais do Google Calendar API
- Escopo: `https://www.googleapis.com/auth/calendar`

## Integração com DynamoDB

### Tabelas Utilizadas:

1. **salon_appointments** - Armazena agendamentos
2. **salon_clients** - Armazena dados dos clientes
3. **salon_services** - Armazena serviços disponíveis
4. **salon_conversations** - Armazena contexto das conversas

## Configuração de Ambiente

### Variáveis de Ambiente Necessárias:

```bash
# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_FILE=config/credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=config/token.json

# AWS DynamoDB
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_REGION=us-east-1

# Google Gemini
GEMINI_API_KEY=sua_gemini_api_key

# WhatsApp Business API
WA_BUSINESS_API_TOKEN=seu_whatsapp_token
WA_BUSINESS_API_PHONE_ID=seu_phone_id
WA_BUSINESS_API_VERIFY_TOKEN=seu_verify_token
```

## Instalação e Execução

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Configurar credenciais:**
- Adicionar arquivo `credentials.json` do Google Calendar
- Configurar variáveis de ambiente

3. **Executar o serviço:**
```bash
python src/main.py
```

O serviço será executado na porta 5000.

## Testes

Para executar os testes:

```bash
python -m pytest tests/ -v
```

## Limitações e Considerações

1. **WhatsApp Business API:** Requer aprovação e configuração adequada
2. **Google Calendar:** Necessita autenticação OAuth2
3. **DynamoDB:** Custos baseados em uso
4. **Gemini API:** Limites de rate e custos por requisição

## Suporte

Para suporte técnico ou dúvidas sobre a implementação, consulte:
- Documentação do WhatsApp Business API
- Documentação do Google Calendar API
- Documentação do Amazon DynamoDB
- Documentação do Google Gemini API

