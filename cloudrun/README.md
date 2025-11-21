# Cloud Run Service Configuration Files

This directory contains Knative service manifests for deploying the Civic Grant Agent to Google Cloud Run.

## Files

- `backend-service.yaml` - Backend FastAPI service configuration
- `frontend-service.yaml` - Frontend Next.js service configuration

## Usage

These files are used by Skaffold when deploying to Cloud Run using the `cloudrun` profile.

### Deploy with Skaffold

```bash
# Set your GCP project
export GCP_PROJECT="your-project-id"

# Deploy to Cloud Run
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

### Manual Deployment

You can also deploy these services manually using `gcloud`:

```bash
# Deploy backend
gcloud run services replace cloudrun/backend-service.yaml \
  --region us-central1 \
  --project ${GCP_PROJECT}

# Deploy frontend
gcloud run services replace cloudrun/frontend-service.yaml \
  --region us-central1 \
  --project ${GCP_PROJECT}
```

## Configuration Notes

### Backend Service
- Requires `GOOGLE_API_KEY` secret in Google Secret Manager
- Configured for 2 CPU cores and 2Gi memory
- Auto-scales from 0 to 10 instances
- Timeout: 300 seconds

### Frontend Service
- Requires `NEXT_PUBLIC_API_URL` environment variable
- Configured for 1 CPU core and 512Mi memory
- Auto-scales from 0 to 10 instances
- Timeout: 300 seconds

## Prerequisites

Before deploying, ensure:

1. **Google Cloud Project** is set up with billing enabled
2. **Secret Manager** has the `GOOGLE_API_KEY` secret created:
   ```bash
   echo -n "your-api-key" | gcloud secrets create GOOGLE_API_KEY --data-file=-
   ```
3. **Service Account Permissions** are configured for Cloud Run to access secrets
4. **Cloud Run API** is enabled:
   ```bash
   gcloud services enable run.googleapis.com
   ```

## Environment Variables

### Backend
- `GOOGLE_API_KEY` - Google Gemini API key (from Secret Manager)
- `GEMINI_MODEL` - Gemini model to use (default: gemini-2.0-flash-exp)
- `PORT` - Port to listen on (default: 8000)

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL (update after backend deployment)
- `NODE_ENV` - Node environment (production)
- `PORT` - Port to listen on (default: 3000)
- `HOSTNAME` - Host to bind to (0.0.0.0)
- `NEXT_TELEMETRY_DISABLED` - Disable Next.js telemetry

## Post-Deployment

After deploying the backend, update the frontend's `NEXT_PUBLIC_API_URL` in `frontend-service.yaml` with the actual backend URL, then redeploy the frontend:

```bash
# Get backend URL
BACKEND_URL=$(gcloud run services describe civic-grant-agent-backend \
  --region us-central1 \
  --format 'value(status.url)')

# Update frontend-service.yaml with the backend URL
# Then redeploy frontend
```
