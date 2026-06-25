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

# 📊 GOOGLE SHEETS URL (INCOLLA QUI IL TUO SCRIPT URL)
GOOGLE_SHEET_URL = "INCOLLA_QUI_URL_GOOGLE_SCRIPT"

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


# 📊 SALVA SU GOOGLE SHEETS
def save_order(user):
    try:
        requests.post(GOOGLE_SHEET_URL, json={
            "telefono": user,
            "nome": sessions[user].get("nome"),
            "tipo": sessions[user].get("tipo"),
            "ordine": sessions[user].get("ordine"),
            "data": sessions[user].get("data"),
            "email": sessions[user].get("email"),
            "indirizzo": sessions[user].get("indirizzo")
        })
    except Exception as e:
        print("SHEET ERROR:", repr(e))


# 📧 EMAIL
def send_email(user, nome, tipo, ordine, data, email, indirizzo):
    try:
        url = "https://api.sendgrid.com/v3/mail/send"

        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }

        html_body = f"""
        <html>
        <body>

        <h2>🧾 Nuovo Ordine Ricevuto</h2>

        <p><b>Nome:</b> {nome}</p>
        <p><b>Tipo:</b> {tipo}</p>
        <p><b>Ordine:</b> {ordine}</p>
        <p><b>Data:</b> {data}</p>
        <p><b>Email:</b> {email}</p>
        <p><b>Indirizzo:</b> {indirizzo}</p>
        <p><b>Telefono:</b> {user}</p>

        </body>
        </html>
        """

        payload = {
            "personalizations": [{"to": [{"email": EMAIL_TO}]}],
            "from": {
                "email": "bot@cortonese.com",
                "name": "Cortonese Carni Bot"
            },
            "subject": "Nuovo Ordine",
            "content": [{"type": "text/html", "value": html_body}]
        }

        requests.post(url, json=payload, headers=headers)

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

        if not data:
            return "OK", 200

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
                "📦 Scrivi CATALOGO\n"
                "🧾 Scrivi ORDINE\n"
                "📞 Scrivi AIUTO"
            )
            sessions[user]["step"] = "menu"
            return "OK", 200

        # 📦 CATALOGO
        if text == "catalogo":
            send_message(user, "📦 Ecco il nostro catalogo completo")
            return "OK", 200

        # 🧾 ORDINE
        if text == "ordine":
            send_message(user, "Nome e Cognome:")
            sessions[user]["step"] = "nome"
            return "OK", 200

        # 📞 AIUTO
        if text == "aiuto":
            send_message(
                user,
                "📞 Assistenza:\n"
                "☎️ 0575 XXXXXXX\n"
                "📱 3XX XXXXXXX\n"
                "📧 info@cortonesecarni.it"
            )
            return "OK", 200

        # 🧠 FLUSSO ORDINE
        if step == "nome":
            sessions[user]["nome"] = text
            send_message(user, "Azienda o privato?")
            sessions[user]["step"] = "tipo"
            return "OK", 200

        if step == "tipo":
            sessions[user]["tipo"] = text
            send_message(user, "Scrivi cosa vuoi ordinare")
            sessions[user]["step"] = "ordine"
            return "OK", 200

        if step == "ordine":
            sessions[user]["ordine"] = text
            send_message(user, "Data consegna?")
            sessions[user]["step"] = "data"
            return "OK", 200

        if step == "data":
            sessions[user]["data"] = text
            send_message(user, "Email?")
            sessions[user]["step"] = "email"
            return "OK", 200

        if step == "email":
            sessions[user]["email"] = text
            send_message(user, "Indirizzo?")
            sessions[user]["step"] = "indirizzo"
            return "OK", 200

        if step == "indirizzo":
            sessions[user]["indirizzo"] = text

            # 📊 salva ordine
            save_order(user)

            # 📧 email
            Thread(target=send_email, args=(
                user,
                sessions[user]["nome"],
                sessions[user]["tipo"],
                sessions[user]["ordine"],
                sessions[user]["data"],
                sessions[user]["email"],
                sessions[user]["indirizzo"]
            )).start()

            send_message(user, "✅ Ordine ricevuto!")

            sessions[user] = {"step": "start"}
            return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", repr(e))

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
