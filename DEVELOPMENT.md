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

## Cloud Run Deployment with Skaffold

You can also deploy the application to Google Cloud Run using Skaffold for a production-ready, serverless deployment.

### Prerequisites for Cloud Run

- **Google Cloud Project** with billing enabled
- **Google Cloud SDK** (`gcloud`) installed and authenticated
- **Skaffold** installed (https://skaffold.dev/docs/install/)
- **Google API Key** for Gemini API

### Quick Deploy to Cloud Run

Use the automated deployment script:

```bash
chmod +x deployment/deploy-cloudrun-skaffold.sh
./deployment/deploy-cloudrun-skaffold.sh
```

This script will:
1. Set up your GCP project
2. Enable required APIs (Cloud Run, Cloud Build, Secret Manager)
3. Create/verify the `GOOGLE_API_KEY` secret
4. Deploy both frontend and backend services to Cloud Run
5. Display the service URLs

### Manual Cloud Run Deployment

If you prefer to deploy manually:

```bash
# 1. Set your GCP project
export GCP_PROJECT="your-project-id"
gcloud config set project ${GCP_PROJECT}

# 2. Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com \
  containerregistry.googleapis.com secretmanager.googleapis.com

# 3. Create the API key secret (if not exists)
echo -n "your-api-key" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# 4. Grant Cloud Run access to secrets
PROJECT_NUMBER=$(gcloud projects describe ${GCP_PROJECT} --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 5. Deploy with Skaffold
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

### View Deployed Services

After deployment, get your service URLs:

```bash
# Backend URL
gcloud run services describe civic-grant-agent-backend \
  --region us-central1 \
  --format 'value(status.url)'

# Frontend URL
gcloud run services describe civic-grant-agent-frontend \
  --region us-central1 \
  --format 'value(status.url)'
```

### Update Frontend Configuration

After deploying the backend, update the frontend's environment variable to point to the actual backend URL:

1. Get the backend URL from the command above
2. Edit `cloudrun/frontend-service.yaml` and update `NEXT_PUBLIC_API_URL`
3. Redeploy: `skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}`

### Monitor Cloud Run Services

View logs:
```bash
# Backend logs
gcloud run services logs read civic-grant-agent-backend --region us-central1

# Frontend logs
gcloud run services logs read civic-grant-agent-frontend --region us-central1
```

### Clean Up Cloud Run Deployment

To remove the Cloud Run services:

```bash
gcloud run services delete civic-grant-agent-backend --region us-central1
gcloud run services delete civic-grant-agent-frontend --region us-central1
```

---

## Troubleshooting

### Local Kubernetes

#### Update the Secret

If you need to update your API key after deployment:

```bash
kubectl delete secret civic-grant-agent-secrets
kubectl create secret generic civic-grant-agent-secrets \
  --from-literal=google-api-key='YOUR_NEW_API_KEY'
kubectl rollout restart deployment civic-grant-agent
```

### Cloud Run

#### Update Secrets

```bash
# Update the secret value
echo -n "new-api-key" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-

# The service will automatically use the latest version
```

#### View Detailed Service Info

```bash
gcloud run services describe civic-grant-agent-backend \
  --region us-central1 \
  --format yaml
```
