import os

# Google Calendar API
GOOGLE_CALENDAR_CREDENTIALS_FILE = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_FILE', 'config/credentials.json')
GOOGLE_CALENDAR_TOKEN_FILE = os.getenv('GOOGLE_CALENDAR_TOKEN_FILE', 'config/token.json')

# AWS DynamoDB
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1') # Pode ser alterado para a região desejada

# Google Gemini LLM
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# WhatsApp Business API
WA_BUSINESS_API_TOKEN = os.getenv('WA_BUSINESS_API_TOKEN')
WA_BUSINESS_API_PHONE_ID = os.getenv('WA_BUSINESS_API_PHONE_ID')
WA_BUSINESS_API_VERIFY_TOKEN = os.getenv('WA_BUSINESS_API_VERIFY_TOKEN', 'YOUR_VERIFY_TOKEN') # Token para verificação do webhook


