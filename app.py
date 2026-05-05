from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")


@app.route("/webhook", methods=["GET"])
def verify():
    hub_mode = request.args.get("hub.mode")
    hub_token = request.args.get("hub.verify_token")
    hub_challenge = request.args.get("hub.challenge")

    if hub_mode == "subscribe" and hub_token == VERIFY_TOKEN:
        print("✅ Webhook verificato")
        return hub_challenge, 200

    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
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
            send_message(user,
                "👋 Benvenuto in Cortonese Carni Srl!\n\n"
                "Sai già cosa prendere o vuoi vedere il nostro catalogo?\n\n"
                "📦 Scrivi: catalogo\n"
                "🧾 Scrivi: ordine"
            )
            sessions[user]["step"] = "menu"
            return "OK", 200

        # 📦 CATALOGO
        if text == "catalogo":
            send_message(user,
                "📦 *CATALOGO PRODOTTI*\n\n"
                "(in arrivo versione completa)\n\n"
                "Se vuoi ordinare scrivi: ordine"
            )
            return "OK", 200

        # 🧾 ORDINE STEP 1
        if text == "ordine":
            send_message(user, "Perfetto 👍\nScrivi Nome e Cognome:")
            sessions[user]["step"] = "nome"
            return "OK", 200

        if step == "nome":
            sessions[user]["nome"] = text
            send_message(user, "Sei un privato o azienda? (scrivi azienda o privato)")
            sessions[user]["step"] = "tipo"
            return "OK", 200

        if step == "tipo":
            sessions[user]["tipo"] = text
            send_message(user, "Scrivi ordine (prodotti + quantità):")
            sessions[user]["step"] = "ordine"
            return "OK", 200

        if step == "ordine":
            sessions[user]["ordine"] = text
            send_message(user, "Scrivi indirizzo di consegna:")
            sessions[user]["step"] = "indirizzo"
            return "OK", 200

        if step == "indirizzo":
            sessions[user]["indirizzo"] = text

            # 📩 CREA ORDINE
            ordine_finale = f"""
🧾 NUOVO ORDINE

Nome: {sessions[user]['nome']}
Tipo: {sessions[user]['tipo']}
Ordine: {sessions[user]['ordine']}
Indirizzo: {sessions[user]['indirizzo']}
"""

            send_email(ordine_finale)

            send_message(user,
                "✅ Ordine ricevuto con successo!\n"
                "Un nostro operatore ti contatterà a breve."
            )

            sessions[user] = {"step": "start"}
            return "OK", 200

    except Exception as e:
        print("Errore:", e)

     return "OK", 200

# 👇 FALLBACK SEMPRE ALLA FINE
else:
    send_message(user,
        "🆘 Non ho capito.\nScrivi 'ordine' o 'catalogo'"
    )
    return "OK", 200

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

    response = requests.post(url, headers=headers, json=payload)
    print("📤 WhatsApp response:", response.text)
