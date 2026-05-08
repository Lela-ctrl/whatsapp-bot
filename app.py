from flask import Flask, request
import requests
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# 🔐 ENV VARIABLES (Render)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO = os.environ.get("EMAIL_TO")

# 🧠 sessioni utenti
sessions = {}


# 📩 INVIO WHATSAPP
def send_message(to, text):
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


# 📧 INVIO EMAIL ORDINE
def send_email(order_text):
    try:
        msg = MIMEText(order_text)
        msg["Subject"] = "Nuovo ordine WhatsApp"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)

        server.sendmail(
            EMAIL_USER,
            EMAIL_TO,
            msg.as_string()
        )

        server.quit()

        print("✅ EMAIL INVIATA")

    except Exception as e:
        print("❌ ERRORE EMAIL:", e)


# 🔐 VERIFY WEBHOOK (GET)
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Forbidden", 403


# 📩 WEBHOOK PRINCIPALE (POST)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        # ❌ ignoriamo status
        if "messages" not in value:
            return "OK", 200

        message = value["messages"][0]
        user = message["from"]
        text = message.get("text", {}).get("body", "").lower()

        # inizializza sessione
        if user not in sessions:
            sessions[user] = {"step": "start"}

        step = sessions[user]["step"]

        # 👋 START
        if step == "start":
            send_message(user,
                "👋 Benvenuto in Cortonese Carni Srl!\n\n"
                "Da qui puoi effettuare i tuoi ordini direttamente online in modo semplice e veloce.\n"
                "Le richieste vengono prese in carico dal nostro staff entro pochi minuti.\n"
                "📦 Scrivi CATALOGO per visualizzare i nostri prodotti\n"
                "🧾 Scrivi ORDINE per effettuare un ordine\n"
                "Per qualsiasi necessità, il nostro team è sempre a disposizione."         
            )
            sessions[user]["step"] = "menu"
            return "OK", 200

        # 📦 CATALOGO
        if text == "catalogo":
            send_message(user,
                "📦 CATALOGO PRODOTTI\n\n"
                "🥩 Carne bovina\n"
                "🐖 Carne suina\n"
                "🍗 Pollame\n\n"
                "👉 Scrivi 'ordine' per acquistare"
            )
            return "OK", 200

        # 🧾 ORDINE - STEP 1
        if text == "ordine":
            send_message(user, "Perfetto 👍\nPer iniziare il tuo ordine, inserisci\n Nome e Cognome:")
            sessions[user]["step"] = "nome"
            return "OK", 200

        # 🧾 STEP 2
        if step == "nome":
            sessions[user]["nome"] = text
            send_message(user, "Ordini da parte di un'azienda o un privato?\n(scrivere il nome dell'azienda)")
            sessions[user]["step"] = "tipo"
            return "OK", 200

        # 🧾 STEP 3
        if step == "tipo":
            sessions[user]["tipo"] = text
            send_message(user, "Perfavore scrivi cosa vuoi ordinare con nome del prodotto e quantità desiderata:")
            sessions[user]["step"] = "ordine"
            return "OK", 200

        # 🧾 STEP 4
        if step == "ordine":
            sessions[user]["ordine"] = text
            send_message(user, "Scrivi il tuo indirizzo di consegna:")
            sessions[user]["step"] = "indirizzo"
            return "OK", 200

        # 🧾 STEP 5 - FINALE
        if step == "indirizzo":
            sessions[user]["indirizzo"] = text

            ordine_finale = f"""
🧾 NUOVO ORDINE

Nome: {sessions[user]['nome']}
Tipo: {sessions[user]['tipo']}
Ordine: {sessions[user]['ordine']}
Indirizzo: {sessions[user]['indirizzo']}
Telefono: {user}
"""

            send_email(ordine_finale)

            send_message(user,
                "✅ Ordine ricevuto con successo.|n"
                "La richiesta è stata inoltrata al nostro staff e verrà presa in carico entro pochi minuti."
                "Grazie per aver scelto Cortonese Carni Srl.\n"
            )

            sessions[user] = {"step": "start"}
            return "OK", 200

        # 🆘 FALLBACK UMANO
        send_message(user,
            "🆘 Non sono riuscito a comprendere correttamente la richiesta.\n"
            "Per assistenza immediata puoi contattare direttamente un nostro operatore:"
            "📞 +39 XXX XXX XXXX"
        )

        return "OK", 200

    except Exception as e:
        print("ERROR:", e)

    return "OK", 200


# 🚀 RUN (solo locale, Render usa gunicorn)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
