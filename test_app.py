from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

app = Flask(__name__)

# Load your Slack Bot Token
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = 'C08QU90N533'  # e.g., 'C01ABCXYZ'

slack_client = WebClient(token=SLACK_BOT_TOKEN)

@app.route("/read", methods=["GET"])
def read_messages():
    try:
        response = slack_client.conversations_history(channel=CHANNEL_ID, limit=5)
        messages = [msg['text'] for msg in response['messages']]
        return jsonify(messages)
    except SlackApiError as e:
        return jsonify({"error": e.response['error']}), 500

@app.route("/write", methods=["POST"])
def write_message():
    data = request.get_json()
    text = data.get("text", "✅ Hello from your bot!")

    try:
        response = slack_client.chat_postMessage(channel=CHANNEL_ID, text=text)
        return jsonify({"ok": response['ok'], "ts": response['ts']})
    except SlackApiError as e:
        return jsonify({"error": e.response['error']}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8080)