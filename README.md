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
## Key Features
- Pod Observer check every request and makes sure the source is good
- Easy to deploy - just pull the repo and update your tokens in the values.yaml
- Pod autoscaler deployed
- Argocd server deployed
- Aws LB controller deployed
- Ebs CSI controller deployed

## Counter Service - Key Points
- Created Dockerfile with slim base image
- Counter is saved in redis database, backed up by pvc
- Gets credentials with configMap
- Deployed using a custom helm chart
- Counter-better app with nicer ui, POST button and build version

## Github Actions - Key Points
- Running on every commit to main branch
- Building and pushing new docker image to dockerhub with last commit SHA as tag
- Updates counter-service's and counter-better's helm chart image tag 

## ArgoCD - Key Points
- Being deployed with terraform
- Deploying apps by code
- Using app of apps
