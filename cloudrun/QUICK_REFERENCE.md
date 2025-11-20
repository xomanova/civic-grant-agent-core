# Skaffold Cloud Run Deployment - Quick Reference

## Prerequisites Checklist

- [ ] Google Cloud Project with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] `skaffold` installed (https://skaffold.dev/docs/install/)
- [ ] Google API key for Gemini

## Installation Commands

### Install Skaffold (if not installed)

**Linux:**
```bash
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
sudo install skaffold /usr/local/bin/
```

**macOS:**
```bash
brew install skaffold
```

**Windows:**
```powershell
choco install skaffold
```

## Deployment Methods

### Method 1: Automated Script (Easiest)

```bash
# Navigate to project directory
cd civic-grant-agent-core

# Run the automated deployment script
chmod +x deployment/deploy-cloudrun-skaffold.sh
./deployment/deploy-cloudrun-skaffold.sh
```

The script will:
1. ✅ Prompt for your GCP project ID
2. ✅ Enable required APIs
3. ✅ Create/verify Google API key secret
4. ✅ Configure IAM permissions
5. ✅ Deploy both services to Cloud Run
6. ✅ Display service URLs

### Method 2: Manual Skaffold (Full Control)

```bash
# 1. Set up GCP project
export GCP_PROJECT="your-project-id"
gcloud config set project ${GCP_PROJECT}

# 2. Enable APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# 3. Create API key secret
echo -n "your-google-api-key" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# 4. Grant permissions
PROJECT_NUMBER=$(gcloud projects describe ${GCP_PROJECT} --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# 5. Deploy with Skaffold
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

### Method 3: Step-by-Step (Learning)

```bash
# Step 1: Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Step 2: Build images (uses Cloud Build)
skaffold build -p cloudrun --default-repo=gcr.io/YOUR_PROJECT_ID

# Step 3: Deploy services
skaffold deploy -p cloudrun --default-repo=gcr.io/YOUR_PROJECT_ID

# Or combine build + deploy
skaffold run -p cloudrun --default-repo=gcr.io/YOUR_PROJECT_ID
```

## Post-Deployment

### Get Service URLs

```bash
# Backend URL
BACKEND_URL=$(gcloud run services describe civic-grant-agent-backend \
    --region us-central1 \
    --format 'value(status.url)')
echo "Backend: $BACKEND_URL"

# Frontend URL
FRONTEND_URL=$(gcloud run services describe civic-grant-agent-frontend \
    --region us-central1 \
    --format 'value(status.url)')
echo "Frontend: $FRONTEND_URL"
```

### Update Frontend Configuration

After first deployment, update frontend to use actual backend URL:

```bash
# 1. Edit cloudrun/frontend-service.yaml
# Replace NEXT_PUBLIC_API_URL value with your backend URL

# 2. Redeploy
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

### Test the Deployment

```bash
# Test backend health endpoint
curl $BACKEND_URL/health

# Test backend API
curl $BACKEND_URL/api/status

# Open frontend in browser
open $FRONTEND_URL
```

## Common Operations

### View Logs

```bash
# Backend logs (last 50 lines)
gcloud run services logs read civic-grant-agent-backend \
    --region us-central1 \
    --limit 50

# Frontend logs (streaming)
gcloud run services logs tail civic-grant-agent-frontend \
    --region us-central1

# All services
gcloud run services logs read \
    --region us-central1 \
    --limit 100
```

### Update Deployment

```bash
# Make code changes, then redeploy
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}

# Force rebuild without cache
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT} --cache-artifacts=false
```

### Update Environment Variables

```bash
# Edit cloudrun/backend-service.yaml or cloudrun/frontend-service.yaml
# Then redeploy
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}
```

### Update Secrets

```bash
# Add new version of secret
echo -n "new-api-key" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-

# No need to redeploy - Cloud Run uses latest version automatically
```

### Scale Services

```bash
# Update max instances
gcloud run services update civic-grant-agent-backend \
    --max-instances 20 \
    --region us-central1

# Set min instances (for faster response)
gcloud run services update civic-grant-agent-backend \
    --min-instances 1 \
    --region us-central1
```

## Monitoring

### Service Status

```bash
# List all services
gcloud run services list --region us-central1

# Detailed service info
gcloud run services describe civic-grant-agent-backend \
    --region us-central1

# List revisions
gcloud run revisions list \
    --service civic-grant-agent-backend \
    --region us-central1
```

### Metrics (via Cloud Console)

```bash
# Open Cloud Run dashboard
gcloud run services describe civic-grant-agent-backend \
    --region us-central1 \
    --format='value(metadata.selfLink)' | \
    xargs -I {} echo "https://console.cloud.google.com/run/detail/us-central1/civic-grant-agent-backend?project=${GCP_PROJECT}"
```

## Troubleshooting

### Build Fails

```bash
# Check build logs
gcloud builds list --limit 5
gcloud builds log [BUILD_ID]

# Test local build
docker build -f backend/Dockerfile .
docker build -f frontend/Dockerfile frontend/
```

### Deployment Fails

```bash
# Check service events
gcloud run services describe civic-grant-agent-backend \
    --region us-central1 \
    --format yaml

# Check IAM permissions
gcloud projects get-iam-policy ${GCP_PROJECT}

# Verify secrets exist
gcloud secrets describe GOOGLE_API_KEY
```

### Service Not Starting

```bash
# Check logs for errors
gcloud run services logs read civic-grant-agent-backend \
    --region us-central1 \
    --limit 100

# Check environment variables
gcloud run services describe civic-grant-agent-backend \
    --region us-central1 \
    --format='value(spec.template.spec.containers[0].env)'
```

### Connection Issues

```bash
# Verify service is public
gcloud run services get-iam-policy civic-grant-agent-backend \
    --region us-central1

# Make service public (if needed)
gcloud run services add-iam-policy-binding civic-grant-agent-backend \
    --region us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"
```

## Cleanup

### Delete Services

```bash
# Delete Cloud Run services
gcloud run services delete civic-grant-agent-backend --region us-central1 --quiet
gcloud run services delete civic-grant-agent-frontend --region us-central1 --quiet

# Delete container images
gcloud container images delete gcr.io/${GCP_PROJECT}/civic-grant-agent-backend --quiet
gcloud container images delete gcr.io/${GCP_PROJECT}/civic-grant-agent-frontend --quiet

# Delete secrets (optional)
gcloud secrets delete GOOGLE_API_KEY --quiet
```

## Cost Estimation

Cloud Run pricing (approximate):
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests
- **Free tier**: 2 million requests/month, 360,000 GiB-seconds, 180,000 vCPU-seconds

**Estimated monthly cost for typical volunteer department:**
- Low usage (100 requests/day): ~$5-10/month
- Medium usage (500 requests/day): ~$15-25/month
- High usage (2000 requests/day): ~$30-50/month

With min-instances=0, you only pay when the service is handling requests.

## Environment Variables Reference

### Backend Service
| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | From Secret Manager |
| `GEMINI_MODEL` | Gemini model version | `gemini-2.0-flash-exp` |
| `PORT` | Service port | `8000` |

### Frontend Service
| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Set after backend deployment |
| `NODE_ENV` | Node environment | `production` |
| `PORT` | Service port | `3000` |
| `HOSTNAME` | Bind hostname | `0.0.0.0` |
| `NEXT_TELEMETRY_DISABLED` | Disable telemetry | `1` |

## Additional Resources

- [Skaffold Documentation](https://skaffold.dev/docs/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Skaffold Cloud Run Guide](https://skaffold.dev/docs/deployers/cloudrun/)
- [Complete Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Cloud Run Configuration](./README.md)
