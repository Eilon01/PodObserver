import slack
import os
from pathlib import Path
from flask import Flask, request, Response, jsonify
import requests
import hashlib
import hmac
import time

# Fetch environment variables
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
K8S_QUESTIONER_SERVICE = os.getenv('K8S_QUESTIONER_SERVICE')
K8S_QUESTIONER_PORT= os.getenv('K8S_QUESTIONER_PORT')

# Define environment variables and their human-readable names
env_variables = {
    'Slack Token': SLACK_TOKEN,
    'SLACK_SIGNING_SECRET': SLACK_SIGNING_SECRET,
    'K8S_QUESTIONER_SERVICE': K8S_QUESTIONER_SERVICE,
    'K8S_QUESTIONER_PORT': K8S_QUESTIONER_PORT
}

# Check which variables are missing and raise error if any do
missing_vars = [variable for variable, value in env_variables.items() if not value]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize Flask app and Slack client
app = Flask(__name__)
client = slack.WebClient(token=SLACK_TOKEN)

# Verify if the request if from slack
def verify_slack_request(request):
    
    # Get slack signature and timestanp
    slack_signature = request.headers['X-Slack-Signature']
    slack_request_timestamp = request.headers['X-Slack-Request-Timestamp']

    # Reject requests older than 1 minute to avoid replay attacks
    if abs(time.time() - int(slack_request_timestamp)) > 60:
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

# Post a message to slack
def send_message(channel_id, message_blocks):
    try:
        client.chat_postMessage(channel=channel_id, blocks=message_blocks)
    except slack.errors.SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

# Format messages for Slack in a block kit format
def format_message(header, message):
    return {
  "blocks": [
                {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": header
                }
                },
                {
                "type": "divider"
                },
                {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
                }
            ]
            }

@app.route('/', methods=['GET'])
def home_page():
    return 'Pod Observer Home Page'

# Route for handling the `/help` command from Slack
@app.route('/help', methods=['POST'])
def help_command():
    # Verify if the incoming request is from Slack
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

    # Retrieve channel info from Slack's request
    channel_id = request.form.get('channel_id')

    # Send help message to the Slack channel
    message = format_message(help_message)
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
        # Send post requesting the pods data
        response = requests.post(f"http://{K8S_QUESTIONER_SERVICE}:{K8S_QUESTIONER_PORT}/get-pods")
        # if post was ok, send message with pods data, else return error
        if response.ok:
            data = response.json()
            header, pods_list = data[0], data[1]
            print(pods_list)
            print(type(pods_list))
            message = format_message(header, pods_list)
            send_message(channel_id, message['blocks'])
        else:
            client.chat_postMessage(channel=channel_id, text="Error: Could not connect to Kubernetes API: K8s Questioner message was not OK.")
   
    # Catch errors for not connecting to k8s questioner
    except requests.exceptions.RequestException as e:
        client.chat_postMessage(channel=channel_id, text="Error: Could not connect to K8s Questioner.")
    
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

    try:
        # Send post requesting the logs and sending pod name and rows count
        response = requests.post(f"http://{K8S_QUESTIONER_SERVICE}:{K8S_QUESTIONER_PORT}/get-logs", json={'user_input': text})
        # if post was ok, send message with logs, else return error
        if response.ok:
            data = response.json()
            header, logs = data[0], data[1]
            print(logs)
            print(type(logs))
            message = format_message(header,logs)
            # client.chat_postMessage(channel=channel_id, text=logs)
            send_message(channel_id, message['blocks'])
        else:
            client.chat_postMessage(channel=channel_id, text="Error: Could not connect to Kubernetes API: K8s Questioner message was not OK.")
    
    # Catch errors for not connecting to k8s questioner
    except requests.exceptions.RequestException as e:
        client.chat_postMessage(channel=channel_id, text="Error: Could not connect to K8s Questioner.")
    
    return Response(), 200