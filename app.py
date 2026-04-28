from flask import Flask, request
import os

app = Flask(__name__)

VERIFY_TOKEN = "michela123"

@app.route('/', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token == VERIFY_TOKEN:
        return challenge
    return "Errore"

@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    print(data)
    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
