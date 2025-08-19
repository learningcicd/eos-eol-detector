#!/bin/bash

# EOL Scanner GKE Deployment Script
set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-gcp-project-id"}
CLUSTER_NAME=${CLUSTER_NAME:-"eol-scanner-cluster"}
REGION=${REGION:-"us-central1"}
NAMESPACE="eol-scanner"
IMAGE_NAME="eol-scanner"
IMAGE_TAG=${IMAGE_TAG:-"latest"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting EOL Scanner deployment to GKE...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install it first.${NC}"
    exit 1
fi

# Set project
echo -e "${YELLOW}📋 Setting GCP project to: ${PROJECT_ID}${NC}"
gcloud config set project $PROJECT_ID

# Build and push Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG .

echo -e "${YELLOW}📤 Pushing image to Container Registry...${NC}"
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG

# Get cluster credentials
echo -e "${YELLOW}🔑 Getting cluster credentials...${NC}"
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Create namespace if it doesn't exist
echo -e "${YELLOW}📁 Creating namespace...${NC}"
kubectl apply -f k8s/namespace.yaml

# Create secrets (you'll need to set these)
echo -e "${YELLOW}🔐 Creating secrets...${NC}"
if [ -z "$API_TOKEN" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ Please set API_TOKEN and GITHUB_TOKEN environment variables${NC}"
    echo "Example:"
    echo "export API_TOKEN='your-api-token'"
    echo "export GITHUB_TOKEN='your-github-token'"
    exit 1
fi

# Create secrets manually
kubectl create secret generic eol-scanner-secrets \
    --namespace=$NAMESPACE \
    --from-literal=api-token="$API_TOKEN" \
    --from-literal=github-token="$GITHUB_TOKEN" \
    --dry-run=client -o yaml | kubectl apply -f -

# Update deployment with correct image
echo -e "${YELLOW}📝 Updating deployment configuration...${NC}"
sed "s|eol-scanner:latest|gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG|g" k8s/deployment.yaml | kubectl apply -f -

# Wait for deployment to be ready
echo -e "${YELLOW}⏳ Waiting for deployment to be ready...${NC}"
kubectl rollout status deployment/eol-scanner -n $NAMESPACE --timeout=300s

# Get service URL
echo -e "${YELLOW}🌐 Getting service information...${NC}"
kubectl get service eol-scanner-service -n $NAMESPACE

# Port forward for local testing (optional)
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo -e "${YELLOW}To test locally, run:${NC}"
echo "kubectl port-forward service/eol-scanner-service 8000:80 -n $NAMESPACE"
echo ""
echo -e "${YELLOW}Then visit: http://localhost:8000${NC}"
echo -e "${YELLOW}API docs: http://localhost:8000/docs${NC}"

# Show logs
echo -e "${YELLOW}📋 Recent logs:${NC}"
kubectl logs -l app=eol-scanner -n $NAMESPACE --tail=20
