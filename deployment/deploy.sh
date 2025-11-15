#!/bin/bash
# Deployment script for Google Cloud Run

set -e

# Configuration
PROJECT_ID=${GOOGLE_PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="firehouse-ai"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "================================================"
echo "Deploying Civic Grant Agent to Google Cloud Run"
echo "================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Authenticate (if needed)
echo "Checking authentication..."
gcloud auth list

# Set project
echo "Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the container
echo ""
echo "Building container image..."
docker build -t ${IMAGE_NAME}:latest .

# Push to Container Registry
echo ""
echo "Pushing image to Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --timeout 300s \
  --set-env-vars "GEMINI_MODEL=gemini-pro,GEMINI_TEMPERATURE=0.7" \
  --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest"

# Get the service URL
echo ""
echo "Deployment complete!"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "Service URL: ${SERVICE_URL}"

echo ""
echo "================================================"
echo "Next steps:"
echo "1. Configure your secrets in Google Secret Manager"
echo "2. Update department_config.json with your information"
echo "3. Test the deployment"
echo "================================================"
