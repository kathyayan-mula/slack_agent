import logging
import sys
from collections import deque
from time import time

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

# Add this line to define processed_events
processed_events = deque(maxlen=1000)  # Keep track of last 1000 events

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

def get_channel_id_by_name(channel_name):
    try:
        # Fetch all channels (public and private)
        result = slack_client.conversations_list(types="public_channel,private_channel")
        for channel in result["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]
        logging.error(f"Channel '{channel_name}' not found.")
        return None
    except SlackApiError as e:
        logging.error("Slack API error: %s", e.response['error'])
        return None

post_to_channel_function = {
    "type": "function",
    "function": {
        "name": "post_to_slack_channel",
        "description": "Post a message to a Slack channel by name",
        "parameters": {
            "type": "object",
            "properties": {
                "channel_name": {
                    "type": "string",
                    "description": "Slack channel name to post to (without #)"
                },
                "message": {
                    "type": "string",
                    "description": "Message content"
                }
            },
            "required": ["channel_name", "message"]
        }
    }
}

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json(force=True, silent=True)

    if data and data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    event = data.get("event", {})
    if event.get("type") == "message":
        # Get the event timestamp
        event_ts = event.get("event_ts") or event.get("ts")
        
        # Check if we've already processed this event
        if event_ts in processed_events:
            return "", 200
            
        # Add the event to our processed list
        processed_events.append(event_ts)
        
        channel_id = event.get("channel")
        try:
            channel_info = slack_client.conversations_info(channel=channel_id)
            channel_name = channel_info["channel"]["name"]
            
            # Only process if message is from app-store-reviews channel
            if channel_name == "app-store-reviews":
                user_id = event.get("user")
                text = event.get("text", "")
                analyze_and_act(user_id, text, channel_id)
        except SlackApiError as e:
            logging.error("Error getting channel info: %s", e.response['error'])

    return "", 200

@app.route("/debug", methods=["GET"])
def debug():
    logging.debug("🛠️ Debug endpoint hit.")
    return "Debug log printed to console.", 200

def send_slack_dm(user_id, message):
    try:
        dm = slack_client.conversations_open(users=user_id)
        channel_id = dm["channel"]["id"]
        slack_client.chat_postMessage(channel=channel_id, text=message)
    except SlackApiError as e:
        logging.error("Slack API error in send_slack_dm: %s", e.response['error'])

def post_to_slack_channel(channel_name, message):
    channel_id = get_channel_id_by_name(channel_name)
    if not channel_id:
        logging.error(f"Cannot post message: Channel '{channel_name}' not found.")
        return
    try:
        slack_client.chat_postMessage(channel=channel_id, text=message)
    except SlackApiError as e:
        logging.error("Slack API error: %s", e.response['error'])

def analyze_and_act(user_id, text, channel_id):
    prompt = f"""
    You are a Slack assistant. If the message below is about direct deposit, early pay, or getting paid, 
    1. Send the user a direct message using the `send_slack_dm` tool with user_id: {user_id}
    2. Send the message to the 'social' channel using the `post_to_slack_channel` tool
    Send only the original message, not a response.
    Message: \"{text}\"
    """

    try:
        response = oai.chat.completions.create(
            model="gpt-4-1106-preview",
            tools=[send_dm_function, post_to_channel_function],
            tool_choice="auto",
            messages=[
                {"role": "system", "content": "You monitor Slack messages and act on relevant ones."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        # Handle all tool calls
        for tool_call in response.choices[0].message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            
            if tool_call.function.name == "send_slack_dm":
                send_slack_dm(user_id, args["message"])
            elif tool_call.function.name == "post_to_slack_channel":
                post_to_slack_channel("social", args["message"])

    except Exception as e:
        logging.error("Error in analyze_and_act: %s", e)

if __name__ == "__main__":
    app.run(debug=True, port=8080)