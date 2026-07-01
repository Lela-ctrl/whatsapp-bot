from flask import Flask, request
import requests
import os
from threading import Thread
from supabase import create_client

app = Flask(__name__)

# 🔐 ENV VARIABLES
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
EMAIL_TO = os.environ.get("EMAIL_TO")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🧠 sessioni
sessions = {}

# -----------------------
# SUPABASE
# -----------------------

def cerca_cliente(telefono):
    try:
        res = supabase.table("clienti").select("*").eq("telefono", telefono).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print("SUPABASE ERROR:", repr(e))
        return None


def salva_cliente(telefono, nome, tipo, email, indirizzo):
    try:
        supabase.table("clienti").upsert({
            "telefono": telefono,
            "nome": nome,
            "tipo": tipo,
            "email": email,
            "indirizzo": indirizzo
        }).execute()
    except Exception as e:
        print("SUPABASE SAVE ERROR:", repr(e))


# -----------------------
# WHATSAPP
# -----------------------

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


# -----------------------
# EMAIL
# -----------------------

def send_email(user, nome, tipo, ordine, data, email, indirizzo):
    try:
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }

        html_body = f"""
        <html>
        <body style="font-family: Arial; padding:20px;">
        <h2>🧾 Nuovo Ordine Ricevuto</h2>

        <p><strong>Nome:</strong> {nome}</p>
        <p><strong>Tipo:</strong> {tipo}</p>
        <p><strong>Ordine:</strong><br>{ordine}</p>
        <p><strong>Data:</strong> {data}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Indirizzo:</strong> {indirizzo}</p>
        <p><strong>Telefono:</strong> {user}</p>

        </body>
        </html>
        """

        payload = {
            "personalizations": [{"to": [{"email": EMAIL_TO}]}],
            "from": {
                "email": "ordinibot@gmail.com",
                "name": "Cortonese Carni"
            },
            "subject": "Nuovo Ordine",
            "content": [{"type": "text/html", "value": html_body}]
        }

        requests.post(url, json=payload, headers=headers)

    except Exception as e:
        print("EMAIL ERROR:", repr(e))


# -----------------------
# VERIFY WEBHOOK
# -----------------------

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


# -----------------------
# WEBHOOK PRINCIPALE
# -----------------------

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
        text = message.get("text", {}).get("body", "").lower().strip()

        cliente = cerca_cliente(user)

        # -----------------------
        # PRIMO ACCESSO
        # -----------------------

        if user not in sessions:
            sessions[user] = {"step": "menu"}

            if cliente:
                sessions[user]["cliente"] = cliente

                send_message(
                    user,
                    f"👋 Bentornato {cliente['nome']}!\n\n"
                    "Da qui puoi effettuare i tuoi ordini direttamente online in modo semplice e veloce.\n"
                    "Le richieste vengono prese in carico dal nostro staff entro pochi minuti.\n"
                    "📦 Scrivi CATALOGO per visualizzare i nostri prodotti\n"
                    "🧾 Scrivi ORDINE per effettuare un ordine\n\n"
                    "Per qualsiasi necessità, il nostro team è sempre a vostra disposizione!."
                )
                sessions[user]["step"] = "menu"

            else:
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

        step = sessions[user]["step"]

        # -----------------------
        # AIUTO (INVARIATO)
        # -----------------------

        if text in ["aiuto", "help", "operatore", "assistenza"]:
            send_message(
                user,
                "☎️ Contatta il nostro staff\n\n"
                "📞 0575 XXXXXXX\n"
                "📱 333 XXXXXXX\n\n"
                "🕒 Lun-Ven 08:00 - 13:00 / 14:00 - 18:00"
            )
            return "OK", 200

        # -----------------------
        # CATALOGO
        # -----------------------

        if text == "catalogo":
            send_message(
                user,
                "📦 Ecco il nostro catalogo completo:\n\n"
                "https://drive.google.com/file/d/1wqqPoIYDuPtxxNvFeZJFk8FzmvM7WiQm/view?usp=sharing"
            )
            return "OK", 200

        # -----------------------
        # ORDINE
        # -----------------------

        if text == "ordine":
            send_message(
                user,
                "Perfetto 👍\n\nPer iniziare il tuo ordine, inserisci\nNome e Cognome:"
            )
            sessions[user]["step"] = "nome"
            return "OK", 200

        # -----------------------
        # FLUSSO ORDINE
        # -----------------------

        if step == "nome":
            sessions[user]["nome"] = text
            send_message(
                user,
                "Ordini da parte di un' azienda o un privato?\n\n(scrivere il nome dell'azienda)"
            )
            sessions[user]["step"] = "tipo"
            return "OK", 200

        if step == "tipo":
            sessions[user]["tipo"] = text
            send_message(
                user,
                "Per favore scrivi cosa vuoi ordinare specificando il nome del prodotto e la quantità desiderata\n (in un solo messaggio):"
            )
            sessions[user]["step"] = "ordine"
            return "OK", 200

        if step == "ordine":
            sessions[user]["ordine"] = text
            send_message(user, "Scrivi la data in cui vorresti ricevere il tuo ordine")
            sessions[user]["step"] = "data"
            return "OK", 200

        if step == "data":
            sessions[user]["data"] = text
            send_message(user, "Scrivi il tuo indirizzo email:")
            sessions[user]["step"] = "email"
            return "OK", 200

        if step == "email":
            sessions[user]["email"] = text
            send_message(user, "Scrivi il tuo indirizzo di consegna:")
            sessions[user]["step"] = "indirizzo"
            return "OK", 200

        if step == "indirizzo":

            sessions[user]["indirizzo"] = text

            Thread(target=send_email, args=(
                user,
                sessions[user]["nome"],
                sessions[user]["tipo"],
                sessions[user]["ordine"],
                sessions[user]["data"],
                sessions[user]["email"],
                sessions[user]["indirizzo"]
            )).start()

            salva_cliente(
                user,
                sessions[user]["nome"],
                sessions[user]["tipo"],
                sessions[user]["email"],
                sessions[user]["indirizzo"]
            )

            send_message(
                user,
                "✅ Ordine ricevuto!\n\nUn nostro operatore prenderà in carico la richiesta a breve.\n\nGrazie per aver scelto Cortonese Carni!"
            )

            sessions[user] = {"step": "menu"}

            return "OK", 200

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", repr(e))
        return "OK", 200


# -----------------------
# RUN
# -----------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
