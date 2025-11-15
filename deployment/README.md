# Civic Grant Agent - Deployment Guide

## Deployment Options

### Option 1: Google Cloud Run (Recommended)

Cloud Run provides serverless deployment with automatic scaling.

#### Prerequisites
- Google Cloud Project with billing enabled
- Google Cloud SDK (`gcloud`) installed
- Docker installed locally
- Google API key for Gemini

#### Quick Deploy

```bash
# Set your project ID
export GOOGLE_PROJECT_ID="your-project-id"

# Run deployment script
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

#### Manual Deployment

```bash
# 1. Build the container
docker build -t gcr.io/YOUR_PROJECT_ID/firehouse-ai:latest .

# 2. Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/firehouse-ai:latest

# 3. Deploy to Cloud Run
gcloud run deploy firehouse-ai \
  --image gcr.io/YOUR_PROJECT_ID/firehouse-ai:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "GEMINI_MODEL=gemini-pro" \
  --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest"
```

#### Setting up Secrets

Store your API key in Google Secret Manager:

```bash
# Create secret
echo -n "your-api-key-here" | gcloud secrets create GOOGLE_API_KEY \
  --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
  --member=serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### Option 2: Cloud Build (CI/CD)

Use Cloud Build for automated deployments:

```bash
# Submit build
gcloud builds submit --config deployment/cloudbuild.yaml

# Or set up trigger for Git commits
gcloud builds triggers create github \
  --repo-name=civic-grant-agent-core \
  --repo-owner=xomanova \
  --branch-pattern="^main$" \
  --build-config=deployment/cloudbuild.yaml
```

### Option 3: Docker Compose (Local Development)

For local testing:

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 4: Kubernetes

For production-scale deployment:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: firehouse-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: firehouse-ai
  template:
    metadata:
      labels:
        app: firehouse-ai
    spec:
      containers:
      - name: firehouse-ai
        image: gcr.io/YOUR_PROJECT/firehouse-ai:latest
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: google-api-key
              key: key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

## Environment Variables

Required environment variables:

```bash
GOOGLE_API_KEY=your_google_api_key
GOOGLE_PROJECT_ID=your_google_project_id
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
OUTPUT_DIR=output
```

## Monitoring & Logging

### Cloud Run Logs

```bash
# View logs
gcloud run logs read firehouse-ai --region us-central1

# Stream logs
gcloud run logs tail firehouse-ai --region us-central1
```

### Application Logs

The application logs to both file (`firehouse_ai.log`) and stdout.

## Scaling Configuration

Cloud Run auto-scales based on:
- CPU utilization
- Request concurrency
- Memory usage

Configure in Cloud Run:
```bash
gcloud run services update firehouse-ai \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 80 \
  --cpu-throttling \
  --region us-central1
```

## Cost Optimization

- **Min instances**: Set to 0 to avoid charges when idle
- **Max instances**: Limit to control costs
- **Memory**: 2Gi is recommended; adjust based on needs
- **CPU**: 2 vCPU for good performance

Estimated cost: ~$10-30/month for typical volunteer FD usage.

## Security Best Practices

1. **API Keys**: Store in Secret Manager, never in code
2. **IAM**: Use least-privilege service accounts
3. **VPC**: Deploy in VPC for network isolation (optional)
4. **Authentication**: Add authentication for production use

## Troubleshooting

### Build Fails
```bash
# Check Docker build locally
docker build -t test-build .

# View build logs
gcloud builds log [BUILD_ID]
```

### Deployment Fails
```bash
# Check service status
gcloud run services describe firehouse-ai --region us-central1

# Check revisions
gcloud run revisions list --service firehouse-ai --region us-central1
```

### Runtime Errors
```bash
# View logs
gcloud run logs read firehouse-ai --region us-central1 --limit 50

# Check environment variables
gcloud run services describe firehouse-ai --region us-central1 --format yaml
```

## Performance Tuning

For better performance:
- Increase CPU allocation: `--cpu 4`
- Increase memory: `--memory 4Gi`
- Adjust timeout: `--timeout 600s` (for long-running operations)
- Enable CPU boost: `--cpu-boost` (faster cold starts)

## Updating Deployment

```bash
# Deploy new version
gcloud run deploy firehouse-ai \
  --image gcr.io/YOUR_PROJECT/firehouse-ai:latest \
  --region us-central1

# Gradual rollout
gcloud run services update-traffic firehouse-ai \
  --to-revisions LATEST=50,PREVIOUS=50 \
  --region us-central1
```

## Cleanup

```bash
# Delete Cloud Run service
gcloud run services delete firehouse-ai --region us-central1

# Delete container images
gcloud container images delete gcr.io/YOUR_PROJECT/firehouse-ai:latest
```
