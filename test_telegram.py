import requests
import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

message = "✅ Teste do bot funcionando!"

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

response = requests.post(url, params=params)
print(response.text)
