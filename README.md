# EOL / EOS Scanner - Production Ready

A comprehensive **End-of-Life (EOL)** / **End-of-Support (EOS)** risk detection system with **ML-powered risk assessment**. Available as both a CLI tool and a production-ready **REST API** designed for deployment on **Google Kubernetes Engine (GKE)**.

## 🚀 Features

- **🔍 Multi-source scanning**: GitHub SBOM, local SBOM, or direct file parsing
- **🤖 ML Risk Assessment**: Intelligent risk scoring using features like `days_to_eol`, release recency, and advisory history
- **🌐 REST API**: Production-ready FastAPI service with authentication and monitoring
- **☁️ Cloud Native**: Docker containers and Kubernetes deployment ready
- **🔒 Security First**: Token-based authentication, non-root containers, secure defaults
- **📊 Rich Analytics**: Detailed risk summaries and batch processing capabilities

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Load Balancer │    │   GKE Cluster   │
│   (Optional)    │◄──►│   (Ingress)     │◄──►│   ┌───────────┐ │
└─────────────────┘    └─────────────────┘    │   │ EOL API   │ │
                                              │   │ Service   │ │
┌─────────────────┐    ┌─────────────────┐    │   └───────────┘ │
│   GitHub API    │◄──►│   EOL Scanner   │◄──►│   ┌───────────┐ │
│   (SBOM)        │    │   API           │    │   │ Risk      │ │
└─────────────────┘    └─────────────────┘    │   │ Model     │ │
                                              │   └───────────┘ │
┌─────────────────┐    ┌─────────────────┐    │   ┌───────────┐ │
│   endoflife.date│◄──►│   PyPI/npm      │◄──►│   │ Persistent│ │
│   (EOL Data)    │    │   (Package Info)│    │   │ Storage   │ │
└─────────────────┘    └─────────────────┘    │   └───────────┘ │
                                              └─────────────────┘
```

## 📦 Installation

### Option 1: Local Development

```bash
# Clone and setup
git clone <repository-url>
cd eol-eos-scanner

# Create virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables
cp config.env.example .env
# Edit .env with your tokens
```

### Option 2: Docker

```bash
# Build image
docker build -t eol-scanner .

# Run container
docker run -p 8000:8000 \
  -e API_TOKEN=your-token \
  -e GITHUB_TOKEN=your-github-token \
  eol-scanner
```

### Option 3: GKE Deployment

```bash
# Set environment variables
export PROJECT_ID="your-gcp-project-id"
export CLUSTER_NAME="eol-scanner-cluster"
export API_TOKEN="your-secure-api-token"
export GITHUB_TOKEN="your-github-token"

# Deploy to GKE
./scripts/deploy.sh
```

## 🎯 Usage

### CLI Mode (Original)

```bash
# Scan GitHub repository
python -m eolscan.cli repo --repo owner/name --near-months 6 --out reports/report.json

# Scan local directory
python -m eolscan.cli path --dir /path/to/repo --near-months 6 --table

# Use local SBOM
python -m eolscan.cli path --dir . --sbom ./reports/sbom.spdx.json --out reports/eol-report.json
```

### API Mode (New)

#### Start the API Server

```bash
# Development
python -m eolscan.api

# Production
uvicorn eolscan.api:app --host 0.0.0.0 --port 8000
```

#### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Scan repository
curl -X POST http://localhost:8000/scan \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "owner/repo-name",
    "near_months": 6,
    "include_risk_assessment": true
  }'

# Scan local path
curl -X POST http://localhost:8000/scan \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/repo",
    "near_months": 6,
    "include_risk_assessment": true
  }'

# Batch scan
curl -X POST http://localhost:8000/scan/batch \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '[
    {"repo": "owner/repo1"},
    {"repo": "owner/repo2"},
    {"path": "/local/path"}
  ]'

# Get model information
curl http://localhost:8000/model/info
```

#### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 🤖 ML Risk Model

The system includes an intelligent risk assessment model that scores packages based on:

