from kubernetes import client, config
from flask import Flask, request, jsonify
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

app = Flask(__name__)

@app.route('/get-pods', methods=['POST'])
def get_pods():

    # Get pod version from /version
    def fetch_version(pod_ip):
        try:
            response = requests.get(f"http://{pod_ip}/version", timeout=10)
            return response.text.strip() if response.status_code == 200 else "N/A"
        except requests.RequestException:
            return "N/A"

    # Format Creatioin timestamp to be like in kubectl
    def format_age(creation_timestamp):
        now = datetime.now(timezone.utc)
        age_seconds = (now - creation_timestamp).total_seconds()

        if age_seconds < 3600:  # Less than 1 hour
            minutes = int(age_seconds // 60)
            return f"{minutes}m"
        elif age_seconds < 86400:  # Less than 24 hours
            hours = int(age_seconds // 3600)
            return f"{hours}h"
        elif age_seconds < 172800:  # Less than 48 hours
            hours = int(age_seconds // 3600)
            return f"{hours}h"  # Return hours for 24h to 48h
        else:  # 2 days or more
            days = int(age_seconds // 86400)
            return f"{days}d"

    def create_pod_output(namespace_pods):
        output_lines = []
        
        # Create Output lines for each pod
        for pod in namespace_pods["all"]:
            line = f"{pod['name']:<{max_pod_name_length}} {pod['status']:<{status_column_width}} {pod['age']:<{age_column_width}} {pod['version']:<{version_column_width}}"
            # Replace spaces with dashes
            line = line.replace(" ", "-")
            output_lines.append(line)
    
        return output_lines

    def format_message(output_lines, max_length):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{'Pod Name':<{max_pod_name_length}} {'Status':<{status_column_width}} {'Age':<{age_column_width}} {'Version'}"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        current_chunk = ""
        for line in output_lines:
            # Append the current line and check if it exceeds max_length
            if len(current_chunk) + len(line) + 1 > max_length:  # +1 for the newline
                # If it exceeds, add the current chunk to blocks and start a new one
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": current_chunk.strip()  # Strip to remove trailing newlines
                    }
                })
                current_chunk = ""  # Start a new chunk
            
            # Add the line to the current chunk
            current_chunk += line + "\n"
        
        # Add the last chunk if there's any remaining content
        if current_chunk:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": current_chunk.strip()
                }
            })
        
        return {
            "blocks": blocks
        }

    # Load Kubernetes configuration
    config.load_incluster_config()
    # Connect to kubernetes and pull pods
    try:    
        v1 = client.CoreV1Api()
        pods_list = v1.list_pod_for_all_namespaces(watch=False)
    except client.exceptions.ApiException as error:
        return jsonify(f"Error:" ,"Could not connect to Kubernetes API: Unable to get Pods information\n{error}")
    
    # Dictionary for data organizing
    namespace_pods = {}

    # Stracture everything in a dictionary
    for pod in pods_list.items:
        pod_info = {
            'name': pod.metadata.name,
            'status': pod.status.phase,
            'age': format_age(pod.metadata.creation_timestamp),
            'pod_ip': pod.status.pod_ip,
            'version': "Fetching..." if pod.status.pod_ip else "N/A"
        }
        namespace_pods.setdefault("all", []).append(pod_info) 

    # Calculate the maximum pod name length for alignment
    max_pod_name_length = max(len(pod['name']) for pods in namespace_pods.values() for pod in pods)

    # Use ThreadPoolExecutor to fetch versions concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_pod = {
            executor.submit(fetch_version, pod['pod_ip']): idx 
            for pods in namespace_pods.values() 
            for idx, pod in enumerate(pods) if pod['version'] == "Fetching..."
        }
        for future in as_completed(future_to_pod):
            idx = future_to_pod[future]
            namespace_pods["all"][idx]['version'] = future.result()

    # Prepare output string
    output_lines = []
    status_column_width = 10
    age_column_width = 5
    version_column_width = 5

    # Generate the pod output
    output_lines = create_pod_output(namespace_pods)

    # Generate the formatted message with sections of max 2000 characters
    formatted_message = format_message(output_lines, 2000)

    return jsonify(formatted_message)

@app.route('/get-logs', methods=['POST'])
def get_logs():

    # Check if pod exists in the cluster
    def check_pod_exists_and_get_ns(pod_name):
        config.load_incluster_config() 
        v1 = client.CoreV1Api() 
        # List all pods in all namespaces
        pods = v1.list_pod_for_all_namespaces(watch=False)
        
        for pod in pods.items:
            if pod.metadata.name == pod_name:
                return pod.metadata.namespace # Pod exists, send its namespace
        return None    # Pod does not exist
            
    def get_rows(log, rows_count):
        # Split log into lines
        lines = log.splitlines()
        
        # Count the lines and ensure the requested rows_count does not exceed available lines
        if rows_count > len(lines):
            rows_count = len(lines)
        
        # Get the last `rows_count` amount of lines
        logs = "\n".join(lines[-rows_count:])
        
        return logs

    def format_message(logs, max_length):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Logs for pod {pod_name}:"
                }
            },
            {
                "type": "divider"
            }
        ]
        # Split logs into chunks of a specified max length
        for i in range(0, len(logs), max_length):
            chunk = logs[i:i + max_length]
            blocks.append({
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": chunk
                }
            })
        
        return {
            "blocks": blocks
        }

    # Extract the text from the incoming request
    data = request.json
    # extract pod name and amount of rows
    user_input = data.get('user_input', '')

    # Check for valid input
    parts = user_input.split()
    #check if there are 2 values exactly
    if len(parts) != 2:
        return jsonify("Input Error:" ,"Please provide exactly two values, make sure it is in the correct order (/get-logs <pod> <rows>).")
    else:
        # split to 2 variables
        pod_name, rows_count = user_input.split()
        
        # Check if second value is number
        if rows_count.isdigit():
            rows_count = int(rows_count)
        else:
            return jsonify("Input Error:" ,"The second value must be a number.")
        
    # Check if the pod exists and its namespace
    try:
        namespace = check_pod_exists_and_get_ns(pod_name)
        if namespace is not None:
            pass
        else:
            return jsonify("Error:" ,"Pod Does not exist.")
    except client.exceptions.ApiException as error:
        return jsonify(f"Error:" ,"Could not connect to Kubernetes API: Unable to check if Pod exists\n{error}")
        
    # Connect to Kubernetes and pull logs
    try:
        config.load_incluster_config() 
        v1 = client.CoreV1Api() 
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace)
    except client.exceptions.ApiException as error:
        return jsonify(f"Error:" ,"Could not connect to Kubernetes API: Unable to fetch logs\n{error}")
    
    # get currect amount of rows
    logs = get_rows(logs,rows_count)
    
    # devide to 2000 character sections
    formatted_message = format_message(logs, 2000)

    return jsonify(formatted_message)