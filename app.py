from flask import Flask, request
import os

app = Flask(__name__)

# Token (serve solo per coerenza, ma non lo blocchiamo più)
VERIFY_TOKEN = "michela123"

# 🔹 Verifica webhook (semplificata al massimo)
@app.route('/', methods=['GET'])
def verify():
    challenge = request.args.get("hub.challenge")
    return str(challenge)

# 🔹 Ricezione messaggi
@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    print(data)
    return "ok", 200

# 🔹 Avvio server (compatibile Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