- **Days to EOL**: How close a package is to end-of-life
- **Release Recency**: How recently the package was updated
- **Advisory History**: Security advisory count and severity
- **Ecosystem Popularity**: Package ecosystem maturity
- **Maintainer Activity**: Number and activity of maintainers

### Risk Levels

- **CRITICAL** (0.8-1.0): Immediate action required
- **HIGH** (0.6-0.8): High priority upgrade needed
- **MEDIUM** (0.4-0.6): Consider upgrading soon
- **LOW** (0.2-0.4): Monitor for future updates
- **MINIMAL** (0.0-0.2): Current version is acceptable

### Example Response

```json
{
  "scan_id": "scan_20241201_143022_12345",
  "timestamp": "2024-12-01T14:30:22.123456",
  "results": [
    {
      "type": "runtime",
      "name": "Python",
      "version": "3.9",
      "status": "Near EOL",
      "eol_date": "2025-10-01",
      "days_to_eol": 80,
      "latest": "3.12",
      "risk_score": 0.75,
      "risk_level": "HIGH",
      "confidence": 0.85,
      "features_used": ["days_to_eol", "days_since_last_release", ...]
    }
  ],
  "summary": {
    "total_items": 5,
    "eol_count": 1,
    "near_eol_count": 2,
    "critical_risks": 1,
    "high_risks": 2
  }
}
```

## 🔧 Configuration

### Environment Variables

| Variable       | Description                  | Required          | Default                                  |
| -------------- | ---------------------------- | ----------------- | ---------------------------------------- |
| `API_TOKEN`    | API authentication token     | Yes               | -                                        |
| `GITHUB_TOKEN` | GitHub Personal Access Token | For repo scanning | -                                        |
| `LOG_LEVEL`    | Logging level                | No                | INFO                                     |
| `MODEL_PATH`   | Path to ML model file        | No                | `/app/models/maintenance_risk_model.pkl` |

### GitHub Token Permissions

For repository scanning, your GitHub token needs:

- `Contents: Read`
- `Dependency graph: Read`

## 🚀 Production Deployment

### GKE Setup

1. **Create GKE Cluster**:

```bash
gcloud container clusters create eol-scanner-cluster \
  --region=us-central1 \
  --num-nodes=3 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10
```

2. **Deploy Application**:

```bash
./scripts/deploy.sh
```

3. **Configure Ingress**:
   Update the domain in `k8s/deployment.yaml` and apply:

```bash
kubectl apply -f k8s/deployment.yaml
```

### Security Considerations

- ✅ Non-root container execution
- ✅ Secrets management via Kubernetes
- ✅ Token-based API authentication
- ✅ CORS configuration
- ✅ Resource limits and requests
- ✅ Health checks and readiness probes
- ✅ Horizontal Pod Autoscaling

### Monitoring

The service includes:

- Health check endpoint (`/health`)
- Structured logging
- Metrics endpoints (extensible)
- Kubernetes liveness/readiness probes

## 🔍 Supported Technologies

### Runtimes

- Python (PyPI)
- Node.js (npm)
- Java (Maven)
- Go
- .NET
- Ruby
- PHP
- Rust

### Operating Systems

- Ubuntu
- Debian
- Alpine Linux
- CentOS
- Rocky Linux
- Red Hat Enterprise Linux

### Package Managers

- pip (requirements.txt, poetry.lock)
- npm (package.json, package-lock.json)
- yarn (yarn.lock)
- pnpm (pnpm-lock.yaml)

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Test API locally
curl http://localhost:8000/health

# Test scanning
curl -X POST http://localhost:8000/scan \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"repo": "microsoft/vscode"}'
```

## 📊 Performance

- **Scan Speed**: ~2-5 seconds per repository
- **API Response Time**: <500ms for typical requests
- **Concurrent Scans**: Supports up to 10 concurrent batch operations
- **Memory Usage**: ~256MB per pod
- **CPU Usage**: ~250m per pod

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: `/docs` endpoint when API is running
- **Issues**: GitHub Issues
- **Security**: Report security issues privately

---

**Built with ❤️ for secure software development**
