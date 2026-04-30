from flask import Flask, request
import os

app = Flask(__name__)

VERIFY_TOKEN = "michela123"

@app.route('/', methods=['GET'])
def verify():
    hub_mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if hub_mode == "subscribe" and token == VERIFY_TOKEN:
        return str(challenge)

    return "Forbidden", 403


@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    print(data)
    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
