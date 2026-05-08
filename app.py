from flask import Flask, request
import requests
import os
import smtplib
from email.mime.text import MIMEText
from threading import Thread

app = Flask(__name__)

# 🔐 ENV VARIABLES
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO = os.environ.get("EMAIL_TO")

sessions = {}


# 📩 WHATSAPP MESSAGE
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
        print("❌ WHATSAPP ERROR:", repr(e))


# 📧 FALLBACK
def fallback(order_text):
    with open("ordini_fallback.txt", "a", encoding="utf-8") as f:
        f.write(order_text + "\n\n")


# 📧 EMAIL
def send_email(order_text):
    try:
        msg = MIMEText(order_text, _charset="utf-8")
        msg["Subject"] = "Nuovo ordine WhatsApp"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)

        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(EMAIL_USER, EMAIL_PASS)

        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())

        server.quit()

        print("✅ EMAIL INVIATA")

    except Exception as e:
        print("❌ EMAIL ERROR:", repr(e))
        fallback(order_text)


# 🔐 VERIFY
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Forbidden", 403


# 📩 WEBHOOK
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

        # 👋 MESSAGGIO PRINCIPALE BRAND
        if step == "start":
            send_message(user,
                "👋 *Benvenuto in Cortonese Carni Srl!*\n\n"
                " Da qui puoi effettuare i tuoi ordini direttamente online in modo semplice e veloce.\n\n"
                "🧾 Scrivi *ORDINE* per iniziare\n"
                "📦 Scrivi *CATALOGO* per vedere i prodotti"
                "Per qualsiasi necessità, il nostro team è sempre a vostra disposizione"
            )
            sessions[user]["step"] = "menu"
            return "OK", 200

        # 📦 CATALOGO
        if text == "catalogo":
            send_message(user,
                "📦 *CATALOGO PRODOTTI*\n\n"
                "🥩 Carne bovina\n🐖 Carne suina\n🍗 Pollame\n\n"
                "👉 Scrivi *ORDINE* per acquistare"
            )
            return "OK", 200

        # 🧾 ORDINE START
        if text == "ordine":
            send_message(user, "Perfetto 👍\nPer iniziare il tuo ordine, inserisci\nNome e Cognome:")
            sessions[user]["step"] = "nome"
            return "OK", 200

        # 🧾 NOME
        if step == "nome":
            sessions[user]["nome"] = text
            send_message(user, "Ordini da parte di un'azienda o un privato?\n(scrivere il nome dell'azienda)")
            sessions[user]["step"] = "tipo"
            return "OK", 200

        # 🧾 TIPO
        if step == "tipo":
            sessions[user]["tipo"] = text
            send_message(user, "Perfavore scrivi cosa vuoi ordinare con nome e quantità dei prodotti!")
            sessions[user]["step"] = "ordine"
            return "OK", 200

        # 🧾 ORDINE
        if step == "ordine":
            sessions[user]["ordine"] = text
            send_message(user, "📅 Che giorno ti serve la consegna?")
            sessions[user]["step"] = "data"
            return "OK", 200

        # 📅 DATA
        if step == "data":
            sessions[user]["data"] = text
            send_message(user, "Perfavore scrivi il tuo indirizzo di consegna")
            sessions[user]["step"] = "indirizzo"
            return "OK", 200

        # 🧾 FINALE
        if step == "indirizzo":
    try:
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
        print("🚀 AVVIO THREAD EMAIL")
        Thread(target=send_email, args=(ordine_finale,)).start()
        print("🚀 THREAD AVVIATO")

        send_message(user,
            "✅ Ordine ricevuto!\nTi contatteremo a breve.\nGrazie per aver scelto Cortonese Carni"
        )

        sessions[user] = {"step": "start"}

        return "OK", 200

    except Exception as e:
        print("❌ ERRORE STEP FINALE:", repr(e))

        send_message(user,
            "⚠️ Errore tecnico, contatta supporto."
        )

        return "OK", 200
        
    except Exception as e:
        print("❌ ERROR:", repr(e))

        try:
            send_message(user,
                "⚠️ Errore tecnico.\n" 
                "Per assistenza immediata puoi contattare direttamente un nostro operatore:\n" 
                "📞 Emanuele +39 328 931 8272"
            )
        except:
            pass

        return "OK", 200

    return "OK", 200


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
