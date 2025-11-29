# Kubernetes Development with Skaffold + k3d

Local Kubernetes development environment for Civic Grant Agent.

## Prerequisites

- **Docker** - Container runtime
- **k3d** - Lightweight Kubernetes (`curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash`)
- **kubectl** - Kubernetes CLI
- **Skaffold** - Development workflow (`brew install skaffold`)

## Quick Start

```bash
# 1. Create k3d cluster
k3d cluster create civic-grant-agent --port 8080:8080@loadbalancer --agents 1

# 2. Create secrets
kubectl create secret generic civic-grant-agent-secrets \
  --from-literal=google-api-key=YOUR_GOOGLE_API_KEY

# 3. Deploy with Skaffold (auto-reload on changes)
skaffold dev

# Access at http://localhost:8080
```

## Skaffold Commands

| Command | Description |
|---------|-------------|
| `skaffold dev` | Watch mode - auto-rebuild on changes |
| `skaffold run` | Deploy once |
| `skaffold delete` | Remove all deployed resources |
| `skaffold build` | Build images only |

## Cluster Management

```bash
# View status
kubectl get all
kubectl logs -f deployment/civic-grant-agent

# Stop/start cluster
k3d cluster stop civic-grant-agent
k3d cluster start civic-grant-agent

# Delete cluster
k3d cluster delete civic-grant-agent
```

## Notes

- Resource limits: 512Mi-1Gi memory, 250m-500m CPU (adjust in `backend.yaml`)
- For production deployment, see [deployment/DEPLOYMENT_GUIDE.md](../deployment/DEPLOYMENT_GUIDE.md)

