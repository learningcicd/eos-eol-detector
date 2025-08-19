# EOL Scanner Deployment Guide

This guide covers deploying the EOL Scanner to production environments, with a focus on Google Kubernetes Engine (GKE).

## 🏗️ Architecture Overview

The EOL Scanner is designed as a cloud-native application with the following components:

- **FastAPI Web Service**: REST API with authentication and monitoring
- **ML Risk Model**: Intelligent risk assessment using scikit-learn
- **Kubernetes Deployment**: Scalable, secure container deployment
- **Persistent Storage**: For model files and logs
- **Load Balancer**: For external access and SSL termination

## 📋 Prerequisites

### Required Tools

- `gcloud` CLI (Google Cloud SDK)
- `kubectl` CLI
- `docker` CLI
- `git`

### Required Permissions

- GCP Project with billing enabled
- Kubernetes Engine Admin role
- Container Registry Admin role

### Required Tokens

- **API Token**: For authenticating API requests
- **GitHub Token**: For accessing GitHub repositories and SBOM data

## 🚀 Quick Start Deployment

### 1. Clone and Setup

```bash
git clone <repository-url>
cd eol-eos-scanner

# Set environment variables
export PROJECT_ID="your-gcp-project-id"
export CLUSTER_NAME="eol-scanner-cluster"
export API_TOKEN="your-secure-api-token"
export GITHUB_TOKEN="your-github-token"
```

### 2. Create GKE Cluster

```bash
gcloud container clusters create $CLUSTER_NAME \
  --region=us-central1 \
  --num-nodes=3 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10 \
  --machine-type=e2-standard-2 \
  --enable-network-policy \
  --enable-autorepair \
  --enable-autoupgrade
```

### 3. Deploy Application

```bash
# Run the deployment script
./scripts/deploy.sh
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n eol-scanner

# Check services
kubectl get services -n eol-scanner

# Check ingress
kubectl get ingress -n eol-scanner

# Port forward for testing
kubectl port-forward service/eol-scanner-service 8000:80 -n eol-scanner
```

## 🔧 Detailed Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# API Configuration
API_TOKEN=your-secure-api-token-here
LOG_LEVEL=INFO

# GitHub Configuration
GITHUB_TOKEN=your-github-personal-access-token

# Model Configuration
MODEL_PATH=/app/models/maintenance_risk_model.pkl

# Security Configuration
CORS_ORIGINS=["http://localhost:3000", "https://your-frontend-domain.com"]
```

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with the following permissions:
   - `Contents: Read`
   - `Dependency graph: Read`
3. Copy the token and set it in your environment

### API Token Generation

Generate a secure API token for authentication:

```bash
# Generate a random token
openssl rand -hex 32
```

## 🐳 Docker Configuration

### Building the Image

```bash
# Build locally
docker build -t eol-scanner .

# Build for GCR
docker build -t gcr.io/$PROJECT_ID/eol-scanner:$IMAGE_TAG .
```

### Running Locally

```bash
docker run -p 8000:8000 \
  -e API_TOKEN=your-token \
  -e GITHUB_TOKEN=your-github-token \
  -e LOG_LEVEL=INFO \
  eol-scanner
```

## ☁️ Kubernetes Deployment

### Namespace and RBAC

The deployment creates a dedicated namespace with appropriate RBAC:

```bash
kubectl apply -f k8s/namespace.yaml
```

### Secrets Management

Create Kubernetes secrets for sensitive data:

```bash
kubectl create secret generic eol-scanner-secrets \
  --namespace=eol-scanner \
  --from-literal=api-token="$API_TOKEN" \
  --from-literal=github-token="$GITHUB_TOKEN"
