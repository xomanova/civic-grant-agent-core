#!/bin/bash
# Firebase - All-in-One Deployment Script
# Architecture:
#   1. Backend -> Cloud Run (via Skaffold)
#   2. Frontend -> Firebase to Cloud Run

set -e

# Parse arguments
BACKEND_ONLY=false
for arg in "$@"; do
  case $arg in
    --backend-only)
      BACKEND_ONLY=true
      shift
      ;;
  esac
done

# PREVENT HANGS: Disable interactive prompts and update checks
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Firebase - All-in-One Deployment Script      ${NC}"
echo -e "${BLUE}================================================${NC}"

# --- 1. CONFIGURATION & CHECKS ---
REGION=${REGION:-"us-central1"}
REPO_NAME="civic-grant-agent"

# Check dependencies
for cmd in gcloud skaffold npm firebase; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is not installed.${NC}"
        exit 1
    fi
done

# Project Setup
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$CURRENT_PROJECT" ]; then
    read -p "Enter GCP Project ID: " PROJECT_ID
else
    echo -e "Current Project: ${GREEN}${CURRENT_PROJECT}${NC}"
    read -p "Use this project? (y/n) [y]: " CONFIRM
    CONFIRM=${CONFIRM:-y}
    if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
        PROJECT_ID=$CURRENT_PROJECT
    else
        read -p "Enter GCP Project ID: " PROJECT_ID
    fi
fi

gcloud config set project ${PROJECT_ID}
export GCP_PROJECT=${PROJECT_ID}

# --- 1.5 SECRETS CONFIGURATION ---
echo -e "\n${BLUE}--- Step 1.5: Configuring Secrets ---${NC}"

# Function to ensure a secret exists
ensure_secret() {
    local secret_name=$1
    local prompt_text=$2
    
    # Check if secret exists
    if gcloud secrets describe $secret_name --project=$PROJECT_ID --quiet &>/dev/null; then
        echo -e "${GREEN}Secret $secret_name already exists. Skipping prompt.${NC}"
    else
        read -p "$prompt_text: " secret_value
        if [ -n "$secret_value" ]; then
            echo "Creating secret $secret_name..."
            echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --project=$PROJECT_ID --quiet 1>/dev/null
        else
            echo -e "${YELLOW}Warning: No value provided for $secret_name. Skipping.${NC}"
        fi
    fi
}

ensure_secret "GOOGLE_API_KEY" "Enter Google API Key (for Gemini Model)"
ensure_secret "GOOGLE_SEARCH_API_KEY" "Enter Google Search API Key (for Custom Search)"
ensure_secret "GOOGLE_SEARCH_ENGINE_ID" "Enter Google Search Engine ID (CX)"
ensure_secret "SIMPLER_GRANTS_API_KEY" "Enter Simpler Grants API Key (from https://api.simpler.grants.gov)"

# Grant Cloud Run Service Account access to secrets
# Note: This assumes the default compute service account is used. 
# For production, use a dedicated service account.
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Granting Secret Access to Service Account: ${SERVICE_ACCOUNT}..."
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" --project=$PROJECT_ID --quiet 1>/dev/null || true

gcloud secrets add-iam-policy-binding GOOGLE_SEARCH_API_KEY \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" --project=$PROJECT_ID --quiet 1>/dev/null || true

gcloud secrets add-iam-policy-binding GOOGLE_SEARCH_ENGINE_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" --project=$PROJECT_ID --quiet 1>/dev/null || true

gcloud secrets add-iam-policy-binding SIMPLER_GRANTS_API_KEY \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" --project=$PROJECT_ID --quiet 1>/dev/null || true

# --- 2. BACKEND DEPLOYMENT (Cloud Run with Sidecar) ---
echo -e "\n${BLUE}--- Step 1: Deploying Backend to Cloud Run (with Grants MCP Sidecar) ---${NC}"

# Ensure Artifact Registry Exists
if ! gcloud artifacts repositories describe ${REPO_NAME} --location=${REGION} --quiet &>/dev/null; then
    echo "Creating Artifact Registry repo..."
    gcloud artifacts repositories create ${REPO_NAME} \
        --repository-format=docker --location=${REGION} --description="Civic Grant Agent Repo" --quiet
