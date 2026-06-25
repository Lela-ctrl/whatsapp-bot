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

# 📊 GOOGLE SHEETS WEB APP URL (INCOLLA QUI)
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

    except Exception as e:
        print("EMAIL ERROR:", repr(e))


# 📊 GOOGLE SHEETS SAVE
def save_to_sheet(user):
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
                "Da qui puoi effettuare i tuoi ordini direttamente online in modo semplice e veloce.\n"
                "Le richieste vengono prese in carico dal nostro staff entro pochi minuti.\n"
                "📦 Scrivi CATALOGO per visualizzare i nostri prodotti\n"
                "🧾 Scrivi ORDINE per effettuare un ordine\n\n"
                "Per qualsiasi necessità, il nostro team è sempre a vostra disposizione!."
            )
            sessions[user]["step"] = "menu"
            return "OK", 200

        # 📦 CATALOGO
        if text == "catalogo":
            send_message(
                user,
                "📦 Ecco il nostro catalogo completo:"
            )
            return "OK", 200

        # 🧾 ORDINE
        if text == "ordine":
            send_message(user, "Perfetto 👍\n\nPer iniziare il tuo ordine, inserisci\nNome e Cognome:")
            sessions[user]["step"] = "nome"
            return "OK", 200

        # 📞 AIUTO
        if text == "aiuto":
            send_message(
                user,
                "📞 Hai bisogno di assistenza?\n\n"
                "Puoi contattare il nostro staff:\n"
                "☎️ Ufficio: 0575 XXXXXXX\n"
                "📱 WhatsApp: 3XX XXXXXXX\n"
                "📧 Email: info@cortonesecarni.it\n\n"
                "Saremo felici di aiutarti!"
            )
            return "OK", 200

        # 🧾 NOME
        if step == "nome":
            sessions[user]["nome"] = text
            send_message(user, "Ordini da parte di un' azienda o un privato?\n\n(scrivere il nome dell'azienda)")
            sessions[user]["step"] = "tipo"
            return "OK", 200

        # 🧾 TIPO
        if step == "tipo":
            sessions[user]["tipo"] = text
            send_message(user, "Per favore scrivi cosa vuoi ordinare specificando il nome del prodotto e la quantità desiderata\n (in un solo messaggio):")
            sessions[user]["step"] = "ordine"
            return "OK", 200

        # 🧾 ORDINE
        if step == "ordine":
            sessions[user]["ordine"] = text
            send_message(user, "Scrivi la data in cui vorresti ricevere il tuo ordine")
            sessions[user]["step"] = "data"
            return "OK", 200

        # 📅 DATA
        if step == "data":
            sessions[user]["data"] = text
            send_message(user, "Scrivi il tuo indirizzo email:")
            sessions[user]["step"] = "email"
            return "OK", 200

        # 📧 EMAIL
        if step == "email":
            sessions[user]["email"] = text
            send_message(user, "Scrivi il tuo indirizzo di consegna:")
            sessions[user]["step"] = "indirizzo"
            return "OK", 200

        # 📦 FINALE
        if step == "indirizzo":
            sessions[user]["indirizzo"] = text

            print("📦 ORDINE COMPLETO")

            # 📊 SALVA SU GOOGLE SHEETS
            save_to_sheet(user)

            Thread(target=send_email, args=(
                user,
                sessions[user]["nome"],
                sessions[user]["tipo"],
                sessions[user]["ordine"],
                sessions[user]["data"],
                sessions[user]["email"],
                sessions[user]["indirizzo"]
            )).start()

            send_message(
                user,
                "✅ Ordine ricevuto!\n\nUn nostro operatore prenderà in carico la richiesta a breve.\n\nGrazie per aver scelto Cortonese Carni!"
            )

            sessions[user] = {"step": "start"}
            return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", repr(e))

    return "OK", 200


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
