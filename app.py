from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "michela123"

ACCESS_TOKEN = "EAATJWLbzvgABRYP2E96UU8BuUhrBecKOejoxCFE5ldS2zAUZAc2ZCXMAAbwbaJWYbGCeZAjTLi8ufy9fTvwGZCDvMZAIbhnEoF1fKLCn8MojbNKSIjh1Ci16SbdlrSjAZBLJsnVAa2ZARUlmBqibxwmH9fIi9iQhaDUjrtk2IWHFHaA3kB2mnmXMBnrovmxlPZCoU47kgydlnHbLpPalEMTMX2zuBsJvNP6EhAe5323Ibqt35O6d6lSZBI4LwJ6NtVXH5oZBj77d5iLw6Y0aePaqY7uBMZA"
PHONE_NUMBER_ID = "1080578401810270"



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
    print("🔥 POST ARRIVATO 🔥")

    data = request.get_json()
    print("📩 EVENTO RICEVUTO:")
    print(data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = message["from"]
        text = message["text"]["body"]

        print(f"📱 Messaggio da {from_number}: {text}")

        send_message(from_number, f"Hai scritto: {text}")

    except Exception as e:
        print("⚠️ Errore parsing:", e)

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
    print("📤 Risposta inviata:", response.text)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
