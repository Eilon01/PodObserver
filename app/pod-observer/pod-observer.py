import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify
import requests
import hashlib
import hmac
import time

# Load .env file containing Slack token and signing secret
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

K8S_QUESTIONER_SERVICE_URL = os.getenv('K8S_QUESTIONER_SERVICE_URL')
# Fetch Slack token and signing secret from environment variables
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

# Check if required environment variables are set
if not SLACK_TOKEN or not SLACK_SIGNING_SECRET:
    raise EnvironmentError("Missing Slack Token or Signing Secret")

# Initialize Flask app and Slack client
app = Flask(__name__)
client = slack.WebClient(token=SLACK_TOKEN)

# Slack request verification function using signing secret to validate authenticity
def verify_slack_request(request):
    
    slack_signature = request.headers['X-Slack-Signature']  # Slack's provided signature
    slack_request_timestamp = request.headers['X-Slack-Request-Timestamp']  # Timestamp for anti-replay protection

    # Reject requests older than 5 minutes to avoid replay attacks
    if abs(time.time() - int(slack_request_timestamp)) > 60 * 5:
        return False

    # Construct the basestring used for verification 
    sig_basestring = f'v0:{slack_request_timestamp}:{request.get_data(as_text=True)}'
    # Generate our own signature using the secret and the request details
    my_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Compare the two signatures and return True if they match
    return hmac.compare_digest(my_signature, slack_signature)


# Function to send a message to Slack using the client
def send_message(channel_id, message_blocks):
    try:
        # Post message to specified Slack channel with formatted blocks
        client.chat_postMessage(channel=channel_id, blocks=message_blocks)
    except slack.errors.SlackApiError as e:
        # Log error if message sending fails
        print(f"Error sending message: {e.response['error']}")


# Function to format messages for Slack in a block kit format
def format_message(message):
    return {"blocks": [{"type": "section","text": {"type": "mrkdwn","text": message}}]}

@app.route('/help', methods=['POST'])
def help_command():
    # Verify if the incoming request is truly from Slack
    if not verify_slack_request(request):
        return Response('Invalid request', status=403)

    # Define the help message to display when users call the `/help` command
    help_message = (
        "*Available Commands*\n\n"
        "*`/help`* - This command provides information on how to use the bot and its available commands.\n\n"
        "*`/get-pods`* - Lists all the running pods in the Kubernetes cluster, their uptime, and the version of each service.\n\n"
        "*`/get-logs <pod-name> <n>`* - Retrieves the last n log lines from the specified pod.\n"
        "    Example: `/get-logs my-pod-1 50` will return the last 50 log lines from the pod named `my-pod-1`."
    )

    message = {"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": help_message}}]}
    
    # Retrieve channel info from Slack's request
    channel_id = request.form.get('channel_id')

    # Send help message to the Slack channel
    send_message(channel_id, message['blocks'])
    return Response(), 200

# Route for handling the `/get-pods` command from Slack
@app.route('/get-pods', methods=['POST'])
def get_pods_command():
    # Verify if the incoming request is from Slack
    if not verify_slack_request(request):
        return Response('Invalid request', status=403)
    
    # Retrieve channel info from Slack's request
    channel_id = request.form.get('channel_id')

    try:
        # Forward command to Kubernetes API service
        response = requests.post(f"{K8S_QUESTIONER_SERVICE_URL}/get-pods")
    
        if response.ok:
            pods_list = response.json()  # Get the response from the K8s API

            print(pods_list)

            # Prepare message for Slack
            message = {"blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": pods_list}}]}
            
            # Send the formatted message to Slack
            send_message(channel_id, message['blocks'])
        else:
            # Log the error or handle it as needed
            client.chat_postMessage(channel=channel_id, text="Error fetching pod information.")

    except requests.exceptions.RequestException as e:
        # Handle connection errors or timeouts
        client.chat_postMessage(channel=channel_id, text="Error: Something went wrong, connection to k8s failed.")
    

    return Response(), 200

# Route for handling the `/get-logs` command from Slack
@app.route('/get-logs', methods=['POST'])
def get_logs_command():
    # Verify if the incoming request is from Slack
    if not verify_slack_request(request):
        return Response('Invalid request', status=403)

    # Retrieve channel info from Slack's request
    channel_id = request.form.get('channel_id')

    # Text contains pod name and number of lines
    text = request.form.get('text') 

    print(text)

    try:
        # Forward command to Kubernetes API service
        response = requests.post(f"{K8S_QUESTIONER_SERVICE_URL}/get-logs", json={'text': text})

        if response.ok:
            logs_info = response.json()  # Get the response from the K8s API

            send_message(channel_id, logs_info)

        else:
            client.chat_postMessage(channel=channel_id, text="Error fetching logs.")
        
    except requests.exceptions.RequestException as e:
        # Handle connection errors or timeouts
        client.chat_postMessage(channel=channel_id, text="Error: Something went wrong, please try again later or contact support.")
    
    return Response(), 200

# Run the Flask application
if __name__ == "__main__":
    app.run(port=6000, debug=True)