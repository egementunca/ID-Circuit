# Deployment Guide

This guide explains how to properly deploy the Identity Circuit Factory to various cloud environments.

## 🏗️ Project Structure for Deployment

After cleanup, your repository should have this clean structure:

```
ID-Circuit/
├── identity_factory/          # Main application
├── sat_revsynth/             # SAT synthesis library
├── tests/                    # Test suite
├── static/                   # Static files for web UI
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
├── start_api.py             # API server entry point
├── README.md                # Main documentation
├── COMPONENTS.md            # Component documentation
├── DEPLOYMENT.md            # This file
└── .gitignore               # Git ignore rules
```

## 🔧 Pre-Deployment Setup

### 1. Clean Installation

```bash
# Remove any existing installations
pip uninstall -y identity-factory sat-revsynth

# Remove egg-info directories
find . -name "*.egg-info" -type d -exec rm -rf {} +

# Clean virtual environment (if needed)
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Fresh installation
pip install -r requirements.txt
pip install -e .
```

### 2. Verify Installation

```bash
# Run tests to ensure everything works
pytest

# Test CLI
python -m identity_factory.cli --help

# Test basic functionality
python -m identity_factory.cli generate --width 3 --length 3
```

## 🚀 Local Development Deployment

### Basic Local Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Start API server
python start_api.py --host 0.0.0.0 --port 8000
```

### Development with Auto-reload

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -e .
pip install uvicorn[standard] watchfiles

# Start with auto-reload
uvicorn identity_factory.api.server:app --reload --host 0.0.0.0 --port 8000
```

## ☁️ Cloud Deployment Options

### Option 1: Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the application
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "identity_factory.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
    identity-factory:
        build: .
        ports:
            - "8000:8000"
        volumes:
            - ./data:/app/data
        environment:
            - IDENTITY_FACTORY_DB_PATH=/app/data/identity_circuits.db
            - IDENTITY_FACTORY_LOG_LEVEL=INFO
        restart: unless-stopped

    # Optional: Add Redis for job queue
    redis:
        image: redis:7-alpine
        ports:
            - "6379:6379"
        volumes:
            - redis_data:/data
        restart: unless-stopped

volumes:
    redis_data:
```

Deploy with Docker:

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
    name: identity-factory
spec:
    replicas: 2
    selector:
        matchLabels:
            app: identity-factory
    template:
        metadata:
            labels:
                app: identity-factory
        spec:
            containers:
                - name: identity-factory
                  image: your-registry/identity-factory:latest
                  ports:
                      - containerPort: 8000
                  env:
                      - name: IDENTITY_FACTORY_DB_PATH
                        value: "/app/data/identity_circuits.db"
                      - name: IDENTITY_FACTORY_LOG_LEVEL
                        value: "INFO"
                  volumeMounts:
                      - name: data-volume
                        mountPath: /app/data
                  livenessProbe:
                      httpGet:
                          path: /health
                          port: 8000
                      initialDelaySeconds: 30
                      periodSeconds: 10
                  readinessProbe:
                      httpGet:
                          path: /health
                          port: 8000
                      initialDelaySeconds: 5
                      periodSeconds: 5
            volumes:
                - name: data-volume
                  persistentVolumeClaim:
                      claimName: identity-factory-pvc
---
apiVersion: v1
kind: Service
metadata:
    name: identity-factory-service
spec:
    selector:
        app: identity-factory
    ports:
        - port: 80
          targetPort: 8000
    type: LoadBalancer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
    name: identity-factory-pvc
spec:
    accessModes:
        - ReadWriteOnce
    resources:
        requests:
            storage: 10Gi
```

### Option 3: Cloud Platform Deployment

#### AWS ECS/Fargate

```bash
# Build and push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-west-2.amazonaws.com
docker build -t identity-factory .
docker tag identity-factory:latest your-account.dkr.ecr.us-west-2.amazonaws.com/identity-factory:latest
docker push your-account.dkr.ecr.us-west-2.amazonaws.com/identity-factory:latest

# Deploy to ECS
aws ecs create-cluster --cluster-name identity-factory-cluster
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster identity-factory-cluster --service-name identity-factory-service --task-definition identity-factory:1 --desired-count 2
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/your-project/identity-factory
gcloud run deploy identity-factory \
  --image gcr.io/your-project/identity-factory \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

#### Azure Container Instances

```bash
# Build and push to Azure Container Registry
az acr build --registry your-registry --image identity-factory .
az container create \
  --resource-group your-rg \
  --name identity-factory \
  --image your-registry.azurecr.io/identity-factory:latest \
  --ports 8000 \
  --memory 2 \
  --cpu 2
```

## ⚙️ Configuration Management

### Environment Variables

Create `.env` file for local development:

```env
# Database
IDENTITY_FACTORY_DB_PATH=./data/identity_circuits.db

# Logging
IDENTITY_FACTORY_LOG_LEVEL=INFO

