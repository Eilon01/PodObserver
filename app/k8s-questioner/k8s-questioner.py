from kubernetes import client, config
from flask import Flask, request, jsonify
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

app = Flask(__name__)

@app.route('/get-pods', methods=['POST'])
def get_pods():
    # Load Kubernetes configuration
    #config.load_kube_config()
    config.load_incluster_config()

    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)

    namespace_pods = {}

    def fetch_version(pod_ip):
        try:
            response = requests.get(f"http://{pod_ip}/version", timeout=10)
            return response.text.strip() if response.status_code == 200 else "N/A"
        except requests.RequestException:
            return "N/A"

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

    # Group pods by namespace
    for pod in ret.items:
        pod_info = {
            'name': pod.metadata.name,
            'status': pod.status.phase,
            'age': format_age(pod.metadata.creation_timestamp),
            'pod_ip': pod.status.pod_ip,
            'version': "Fetching..." if pod.status.pod_ip else "N/A"
        }
        namespace_pods.setdefault("all", []).append(pod_info)  # Use a single key for all pods

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

    header = f"{'Pod Name':<{max_pod_name_length}} {'Status':<{status_column_width}} {'Age':<{age_column_width}} {'Version':<{version_column_width}}"
    output_lines.append(header)
    output_lines.append("=" * len(header))

    for pod in namespace_pods["all"]:
        line = f"{pod['name']:<{max_pod_name_length}} {pod['status']:<{status_column_width}} {pod['age']:<{age_column_width}} {pod['version']:<{version_column_width}}"
        # Replace spaces with dashes
        line = line.replace(" ", "-")
        output_lines.append(line)

    # Join all lines into a single string
    pods = "\n".join(output_lines)

    return jsonify(pods)

@app.route('/get-logs', methods=['POST'])
def get_logs():

    # fake logs
    with open('fake-logs', 'r') as file:
        logs = file.read()

    # Extract the text from the incoming request
    data = request.json
    text = data.get('text', '')  # Get the command text
    pod_name, num_lines = text.split()  # Assume input format is "pod_name num_lines"
    num_lines = int(num_lines)

    # Split logs into lines
    log_lines = logs.splitlines()

    # Ensure num_lines does not exceed available lines
    if num_lines > len(log_lines):
        num_lines = len(log_lines)-1

    # Get the last num_lines amount of logs
    pod_logs = "\n".join(log_lines[-num_lines:])

    logs_message = [{"type": "section","text": {"type": "mrkdwn","text": f"*Logs for pod '{pod_name}'*:\n{pod_logs}"}}]

    return jsonify(logs_message)

# Run Flask
if __name__ == "__main__":
    app.run(port=6001, debug=True)  