fi
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Deploy ONLY the backend using Skaffold
# We assume skaffold.yaml is configured to build the backend image
echo "Building and Deploying Backend..."
skaffold run -p cloudrun \
    --default-repo=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME} \
    --module=backend  # <--- IMPORTANT: Assumes you defined modules in skaffold.yaml, or just ensure skaffold only targets backend

# Make Backend Public (Required for Firebase to talk to it)
echo "Configuring Backend IAM..."
gcloud run services add-iam-policy-binding civic-grant-agent-backend \
    --region ${REGION} --member="allUsers" --role="roles/run.invoker" --quiet 1>/dev/null

# Get Backend URL
# BACKEND_URL=$(gcloud run services describe civic-grant-agent-backend --region ${REGION} --format 'value(status.url)')
# Use custom domain for backend
BACKEND_URL="https://civic-grant-agent-core.xomanova.io"
echo -e "${GREEN}Backend is live at: ${BACKEND_URL}${NC}"

if [ "$BACKEND_ONLY" = true ]; then
    echo -e "${GREEN}Backend deployment complete. Stopping as --backend-only flag was passed.${NC}"
    exit 0
fi

# Update NEXT_PUBLIC_API_URL in frontend-service.yaml
echo "Updating NEXT_PUBLIC_API_URL in frontend-service.yaml to ${BACKEND_URL}..."
# Use sed to find the line with NEXT_PUBLIC_API_URL and replace the value in the NEXT line
sed -i '/name: NEXT_PUBLIC_API_URL/{n;s|value: ".*"|value: "'"${BACKEND_URL}"'"|;}' cloudrun/frontend-service.yaml

# --- 3. FRONTEND DEPLOYMENT (Cloud Run) ---
echo -e "\n${BLUE}--- Step 2: Deploying Frontend to Cloud Run ---${NC}"

# Deploy Frontend using Skaffold
echo "Building and Deploying Frontend..."
skaffold run -p cloudrun \
    --default-repo=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME} \
    --module=frontend

# Make Frontend Public
echo "Configuring Frontend IAM..."
gcloud run services add-iam-policy-binding civic-grant-agent-frontend \
    --region ${REGION} --member="allUsers" --role="roles/run.invoker" --quiet 1>/dev/null

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe civic-grant-agent-frontend --region ${REGION} --format 'value(status.url)')
echo -e "${GREEN}Frontend is live at: ${FRONTEND_URL}${NC}"

# --- 4. FIREBASE CONFIGURATION ---
echo -e "\n${BLUE}--- Step 3: Configuring Firebase Hosting ---${NC}"

# Generate .firebaserc
cat > deployment/firebase/.firebaserc <<EOF
{
  "projects": {
    "default": "${PROJECT_ID}"
  }
}
EOF

# Generate firebase.json (Load Balancer Mode)
# - **              -> Frontend (Next.js App and Runtime Middleware)
cat > deployment/firebase/firebase.json <<EOF
{
  "hosting": {
    "site": "${PROJECT_ID}",
    "public": "public",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "run": {
          "serviceId": "civic-grant-agent-frontend",
          "region": "${REGION}"
        }
      }
    ]
  }
}
EOF

# Create empty public directory (required by Firebase, but must stay empty for Cloud Run rewrites)
mkdir -p deployment/firebase/public
# Ensure public directory is empty (remove any placeholder files)
rm -f deployment/firebase/public/*

# --- 5. FINAL DEPLOY ---
echo -e "\n${BLUE}--- Step 4: Deploying to Firebase Global CDN ---${NC}"

# Ensure Firebase is enabled on the project
if ! firebase projects:list | grep -q "${PROJECT_ID}"; then
    echo "Initializing Firebase on project..."
    firebase projects:addfirebase ${PROJECT_ID} --y || echo "Please enable Firebase manually in console if this fails."
fi

# Deploy from the firebase directory
(cd deployment/firebase && firebase deploy --only hosting)

echo -e "\n${GREEN}================================================"
echo "      DEPLOYMENT COMPLETE "
echo "================================================"
echo -e "App URL:      https://${PROJECT_ID}.web.app"
echo -e "Backend URL:  ${BACKEND_URL}"
echo -e "Custom Domain: https://civic-grant-agent.xomanova.io"
echo "================================================${NC}"