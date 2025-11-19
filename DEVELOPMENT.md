# Local Development Guide

This guide walks you through setting up and running the Civic Grant Agent locally using Docker, Kubernetes (k3d) and Skaffold.

---

## Prerequisites

Install the following tools before getting started:

- **Docker** - Container runtime
- **k3d** - Lightweight Kubernetes in Docker
- **kubectl** - Kubernetes command-line tool
- **Skaffold** - Kubernetes development workflow tool

---

## Quick Start

### 1. Create a Local Kubernetes Cluster

```bash
k3d cluster create civic-grant-agent
```

This creates a local k3d cluster named `civic-grant-agent`.

### 2. Set Up Your Google API Key

Create the Kubernetes secret with your Google Cloud API key:

```bash
kubectl create secret generic civic-grant-agent-secrets \
  --from-literal=google-api-key='YOUR_GOOGLE_CLOUD_API_KEY'
```

**Note:** Replace `YOUR_GOOGLE_CLOUD_API_KEY` with your actual API key.

### 3. Start the Development Environment

From the project root directory:

```bash
skaffold dev
```

Skaffold will:
- Build the frontend and backend Docker images
- Deploy to your local Kubernetes cluster
- Set up port forwarding automatically
- Watch for file changes and rebuild/redeploy

### 4. Access the Application

Once deployment is complete, open your browser to:

```
http://localhost:3000
```

The backend API will be available at:

```
http://localhost:8000
```

---

## Development Workflow

### Hot Reload

Skaffold watches for file changes and automatically:
- Rebuilds modified containers
- Syncs code changes without full rebuilds (for supported files)
- Restarts affected services

### View Logs

Skaffold streams logs from all containers. You'll see output from both the frontend and backend in your terminal.

### Make Changes

Edit files in `frontend/` or `backend/` directories. Skaffold will detect changes and update the running containers.

---

## Stopping the Environment

### Stop Skaffold

Press `Ctrl+C` in the terminal running `skaffold dev`.

Skaffold will automatically clean up the deployed resources.

### Delete the Cluster (Optional)

To completely remove the k3d cluster:

```bash
k3d cluster delete civic-grant-agent
```

---

## Troubleshooting

### Update the Secret

If you need to update your API key after deployment:

```bash
kubectl delete secret civic-grant-agent-secrets
kubectl create secret generic civic-grant-agent-secrets \
  --from-literal=google-api-key='YOUR_NEW_API_KEY'
kubectl rollout restart deployment civic-grant-agent
```
