import requests

TOKEN = "8632831814:AAHU8LIDCP2iI6ZZ03j_F3i7y21XVunbTIM"
CHAT_ID = 8752000601  # sem aspas

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": "🔥 TESTE DIRETO"
})

print(response.status_code)
print(response.json())