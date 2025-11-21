# Civic Grant Agent - Deployment Guide

### Google Cloud Run with Skaffold

#### Prerequisites
- Google Cloud Project with billing enabled
- Google Cloud SDK (`gcloud`) installed and authenticated
- Skaffold installed (https://skaffold.dev/docs/install/)
- Google API key for Gemini

#### Quick Deploy with Skaffold - Interactive Script

```bash
# Automated deployment script
chmod +x deployment/deploy-cloudrun-skaffold.sh
./deployment/deploy-cloudrun-skaffold.sh
```

The script handles:
- GCP project setup and API enablement
- Secret Manager configuration
- Building and pushing container images
- Deploying frontend and backend services
- Displaying service URLs

#### Manual Skaffold Deployment

```bash
# Set your project
export GCP_PROJECT="your-project-id"

# Deploy using Skaffold
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

See `cloudrun/README.md` for detailed Cloud Run service configuration.

---
