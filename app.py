from flask import Flask, request
import requests
import os
from threading import Thread
from email.mime.text import MIMEText

app = Flask(__name__)

# 🔐 ENV VARIABLES (Render)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

EMAIL_TO = os.environ.get("EMAIL_TO")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

# 🧠 sessioni utenti
sessions = {}


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

        requests.post(url, headers=headers, json=payload)

    except Exception as e:
        print("WHATSAPP ERROR:", repr(e))


# 📧 EMAIL (RESEND API)
def send_email(order_text):
    try:
        print("📧 INVIO EMAIL VIA RESEND...")

        url = "https://api.resend.com/emails"

        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "from": "Ordini <onboarding@resend.dev>",
            "to": ["cortonesecarnisrl@gmail.com"],
            "subject": "Nuovo ordine WhatsApp",
            "text": order_text
        }

        response = requests.post(url, json=payload, headers=headers)

        print("📩 STATUS:", response.status_code)
        print("📩 RESPONSE:", response.text)

        if response.status_code == 200:
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
    try:
        data = request.get_json()

        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return "OK", 200

        message = value["messages"][0]
        user = message["from"]
        text = message.get("text", {}).get("body", "").lower()

        if user not in sessions:
            sessions[user] = {"step": "start"}

        step = sessions[user]["step"]

        # 👋 START
        if step == "start":
            send_message(
                user,
                "👋 Benvenuto in Cortonese Carni Srl!\n\n"
                "Scrivi ORDINE per iniziare\n"
                "Scrivi CATALOGO per vedere prodotti"
            )
            sessions[user]["step"] = "menu"
            return "OK", 200

        # 📦 CATALOGO
        if text == "catalogo":
            send_message(
                user,
                "📦 CATALOGO\n🥩 Carne bovina\n🐖 Carne suina\n🍗 Pollame"
            )
            return "OK", 200

        # 🧾 ORDINE
        if text == "ordine":
            send_message(user, "Nome e Cognome?")
            sessions[user]["step"] = "nome"
            return "OK", 200

        # 🧾 NOME
        if step == "nome":
            sessions[user]["nome"] = text
            send_message(user, "Privato o azienda?")
            sessions[user]["step"] = "tipo"
            return "OK", 200

        # 🧾 TIPO
        if step == "tipo":
            sessions[user]["tipo"] = text
            send_message(user, "Cosa vuoi ordinare?")
            sessions[user]["step"] = "ordine"
            return "OK", 200

        # 🧾 ORDINE
        if step == "ordine":
            sessions[user]["ordine"] = text
            send_message(user, "📅 Giorno consegna?")
            sessions[user]["step"] = "data"
            return "OK", 200

        # 📅 DATA
        if step == "data":
            sessions[user]["data"] = text
            send_message(user, "Indirizzo di consegna?")
            sessions[user]["step"] = "indirizzo"
            return "OK", 200

        # 📦 FINALE
        if step == "indirizzo":
            sessions[user]["indirizzo"] = text

            ordine_finale = f"""
🧾 NUOVO ORDINE

Nome: {sessions[user]['nome']}
Tipo: {sessions[user]['tipo']}
Ordine: {sessions[user]['ordine']}
Data consegna: {sessions[user]['data']}
Indirizzo: {sessions[user]['indirizzo']}
Telefono: {user}
"""

            print("📦 ORDINE COMPLETO")
            print(ordine_finale)

            # 🚀 EMAIL ASINCRONA
            Thread(target=send_email, args=(ordine_finale,)).start()

            send_message(user, "✅ Ordine ricevuto! Ti contatteremo a breve.")

            sessions[user] = {"step": "start"}

            return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", repr(e))

    return "OK", 200


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
