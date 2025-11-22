#!/bin/bash
# Firebase - All-in-One Deployment Script
# Architecture:
#   1. Backend -> Cloud Run (via Skaffold)
#   2. Frontend -> Firebase to Cloud Run

set -e

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

# --- 2. BACKEND DEPLOYMENT (Cloud Run) ---
echo -e "\n${BLUE}--- Step 1: Deploying Backend to Cloud Run ---${NC}"

# Ensure Artifact Registry Exists
if ! gcloud artifacts repositories describe ${REPO_NAME} --location=${REGION} &>/dev/null; then
    echo "Creating Artifact Registry repo..."
    gcloud artifacts repositories create ${REPO_NAME} \
        --repository-format=docker --location=${REGION} --description="Civic Grant Agent Repo"
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
    --region ${REGION} --member="allUsers" --role="roles/run.invoker" &>/dev/null

# Get Backend URL
BACKEND_URL=$(gcloud run services describe civic-grant-agent-backend --region ${REGION} --format 'value(status.url)')
echo -e "${GREEN}Backend is live at: ${BACKEND_URL}${NC}"

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
    --region ${REGION} --member="allUsers" --role="roles/run.invoker" &>/dev/null

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