```

### Persistent Storage

The deployment uses PersistentVolumeClaims for:

- **Models**: ML model files and training data
- **Logs**: Application logs and audit trails

### Resource Limits

The deployment includes resource limits:

- **CPU**: 250m request, 500m limit
- **Memory**: 256Mi request, 512Mi limit

### Health Checks

The deployment includes:

- **Liveness Probe**: Checks if the application is running
- **Readiness Probe**: Checks if the application is ready to serve traffic

### Autoscaling

Horizontal Pod Autoscaler configuration:

- **Min Replicas**: 2
- **Max Replicas**: 10
- **CPU Target**: 70%
- **Memory Target**: 80%

## 🔒 Security Configuration

### Container Security

- **Non-root User**: Application runs as user `scanner` (UID 1000)
- **Read-only Root Filesystem**: Except for writable volumes
- **Security Context**: Configured in deployment

### Network Security

- **Network Policies**: Restrict pod-to-pod communication
- **Ingress Security**: TLS termination and HTTPS enforcement
- **Service Mesh**: Optional Istio integration

### Secrets Management

- **Kubernetes Secrets**: For API tokens and credentials
- **External Secrets**: Integration with HashiCorp Vault or Google Secret Manager

## 📊 Monitoring and Observability

### Health Checks

```bash
# Health endpoint
curl http://your-domain.com/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-12-01T14:30:22.123456",
  "version": "1.0.0",
  "model_status": "available"
}
```

### Logging

The application logs to:

- **stdout/stderr**: For Kubernetes log collection
- **File**: `/app/reports/eol_scanner.log`

### Metrics

Prometheus metrics endpoints (extensible):

- `/metrics`: Application metrics
- `/health`: Health check metrics

### Alerting

Configure alerts for:

- Pod restarts
- High error rates
- Resource usage
- API response times

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy to GKE

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v0
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}

      - name: Build and push Docker image
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/eol-scanner:${{ github.sha }} .
          docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/eol-scanner:${{ github.sha }}

      - name: Deploy to GKE
        run: |
          gcloud container clusters get-credentials ${{ secrets.CLUSTER_NAME }} --region=${{ secrets.REGION }}
          kubectl set image deployment/eol-scanner eol-scanner=gcr.io/${{ secrets.GCP_PROJECT_ID }}/eol-scanner:${{ github.sha }} -n eol-scanner
          kubectl rollout status deployment/eol-scanner -n eol-scanner
```

## 🧪 Testing

### Local Testing

```bash
# Start the API
./scripts/start_api.sh

# Run tests
./scripts/test_api.py
```

### Production Testing

```bash
# Test health endpoint
curl https://your-domain.com/health

# Test scanning
curl -X POST https://your-domain.com/scan \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{"repo": "microsoft/vscode"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**

   - Check logs: `kubectl logs -n eol-scanner <pod-name>`
   - Verify environment variables
   - Check resource limits

2. **API Authentication Failures**

   - Verify API_TOKEN is set correctly
   - Check secret configuration
   - Validate token format

3. **GitHub API Errors**

   - Verify GITHUB_TOKEN permissions
   - Check rate limiting
   - Validate repository access

4. **Model Loading Issues**
   - Check persistent volume mounts
   - Verify model file permissions
   - Check disk space

### Debug Commands

```bash
# Check pod status
kubectl get pods -n eol-scanner

# View logs
kubectl logs -f deployment/eol-scanner -n eol-scanner

# Check events
kubectl get events -n eol-scanner

# Port forward for debugging
kubectl port-forward service/eol-scanner-service 8000:80 -n eol-scanner

# Exec into pod
kubectl exec -it deployment/eol-scanner -n eol-scanner -- /bin/bash
```

## 📈 Scaling

### Horizontal Scaling

The application automatically scales based on:

- CPU usage
- Memory usage
- Custom metrics

### Vertical Scaling

To increase resource limits:

```bash
# Edit deployment
kubectl edit deployment eol-scanner -n eol-scanner

# Update resource limits
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Database Scaling

For production workloads, consider:

- PostgreSQL for scan history
- Redis for caching
- Elasticsearch for log aggregation

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Update image
kubectl set image deployment/eol-scanner eol-scanner=new-image:tag -n eol-scanner

# Monitor rollout
kubectl rollout status deployment/eol-scanner -n eol-scanner

# Rollback if needed
kubectl rollout undo deployment/eol-scanner -n eol-scanner
```

### Model Updates

```bash
# Train new model
curl -X POST https://your-domain.com/model/train \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d @training_data.json
```

### Backup and Recovery

```bash
# Backup persistent volumes
kubectl get pvc -n eol-scanner

# Backup secrets
kubectl get secret eol-scanner-secrets -n eol-scanner -o yaml > backup-secrets.yaml
```

## 📞 Support

For deployment issues:

1. Check the troubleshooting section
2. Review application logs
3. Verify configuration
4. Contact the development team

---

**Happy Deploying! 🚀**
