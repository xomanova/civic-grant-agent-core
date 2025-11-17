# Kubernetes Deployment with Skaffold and k3d

This directory contains Kubernetes manifests for deploying the Civic Grant Agent with Skaffold and k3d.

## Prerequisites

1. **Docker** - Container runtime
2. **k3d** - Lightweight Kubernetes
3. **kubectl** - Kubernetes CLI
4. **Skaffold** - Development workflow tool

### Installation (macOS/Linux)

```bash
# Install k3d
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Install kubectl
brew install kubectl  # macOS
# OR
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install Skaffold
brew install skaffold  # macOS
# OR
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
chmod +x skaffold && sudo mv skaffold /usr/local/bin
```

## Quick Start

### 1. Create k3d Cluster

```bash
# Create a local Kubernetes cluster with port forwarding
k3d cluster create civic-grant-agent \
  --port 8080:8080@loadbalancer \
  --agents 1
```

This creates:
- A lightweight Kubernetes cluster
- Port 8080 forwarded to your localhost
- 1 agent node

### 2. Configure Secrets

Create your secret with your actual Google API key:

```bash
kubectl create secret generic civic-grant-agent-secrets \
  --from-literal=google-api-key=YOUR_ACTUAL_GOOGLE_API_KEY
```

### 3. Deploy with Skaffold

```bash
# From the project root
cd /path/to/civic-grant-agent-core

# Development mode (auto-reload on code changes)
skaffold dev

# OR just deploy once
skaffold run
```

### 4. Access the Application

Once deployed, access the ADK Web UI at:
```
http://localhost:8080
```

## Skaffold Commands

### Development Mode
```bash
# Watch for changes and auto-rebuild/redeploy
skaffold dev
```

### Deploy Only
```bash
# Deploy without watching
skaffold run
```

### Debug Mode
```bash
# Deploy with debugging enabled
skaffold debug
```

### Delete Deployment
```bash
# Remove all deployed resources
skaffold delete
```

### Build Only
```bash
# Just build the Docker image
skaffold build
```

## k3d Cluster Management

### View Cluster Info
```bash
# List clusters
k3d cluster list

# Get cluster info
kubectl cluster-info

# View nodes
kubectl get nodes
```

### View Deployments
```bash
# List all resources
kubectl get all

# View deployment status
kubectl get deployment civic-grant-agent

# View logs
kubectl logs -f deployment/civic-grant-agent

# Describe pod for troubleshooting
kubectl describe pod -l app=civic-grant-agent
```

### Port Forwarding (if LoadBalancer not working)
```bash
# Forward port manually
kubectl port-forward service/civic-grant-agent 8080:8080
```

### Stop/Delete Cluster
```bash
# Stop the cluster (preserves state)
k3d cluster stop civic-grant-agent

# Start it again
k3d cluster start civic-grant-agent

# Delete the cluster completely
k3d cluster delete civic-grant-agent
```

## Development Workflow

### 1. Make Code Changes
Edit any Python files in:
- `agent_config.py`
- `agents/`
- `tools/`
- `utils/`

### 2. Skaffold Auto-Reloads
With `skaffold dev` running, Skaffold will:
1. Detect your changes
2. Rebuild the container
3. Redeploy to k3d
4. Show logs in real-time

### 3. Test in Browser
Refresh http://localhost:8080 to see your changes.

## Troubleshooting

### Pod Not Starting
```bash
# Check pod status
kubectl get pods

# View detailed pod info
kubectl describe pod -l app=civic-grant-agent

# Check logs
kubectl logs -f deployment/civic-grant-agent
```

### Secret Not Found
```bash
# Verify secret exists
kubectl get secret civic-grant-agent-secrets

# Recreate if needed
kubectl delete secret civic-grant-agent-secrets
kubectl create secret generic civic-grant-agent-secrets \
  --from-literal=google-api-key=YOUR_KEY
```

### Port 8080 Already in Use
```bash
# Change the port in skaffold.yaml portForward section
# OR stop other services using port 8080
lsof -ti:8080 | xargs kill -9
```

### Image Not Found
```bash
# Ensure local image is being used
k3d image import civic-grant-agent

# OR rebuild with Skaffold
skaffold build --cache-artifacts=false
```

### Can't Connect to Cluster
```bash
# Get kubeconfig
k3d kubeconfig get civic-grant-agent

# Merge with your kubectl config
k3d kubeconfig merge civic-grant-agent --kubeconfig-merge-default
```

## Resource Limits

The deployment is configured with:
- **Requests**: 512Mi memory, 250m CPU
- **Limits**: 1Gi memory, 500m CPU

Adjust in `deployment.yaml` if needed for your workload.

## Production Considerations

For production deployment:

1. **Use a real cluster** (GKE, EKS, AKS) instead of k3d
2. **Set up ingress** with TLS certificates
3. **Use proper secret management** (Google Secret Manager, Vault)
4. **Configure horizontal pod autoscaling**
5. **Set up monitoring** (Prometheus, Grafana)
6. **Enable resource quotas** and limits
7. **Implement backup** for persistent data

## Architecture

```
┌─────────────────────────────────────────┐
│         k3d Cluster                     │
│  ┌───────────────────────────────────┐  │
│  │  civic-grant-agent Deployment     │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Container                  │  │  │
│  │  │  - ADK Web UI (port 8080)   │  │  │
│  │  │  - Google API Key (secret)  │  │  │
│  │  │  - Output volume            │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Service (LoadBalancer)           │  │
│  │  Port: 8080 → 8080                │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
              ↓
    http://localhost:8080
```

## Next Steps

- Read the main [README.md](../README.md) for application usage
- See [ADK_SETUP.md](../ADK_SETUP.md) for ADK-specific details
- Check [deployment/](../deployment/) for cloud deployment options

---

**Built for civic good, deployed for easy access** 🚒
