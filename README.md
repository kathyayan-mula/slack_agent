# Slack Agent: Intelligent Slack Listener with OpenAI GPT-4 and Flask

This project creates an intelligent Slack bot agent that listens to messages in the app-store-reviews channel and analyzes them using OpenAI's GPT-4. Based on the content of the messages, it can take contextual actions such as sending a DM or posting to the social channel. The agent is powered by Flask, the Slack Web API, and OpenAI's function calling tools.

---

## Features

* 🧠 Listens to messages from app-store-reviews channel
* 🔍 Analyzes messages using GPT-4 with tools
* 🤖 Sends DMs to users and posts to social channel
* 🧪 Flask-based local server for development and debugging

---

## Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/slack-agent.git
cd slack-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies:**

* `flask`
* `slack_sdk`
* `openai`
* `python-dotenv`

---

## Slack App Configuration

1. **Create a new Slack App:**

   * Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**
   * Choose **From Scratch**
   * App Name: `SlackAgent`
   * Workspace: Select your development workspace

2. **Add OAuth Scopes:** Go to **OAuth & Permissions** → **Bot Token Scopes**, add the following:

   * `chat:write`
   * `channels:read`
   * `channels:history`
   * `users:read`
   * `im:write`
   * `channels:join`

3. **Enable Events API:**

   * Under **Event Subscriptions**, enable the toggle
   * Set the Request URL to your Flask server via ngrok (e.g., `https://xxxx.ngrok-free.app/slack/events`)
   * Subscribe to the following bot events:

     * `message.channels`

4. **Install the App to Workspace:**

   * Go to **OAuth & Permissions** → click **Install App to Workspace**
   * Copy the **Bot User OAuth Token** (starts with `xoxb-...`)

---

## Environment Setup

Create a `.env` file with your credentials:

```env
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxxxxxxxx
SLACK_SIGNING_SECRET=your-signing-secret
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxx
```

---

## Running the App

### 1. Start Flask App

```bash
python3 app.py
```

This will run the server at `http://localhost:8080`.

### 2. Start Ngrok

```bash
ngrok http 8080
```

Copy the HTTPS forwarding URL and set it as the **Slack Request URL**.

---

## How It Works

1. The bot listens for messages in the app-store-reviews channel
2. When a message is received, it's analyzed by GPT-4
3. If the message is about direct deposit, early pay, or getting paid:
   - The user receives a direct message
   - The message is posted to the social channel
4. Duplicate message processing is prevented using event timestamps

---

## Tools Registered with GPT

### `send_slack_dm`

* Sends a direct message to a Slack user

### `post_to_slack_channel`

* Posts a message to the social channel

---

## Known Issues

* Make sure the bot is invited to both app-store-reviews and social channels
* Ensure all required OAuth scopes are added to the Slack app

---

## License

MIT License. Use responsibly.