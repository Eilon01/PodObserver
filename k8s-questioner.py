from kubernetes import client, config
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get-pods', methods=['POST'])
def get_pods():
    # Simulated response for listing pods
    pods = [
        {"namespace": "namespace1", "name": "name1", "status": "Running", "age": "5d", "version": "v1.2.3"},
        {"namespace": "namespace2", "name": "name2", "status": "Pending", "age": "10d", "version": "v1.2.4"},
        {"namespace": "namespace999", "name": "name999", "status": "Running", "age": "1d", "version": "v1.2.1"}
    ]
    return jsonify(pods)

@app.route('/get-logs', methods=['POST'])
def get_logs():
    # Extract the text from the incoming request
    data = request.json
    text = data.get('text', '')  # Get the command text
    pod_name, num_lines = text.split()  # Assume input format is "pod_name num_lines"

    # Simulated log response
    logs = f"Logs for pod '{pod_name}': this is {num_lines} of logs..."  # Mocked logs
    return jsonify(logs)

# Run Flask
if __name__ == "__main__":
    app.run(port=5001, debug=True)  # Assuming this runs on a different port
