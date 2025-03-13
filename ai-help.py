import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import openai
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

# Environment Variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")  # Bot token from Slack
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")    # API key from OpenAI

# Debugging: Print the environment variables
print(f"SLACK_BOT_TOKEN: {SLACK_BOT_TOKEN}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")

# Debugging: Check environment variables
if not SLACK_BOT_TOKEN or not OPENAI_API_KEY:
    raise EnvironmentError("SLACK_BOT_TOKEN or OPENAI_API_KEY not set!")

# Initialize Slack and OpenAI Clients
slack_client = WebClient(token=SLACK_BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

# Flask Application
app = Flask(__name__)

def chatgpt_response(prompt):
    """
    Function to communicate with ChatGPT and return a response.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",  # Replace with "gpt-4" if available
            prompt=prompt,
            timeout=30,  # Add timeout to limit the duration
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7  # Adjust for more or less creativity
        )
        return response['choices'][0]['message']['content']
    except openai.error.OpenAIError as e:
        print(f"Error communicating with OpenAI: {e}")
        return "I'm sorry, I could not process the message at this time."

def handle_message(event_data):
    """
    Handle Slack messages and send a ChatGPT response back to the user.
    """
    try:
        # Extract channel ID and user message
        channel_id = event_data.get('channel')
        user_message = event_data.get('text', '')

        if not channel_id or not user_message:
            print("Missing channel or message data from event!")
            return

        # Get a response from ChatGPT
        bot_response = chatgpt_response(user_message)

        # Send the ChatGPT response to Slack
        slack_client.chat_postMessage(channel=channel_id, text=bot_response)
    except SlackApiError as e:
        print(f"Slack API Error: {e.response['error']}")

@app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    Endpoint for handling Slack events, including URL verification.
    """
    data = request.get_json()  # Parse the JSON payload
    print(f"Received data: {data}")  # Debugging logs

    # Respond to Slack's URL verification challenge
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]}), 200

    # Handle event callbacks specifically
    if data.get("type") == "event_callback":
        event_data = data.get("event", {})
        if event_data.get("type") == "message":  # Process message events
            handle_message(event_data)
        return jsonify({"status": "ok"}), 200

    return jsonify({'message': 'Event received'}), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle generic webhooks for debugging or testing purposes.
    """
    data = request.json
    print(f"Incoming webhook data: {data}")
    return jsonify({"status": "received"}), 200

# Define a route for the root path
@app.route("/")
def home():
    return jsonify({"message": "Welcome to the AI Help API!"}), 200

# Define a route for favicon.ico (optional, just to fix the 404)
@app.route("/favicon.ico")
def favicon():
    return "", 204  # Return a "No Content" response

if __name__ == "__main__":
    # Run the Flask app on the specified port
    print("Starting Flask app...")
    app.run(host="localhost", port=3000, debug=False)