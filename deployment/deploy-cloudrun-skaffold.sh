#!/bin/bash
# Skaffold Cloud Run Deployment Script
# Deploys Civic Grant Agent to Google Cloud Run using Skaffold

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGION=${REGION:-"us-central1"}
DEFAULT_PROJECT=""

echo "================================================"
echo "Civic Grant Agent - Cloud Run Deployment"
echo "Using Skaffold"
echo "================================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Check if skaffold is installed
if ! command -v skaffold &> /dev/null; then
    echo -e "${RED}Error: skaffold not found. Please install Skaffold.${NC}"
    echo "Visit: https://skaffold.dev/docs/install/"
    exit 1
fi

# Get current GCP project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ]; then
    echo -e "${YELLOW}No GCP project is currently set.${NC}"
    echo -e "Please set your project ID:"
    read -p "GCP Project ID: " PROJECT_ID
else
    echo -e "Current GCP project: ${GREEN}${CURRENT_PROJECT}${NC}"
    read -p "Use this project? (y/n) [y]: " USE_CURRENT
    USE_CURRENT=${USE_CURRENT:-y}
    
    if [[ "$USE_CURRENT" =~ ^[Yy]$ ]]; then
        PROJECT_ID=$CURRENT_PROJECT
    else
        read -p "Enter GCP Project ID: " PROJECT_ID
    fi
fi

# Set the project
echo ""
echo "Setting GCP project to: ${PROJECT_ID}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo ""
echo "Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

# Check if GOOGLE_API_KEY secret exists
echo ""
echo "Checking for GOOGLE_API_KEY secret..."
if ! gcloud secrets describe GOOGLE_API_KEY &>/dev/null; then
    echo -e "${YELLOW}GOOGLE_API_KEY secret not found.${NC}"
    read -p "Enter your Google API Key: " API_KEY
    echo -n "$API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-
    echo -e "${GREEN}Secret created successfully.${NC}"
else
    echo -e "${GREEN}GOOGLE_API_KEY secret already exists.${NC}"
fi

# Grant Cloud Run access to the secret
echo ""
echo "Granting Cloud Run access to secrets..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None \
    2>/dev/null || echo "IAM binding already exists"

# Deploy using Skaffold
echo ""
echo "================================================"
echo "Deploying to Cloud Run with Skaffold..."
echo "Region: ${REGION}"
echo "Project: ${PROJECT_ID}"
echo "================================================"
echo ""

# Run skaffold with cloudrun profile
skaffold run \
    -p cloudrun \
    --default-repo=gcr.io/${PROJECT_ID} \
    --region=${REGION}

# Get service URLs
echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""

BACKEND_URL=$(gcloud run services describe civic-grant-agent-backend \
    --region ${REGION} \
    --format 'value(status.url)' 2>/dev/null || echo "Not deployed yet")

FRONTEND_URL=$(gcloud run services describe civic-grant-agent-frontend \
    --region ${REGION} \
    --format 'value(status.url)' 2>/dev/null || echo "Not deployed yet")

echo "Backend URL:  ${BACKEND_URL}"
echo "Frontend URL: ${FRONTEND_URL}"
echo ""

if [ "$BACKEND_URL" != "Not deployed yet" ] && [ "$FRONTEND_URL" != "Not deployed yet" ]; then
    echo -e "${YELLOW}Note: You may need to update the frontend's NEXT_PUBLIC_API_URL${NC}"
    echo -e "${YELLOW}environment variable to point to the backend URL.${NC}"
    echo ""
    echo "To update the frontend with the backend URL:"
    echo "1. Edit cloudrun/frontend-service.yaml"
    echo "2. Update NEXT_PUBLIC_API_URL to: ${BACKEND_URL}"
    echo "3. Re-run: skaffold run -p cloudrun --default-repo=gcr.io/${PROJECT_ID}"
fi

echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo "1. Test the backend: curl ${BACKEND_URL}/health"
echo "2. Open the frontend: ${FRONTEND_URL}"
echo "3. Monitor logs: gcloud run services logs read --service=civic-grant-agent-backend --region=${REGION}"
echo "4. Update environment variables if needed"
echo ""
