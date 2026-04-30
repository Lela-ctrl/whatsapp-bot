from flask import Flask, request
import os

app = Flask(__name__)

VERIFY_TOKEN = "michela123"


# 🔹 Verifica + messaggi nello stesso endpoint
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():

    # 🔹 VERIFICA META (GET)
    if request.method == 'GET':
        hub_mode = request.args.get("hub.mode")
        hub_token = request.args.get("hub.verify_token")
        hub_challenge = request.args.get("hub.challenge")

        if hub_mode == "subscribe" and hub_token == VERIFY_TOKEN:
            return hub_challenge, 200

        return "Verification failed", 403


    # 🔹 MESSAGGI (POST)
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        return "ok", 200


# 🔹 Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
