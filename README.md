# Pod Observer

Pod Observer is a Slack bot designed to monitor and gather detailed information about running pods within a cluster. It offers real-time tracking of pod status, uptime, version, and logs, providing visibility into pod lifecycle events and health.

## Features
- List all running pods in the cluster with their current status.
- Track pod uptime and version information.
- Fetch logs of specific pods for troubleshooting and debugging.

Pod Observer simplifies Kubernetes pod management by integrating with Slack, making it an essential tool for DevOps teams to monitor and maintain cluster health effortlessly.

## How To Use
### Commands
- `/help` - Provides information on how to use the bot and its available commands.
- `/get-pods` - Lists all the running pods in the Kubernetes cluster, their status, uptime, and version of each service.
- `/get-logs` - Retrieves the last `n` log lines from the specified pod.
  - **Example**: 
    ```bash
    /get-logs my-pod-1 20
    ```
    This command returns the last 20 log lines from the pod named `my-pod-1`.

## Repository Structure
To help you find what you need, here is the repository structure:
```bash
.
├── .github/workflows/
│   └── ci.yaml                # GitHub Actions CI job
│
├── app/
│   ├── k8s-questioner/        # Service that communicates with the Kubernetes API
│   └── pod-observer/          # Main service that runs the bot
│
├── argocd/
│   └── app.yaml               # Manifest file for ArgoCD
│
├── helm-chart/
│   └── Pod-Observer/          # Helm Chart for Pod Observer
│
└── slack-bot/
    └── slack-bot-manifest.json # Manifest file for creating the bot
```

## Security
- Pod Observer checks every request to ensure the source is valid.
- The backend service has no public IP or ingress access for pulling data from Kubernetes.
- Network policy for k8s-questioner limits unauthorized access.

## Ease of Use
- Helm chart: Simply update `values.yaml` according to your needs.
- Manifest for creating the bot in Slack.
- ArgoCD and GitHub Actions CI ready for developers.

## Guide
### Clone the Git Repository
```bash
git clone https://github.com/Eilon01/PodObserver.git
```
## Configuration Steps
1. Edit `values.yaml`, ensuring you set your Slack token, signing token, and have an endpoint for Pod Observer.
2. Install the chart
```bash
helm install pod-observer ./helm-chart/Pod-Observer --namespace pod-observer --create-namespace
```
3. Create a bot on the Slack API website using `slack-bot-manifest.json`. Be sure to update your slash command request URL to your Pod Observer endpoint.
