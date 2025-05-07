import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

oai = OpenAI(api_key=OPENAI_API_KEY)
slack_client = WebClient(token=SLACK_BOT_TOKEN)

send_dm_function = {
    "type": "function",
    "function": {
        "name": "send_slack_dm",
        "description": "Send a direct message to a Slack user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Slack user ID to message"
                },
                "message": {
                    "type": "string",
                    "description": "Message content"
                }
            },
            "required": ["user_id", "message"]
        }
    }
}

@app.route("/slack/events", methods=["POST"])
def slack_events():
    logging.debug("📩 HEADERS: %s", dict(request.headers))
    logging.debug("📩 BODY: %s", request.get_data(as_text=True))

    data = request.get_json(force=True, silent=True)
    logging.debug("📩 PARSED JSON: %s", data)

    if data and data.get("type") == "url_verification":
        logging.debug("✅ Responding to challenge")
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})
    if event.get("type") == "message" and "bot_id" not in event:
        user_id = event.get("user")
        channel_id = event.get("channel")
        text = event.get("text", "")
        analyze_and_act(user_id, text, channel_id)

    return "", 200

@app.route("/debug", methods=["GET"])
def debug():
    logging.debug("🛠️ Debug endpoint hit.")
    return "Debug log printed to console.", 200

def analyze_and_act(user_id, text, channel_id):
    prompt = f"""
    You are a Slack assistant. If the message below is about direct deposit, early pay, or getting paid.
    1. send a direct message to the user. Send only the original message, not a response.
    Message: \"{text}\"
    """

    try:
        response = oai.chat.completions.create(
            model="gpt-4-1106-preview",
            tools=[send_dm_function],
            tool_choice="auto",
            messages=[
                {"role": "system", "content": "You monitor Slack messages and act on relevant ones."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        tool_call = response.choices[0].message.tool_calls[0]
        if tool_call:
            args = json.loads(tool_call.function.arguments)
            send_slack_dm(user_id, args["message"])
    except Exception as e:
        logging.error("Error in analyze_and_act: %s", e)

def send_slack_dm(user_id, message):
    try:
        logging.debug(f"🔍 Trying to DM user_id: {user_id}")
        try:
            user_info = slack_client.users_info(user=user_id)
            logging.debug("👤 Found user:", user_info["user"]["name"])
        except SlackApiError as e:
            logging.error("⚠️ users_info failed:", e.response["error"])
        dm = slack_client.conversations_open(users=user_id)
        channel_id = dm["channel"]["id"]
        slack_client.chat_postMessage(channel=channel_id, text=message)
    except SlackApiError as e:
        logging.error("Slack API error: %s", e.response['error'])

if __name__ == "__main__":
    app.run(debug=True, port=8080)