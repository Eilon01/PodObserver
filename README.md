# Pod Observer

Pod Observer is a Slack bot designed to monitor and gather detailed information about running pods within a cluster. It offers real-time tracking of pod status, updtime, version and logs providing visibility into pod lifecycle events and health.

## Features:
 - List all running pods in the cluster with their current status.
 - Track pod uptime and version information.
 - Fetch logs of specific pods for troubleshooting and debugging.

Pod Observer simplifies Kubernetes pod management by integrating with Slack, making it an essential tool for DevOps teams to monitor and maintain cluster health effortlessly.

## How To Use:
### Commands:
/help - This command provides information on how to use the bot and its available commands.

/get-pods - Lists all the running pods in the Kubernetes cluster, their status, uptime, and version of each service.

/get-logs - Retrieves the last n log lines from the specified pod.
            Example: /get-logs my-pod-1 20 will return the last 20 log lines from the pod named my-pod-1.



Repository stracture to help you find what you need
```bash
.
├── .github/workflows/
│   └── ci.yaml     = Github actions CI job
│
├── app/
│   ├── k8s-questioner/            = Service that communicates with k8s api
│   └── pod-observer/              = Main service that runs the bot
│
├── argocd/
│   └── app.yaml                   = Manifest file for argocd
│
├── helm-chart/
│   └── Pod-Observer/              = Helm Chart for Pod Observer
│
└── slack-bot/
    └── slack-bot-manifest.json    = Manifest file for creating the bot
```
## Security:
- Pod Observer check every request and makes sure the source is good
- backend service with no access public ip or ingress for pulling data from k8s
- Network policy for K8s Questioner limiting breaches

## Ease of use:
- Helm chart, just update values.yaml according to your needs
- manifest for creating the bot in slack
- argocd and github actions ci ready for devs

# Guide:
### clone the git repository
```bash
git clone https://github.com/Eilon01/PodObserver.git
```

### Edit values.yaml, make sure you set your slack token, signing token, make sure you have an endpoint to pod observer

### Create a bot in slack api website with slack-bot-manifest.json, make sure to update your slash command request url to your pod observer endpoint.