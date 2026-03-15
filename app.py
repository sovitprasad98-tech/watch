# Vercel entrypoint
from flask import Flask, request, jsonify
import json, asyncio, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from telegram import Update
from main import build_app, BOT_TOKEN
import requests as req

app = Flask(__name__)

async def process_update(update_data):
    application = build_app()
    await application.initialize()
    update = Update.de_json(update_data, application.bot)
    await application.process_update(update)
    await application.shutdown()

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "bot": "@watch_ads_sovitx_bot"})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_data = request.get_json(force=True)
        asyncio.run(process_update(update_data))
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"ok": True})

@app.route("/set-webhook", methods=["GET"])
def set_webhook():
    host = request.host
    url  = f"https://{host}/webhook"
    r    = req.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": url, "allowed_updates": ["message", "callback_query"]},
        timeout=8
    )
    return jsonify(r.json())

if __name__ == "__main__":
    app.run(debug=False)
      