# SAT Solver
IDENTITY_FACTORY_SAT_SOLVER=minisat-gh

# Features
IDENTITY_FACTORY_ENABLE_POST_PROCESSING=true
IDENTITY_FACTORY_ENABLE_ML_FEATURES=true
IDENTITY_FACTORY_ENABLE_DEBRIS_ANALYSIS=true

# Job Queue (optional)
IDENTITY_FACTORY_REDIS_URL=redis://localhost:6379
IDENTITY_FACTORY_ENABLE_JOB_QUEUE=false

# API
IDENTITY_FACTORY_API_HOST=0.0.0.0
IDENTITY_FACTORY_API_PORT=8000
```

### Production Configuration

For production, use environment variables or configuration management:

```bash
# Set production environment variables
export IDENTITY_FACTORY_DB_PATH=/app/data/identity_circuits.db
export IDENTITY_FACTORY_LOG_LEVEL=WARNING
export IDENTITY_FACTORY_ENABLE_JOB_QUEUE=true
export IDENTITY_FACTORY_REDIS_URL=redis://redis-service:6379
```

## 📊 Monitoring and Logging

### Health Checks

The API provides health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/api/v1/health
```

### Logging Configuration

Configure logging in your deployment:

```python
# In your deployment script
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Metrics

The API provides basic metrics:

```bash
# Get factory statistics
curl http://localhost:8000/api/v1/stats

# Get detailed statistics
curl http://localhost:8000/api/v1/stats/detailed
```

## 🔒 Security Considerations

### API Security

```python
# Add authentication to API
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Implement your token verification logic
    if not is_valid_token(token.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return token.credentials

# Apply to endpoints
@app.post("/api/v1/generate")
async def generate_circuit(
    request: CircuitRequest,
    token: str = Depends(verify_token)
):
    # Your endpoint logic
    pass
```

### Database Security

```bash
# Use encrypted database
export IDENTITY_FACTORY_DB_PATH=/app/data/encrypted_circuits.db
export IDENTITY_FACTORY_DB_ENCRYPTION_KEY=your-secret-key

# Use read-only database for certain operations
export IDENTITY_FACTORY_DB_READ_ONLY=true
```

## 🚀 Performance Optimization

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX idx_circuits_dim_group ON circuits(dim_group_id);
CREATE INDEX idx_circuits_width_length ON circuits(width, length);
CREATE INDEX idx_equivalents_circuit_id ON circuit_equivalents(circuit_id);
```

### Memory Optimization

```python
# Configure memory limits
config = FactoryConfig(
    max_equivalents=5000,  # Limit memory usage
    enable_parquet_storage=True,  # Use efficient storage
    max_workers=2  # Limit concurrent operations
)
```

### Caching

```python
# Add Redis caching
import redis
from functools import lru_cache

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

@lru_cache(maxsize=1000)
def get_circuit_features(circuit_id: int):
    # Cache circuit features
    cache_key = f"circuit_features:{circuit_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Compute features
    features = compute_features(circuit_id)
    redis_client.setex(cache_key, 3600, json.dumps(features))
    return features
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Identity Factory

on:
    push:
        branches: [main]

jobs:
    test:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v3
            - name: Set up Python
              uses: actions/setup-python@v4
              with:
                  python-version: "3.11"
            - name: Install dependencies
              run: |
                  pip install -r requirements.txt
                  pip install -e .
            - name: Run tests
              run: pytest

    build-and-deploy:
        needs: test
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v3
            - name: Build Docker image
              run: docker build -t identity-factory .
            - name: Deploy to cloud
              run: |
                  # Your deployment commands here
                  echo "Deploying to production..."
```

## 📋 Deployment Checklist

-   [ ] Clean installation with `pip install -e .`
-   [ ] All tests pass (`pytest`)
-   [ ] Database schema is created
-   [ ] Environment variables are configured
-   [ ] Health checks are working
-   [ ] Logging is configured
-   [ ] Security measures are in place
-   [ ] Performance monitoring is set up
-   [ ] Backup strategy is implemented
-   [ ] Documentation is updated

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `pip install -e .` was run
2. **Database Errors**: Check database path and permissions
3. **SAT Solver Issues**: Verify SAT solver is installed
4. **Memory Issues**: Reduce `max_equivalents` in configuration
5. **API Errors**: Check health endpoint and logs

### Debug Commands

```bash
# Check installation
python -c "import identity_factory; print('Import successful')"

# Check database
python -c "from identity_factory.database import CircuitDatabase; db = CircuitDatabase(); print('Database OK')"

# Check SAT solver
python -c "from sat_revsynth.sat.solver import Solver; s = Solver('minisat-gh'); print('SAT solver OK')"

# Run with debug logging
IDENTITY_FACTORY_LOG_LEVEL=DEBUG python start_api.py
```

This deployment guide should help you successfully deploy the Identity Circuit Factory to any cloud environment while maintaining clean, organized code and proper configuration management.
