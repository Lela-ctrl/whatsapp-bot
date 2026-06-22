from flask import Flask, request
import requests
import os
from threading import Thread

app = Flask(__name__)

# 🔐 ENV VARIABLES (Render)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

EMAIL_TO = os.environ.get("EMAIL_TO")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

# 🧠 sessioni utenti
sessions = {}


# 📩 WHATSAPP SEND
# 📩 WHATSAPP SEND
def send_message(to, text):
    try:
        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload
        )

        print("WHATSAPP STATUS:", response.status_code)
        print("WHATSAPP RESPONSE:", response.text)

    except Exception as e:
        print("WHATSAPP ERROR:", repr(e))


# 📧 EMAIL (SENDGRID STABILE)
def send_email(user, nome, tipo, ordine, data, email, indirizzo):
    try:
        print("📧 INVIO EMAIL SENDGRID...")

        url = "https://api.sendgrid.com/v3/mail/send"

        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color:#f6f6f6; padding:20px;">

            <div style="max-width:600px; margin:auto; background:white; padding:20px; border-radius:10px;">

                <h2 style="color:#2c3e50;">🧾 Nuovo Ordine Ricevuto</h2>

                <hr>

                <p><strong>Nome:</strong> {nome}</p>
                <p><strong>Tipo cliente:</strong> {tipo}</p>
                <p><strong>Ordine:</strong><br>{ordine}</p>
                <p><strong>Data consegna:</strong> {data}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Indirizzo:</strong> {indirizzo}</p>
                <p><strong>Telefono:</strong> {user}</p>

                <hr>

                <p style="font-size:12px; color:#888;">
                    Sistema automatico WhatsApp - Cortonese Carni Srl
                </p>

            </div>

        </body>
        </html>
        """

        payload = {
            "personalizations": [
                {
                    "to": [{"email": EMAIL_TO}]
                }
            ],
            "from": {
                "email": "ordinibot@gmail.com",
                "name": "Cortonese Carni Ordini"
            },
            "subject": "🧾 Nuovo ordine ricevuto - Cortonese Carni",
            "content": [
                {
                    "type": "text/html",
                    "value": html_body
                }
            ]
        }

        response = requests.post(url, json=payload, headers=headers)

        print("📩 STATUS:", response.status_code)
        print("📩 RESPONSE:", response.text)

        if response.status_code in [200, 202]:
            print("✅ EMAIL INVIATA")
        else:
            print("❌ ERRORE INVIO EMAIL")

    except Exception as e:
        print("EMAIL ERROR:", repr(e))


# 🔐 VERIFY WEBHOOK
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Forbidden", 403


# 📩 WEBHOOK PRINCIPALE
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    print("\n\n🔥 FULL PAYLOAD:")
    print(data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        print("\n🔥 VALUE KEYS:", value.keys())

        if "messages" not in value:
            print("⚠️ Nessun messaggio (solo status o altro)")
            return "OK", 200

        message = value["messages"][0]
        print("📩 MESSAGE:", message)

        return "OK", 200

    except Exception as e:
        print("❌ ERROR:", repr(e))

    return "OK", 200
    except Exception as e:
        print("WEBHOOK ERROR:", repr(e))

    return "OK", 200


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
