# Skaffold Cloud Run Deployment Guide

This guide explains how to deploy the Civic Grant Agent to Google Cloud Run using Skaffold.

## What is Skaffold?

Skaffold is a command-line tool that facilitates continuous development for container-based applications. It handles the workflow for building, pushing, and deploying your application.

## Why Use Skaffold for Cloud Run?

- **Unified Configuration**: Single `skaffold.yaml` for both local development and Cloud Run deployment
- **Automated Builds**: Automatically builds and pushes container images to GCR
- **Multi-Service Deployment**: Deploys both frontend and backend services in one command
- **Environment Consistency**: Same build process for development and production

## Quick Start

### Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Skaffold** installed (https://skaffold.dev/docs/install/)
4. **Google API Key** for Gemini API

### Deploy in 3 Steps

#### Step 1: Set Your GCP Project

```bash
export GCP_PROJECT="your-project-id"
gcloud config set project ${GCP_PROJECT}
```

#### Step 2: Create API Key Secret

```bash
# Create the secret in Google Secret Manager
echo -n "your-google-api-key" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# Grant Cloud Run access to the secret
PROJECT_NUMBER=$(gcloud projects describe ${GCP_PROJECT} --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### Step 3: Deploy with Skaffold

```bash
# Deploy to Cloud Run
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

Or use the automated script:

```bash
chmod +x deployment/deploy-cloudrun-skaffold.sh
./deployment/deploy-cloudrun-skaffold.sh
```

## Understanding the Configuration

### skaffold.yaml Profile

The `cloudrun` profile in `skaffold.yaml` configures:

- **Build**: Uses Google Cloud Build to build container images
- **Push**: Automatically pushes images to Google Container Registry (GCR)
- **Deploy**: Deploys services to Cloud Run in the specified region

### Cloud Run Services

The deployment creates two Cloud Run services:

1. **civic-grant-agent-backend** - FastAPI Python backend
   - 2 CPU cores, 2Gi memory
   - Auto-scales 0-10 instances
   - Configured with Gemini API key from Secret Manager

2. **civic-grant-agent-frontend** - Next.js frontend
   - 1 CPU core, 512Mi memory
   - Auto-scales 0-10 instances
   - Connects to backend API

## Post-Deployment

### Get Service URLs

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

After initial deployment, update the frontend to use the actual backend URL:

1. Get the backend URL from above
2. Edit `cloudrun/frontend-service.yaml`
3. Update the `NEXT_PUBLIC_API_URL` environment variable
4. Redeploy: `skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}`

## Monitoring and Logs

### View Logs

```bash
# Backend logs
gcloud run services logs read civic-grant-agent-backend --region us-central1

# Frontend logs
gcloud run services logs read civic-grant-agent-frontend --region us-central1

# Stream live logs
gcloud run services logs tail civic-grant-agent-backend --region us-central1
```

### Service Status

```bash
# List all services
gcloud run services list --region us-central1

# Describe a service
gcloud run services describe civic-grant-agent-backend --region us-central1
```

## Development Workflow

### Local Development

For local development, use the default profile or the `dev` profile:

```bash
# Create local k3d cluster
k3d cluster create civic-grant-agent

# Deploy locally
skaffold dev

# Or run in background
skaffold run
```

### Deploy to Cloud Run

When ready to deploy to production:

```bash
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

## Updating Your Deployment

### Rebuild and Redeploy

```bash
# Redeploy with latest changes
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

### Update Environment Variables

Edit the service YAML files in `cloudrun/` directory and redeploy.

### Update Secrets

```bash
# Add new version of secret
echo -n "new-api-key" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-

# Services automatically use latest version
```

## Cost Optimization

Cloud Run pricing is based on:
- CPU and memory allocation
- Request duration
- Number of requests

To optimize costs:

1. **Set min instances to 0** - No charges when idle
2. **Adjust max instances** - Limit concurrent instances
3. **Right-size resources** - Use appropriate CPU/memory
4. **Monitor usage** - Review Cloud Console metrics

Estimated cost: $10-30/month for typical volunteer department usage.

## Troubleshooting

### Build Fails

```bash
# Check Cloud Build status
gcloud builds list --limit 5

# View build logs
gcloud builds log <BUILD_ID>
```

### Deployment Fails

```bash
# Check service status
gcloud run services describe civic-grant-agent-backend --region us-central1

# Check recent revisions
gcloud run revisions list --service civic-grant-agent-backend --region us-central1
```

### Service Not Responding

```bash
# Check logs for errors
gcloud run services logs read civic-grant-agent-backend --region us-central1 --limit 50

# Test health endpoint
curl $(gcloud run services describe civic-grant-agent-backend --region us-central1 --format 'value(status.url)')/health
```

## Cleanup

To remove all Cloud Run services:

```bash
# Delete services
gcloud run services delete civic-grant-agent-backend --region us-central1
gcloud run services delete civic-grant-agent-frontend --region us-central1

# Delete container images
gcloud container images delete gcr.io/${GCP_PROJECT}/civic-grant-agent-backend
gcloud container images delete gcr.io/${GCP_PROJECT}/civic-grant-agent-frontend
```

## Additional Resources

- [Skaffold Documentation](https://skaffold.dev/docs/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)

## Support

For issues or questions:
- Check the [deployment/README.md](../deployment/README.md) for general deployment info
- Review [DEVELOPMENT.md](../DEVELOPMENT.md) for local development
- Open an issue on GitHub
