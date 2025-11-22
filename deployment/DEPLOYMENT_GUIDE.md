# Civic Grant Agent - Deployment Guide

## 1. Cloud Run Deployment

There is a unified script to deploy both the Backend and Frontend to Google Cloud Run with Firebase acting as the Load Balancer. Probably don't really need Firebase here but I started out with several more path routing ideas in mind I haven't implemented yet.

### Prerequisites
- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- `skaffold` installed
- `firebase-tools` installed (`npm install -g firebase-tools`)

### Deployment Command

```bash
# Run the all-in-one deployment script
./deployment/firebase-deploy.sh
```

This script will:
1.  Build and deploy the **Backend** to Cloud Run using Skaffold.
2.  Build and deploy the **Frontend** to Cloud Run using Skaffold.
3.  Inject the Backend URL into the Frontend configuration.
4.  Deploy **Firebase Hosting** rules to route traffic to the Frontend container.

---

## 2. Local Development with Skaffold

You can run the entire stack locally on Kubernetes (Minikube, k3d) using Skaffold. This provides hot-reloading for both services.

### Prerequisites
- A local Kubernetes cluster (e.g., Minikube, k3d)
- Docker installed
- `skaffold` installed

### Run Locally

```bash
# Start both services in dev mode
skaffold dev
```

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000

```
