# 🚀 Deployment Guide

## Overview

This guide covers deploying ScholarGraph AI in various environments, from local development to production cloud deployments.

## Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 8GB+ (16GB+ recommended for production)
- **Storage**: 50GB+ SSD
- **Network**: Stable internet connection
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows 10+

### Software Dependencies
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 18+
- **Python**: 3.10+
- **PostgreSQL**: 14+ (production)
- **Ollama**: Latest (for LLaMA)

## Local Development Setup

### Quick Start with Docker
```bash
# Clone repository
git clone https://github.com/yourusername/ScholarGraph.git
cd ScholarGraph

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Setup

#### Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.template .env
# Edit .env with your configuration

# Initialize database
python -c "from database.session import init_db; init_db()"

# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### LLaMA Setup
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull LLaMA 3.1
ollama pull llama3.1:8b

# Verify installation
ollama list
```

## Production Deployment

### Docker Production Setup

#### Production Dockerfile
```dockerfile
# Backend Dockerfile
FROM python:3.10-slim AS backend

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

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS frontend

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Use nginx for serving
FROM nginx:alpine
COPY --from=frontend /app/out /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Production Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://scholargraph:password@postgres:5432/scholargraph
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=scholargraph
      - POSTGRES_USER=scholargraph
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  ollama_data:
```

### Kubernetes Deployment

#### Namespace and ConfigMaps
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: scholargraph

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: scholargraph-config
  namespace: scholargraph
data:
  DATABASE_URL: "postgresql://scholargraph:password@postgres:5432/scholargraph"
  REDIS_URL: "redis://redis:6379/0"
  DEBUG: "false"
  HOST: "0.0.0.0"
  PORT: "8000"
```

#### Secrets
```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: scholargraph-secrets
  namespace: scholargraph
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-key>
  PINECONE_API_KEY: <base64-encoded-key>
  JWT_SECRET_KEY: <base64-encoded-key>
```

#### Backend Deployment
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scholargraph-backend
  namespace: scholargraph
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scholargraph-backend
  template:
    metadata:
      labels:
        app: scholargraph-backend
    spec:
      containers:
      - name: backend
        image: scholargraph/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: scholargraph-config
        - secretRef:
            name: scholargraph-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
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

---
# backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: scholargraph-backend
  namespace: scholargraph
spec:
  selector:
    app: scholargraph-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### Frontend Deployment
```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scholargraph-frontend
  namespace: scholargraph
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scholargraph-frontend
  template:
    metadata:
      labels:
        app: scholargraph-frontend
    spec:
      containers:
      - name: frontend
        image: scholargraph/frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"

---
# frontend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: scholargraph-frontend
  namespace: scholargraph
spec:
  selector:
    app: scholargraph-frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

#### Ingress Configuration
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: scholargraph-ingress
  namespace: scholargraph
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - scholargraph.ai
    - api.scholargraph.ai
    secretName: scholargraph-tls
  rules:
  - host: scholargraph.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: scholargraph-frontend
            port:
              number: 80
  - host: api.scholargraph.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: scholargraph-backend
            port:
              number: 8000
```

### Cloud Deployment Options

#### AWS Deployment

##### ECS with Fargate
```bash
# Build and push Docker images
docker build -t scholargraph/backend ./backend
docker build -t scholargraph/frontend ./frontend

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
docker tag scholargraph/backend:latest $ECR_REGISTRY/scholargraph-backend:latest
docker tag scholargraph/frontend:latest $ECR_REGISTRY/scholargraph-frontend:latest
docker push $ECR_REGISTRY/scholargraph-backend:latest
docker push $ECR_REGISTRY/scholargraph-frontend:latest
```

##### CloudFormation Template
```yaml
# infrastructure.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'ScholarGraph AI Infrastructure'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-scholargraph-vpc'

  # Add more resources as needed
```

#### Google Cloud Platform

##### Cloud Run Deployment
```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT-ID/scholargraph-backend ./backend
gcloud builds submit --tag gcr.io/PROJECT-ID/scholargraph-frontend ./frontend

# Deploy services
gcloud run deploy scholargraph-backend \
  --image gcr.io/PROJECT-ID/scholargraph-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy scholargraph-frontend \
  --image gcr.io/PROJECT-ID/scholargraph-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure Deployment

##### Container Instances
```bash
# Create resource group
az group create --name scholargraph-rg --location eastus

# Build and push to ACR
az acr build --registry scholargraph --image backend ./backend
az acr build --registry scholargraph --image frontend ./frontend

# Deploy container instances
az container create \
  --resource-group scholargraph-rg \
  --name scholargraph-backend \
  --image scholargraph.azurecr.io/backend \
  --dns-name-label scholargraph-api \
  --ports 8000
```

## Environment Configuration

### Development Environment (.env)
```bash
# Database
DATABASE_URL=sqlite:///./scholargraph.db

# AI/ML
OPENAI_API_KEY=sk-your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=scholargraph-dev

# Authentication
JWT_SECRET_KEY=dev-secret-key-change-in-production

# App Settings
DEBUG=true
HOST=0.0.0.0
PORT=8000

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB
```

### Production Environment (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/scholargraph

# Redis
REDIS_URL=redis://redis:6379/0

# AI/ML
OPENAI_API_KEY=sk-production-openai-key
PINECONE_API_KEY=production-pinecone-key
PINECONE_INDEX_NAME=scholargraph-prod

# Authentication
JWT_SECRET_KEY=super-secure-production-secret

# App Settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Security
ALLOWED_ORIGINS=https://scholargraph.ai,https://app.scholargraph.ai

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
```

## Monitoring and Logging

### Health Checks
```python
# health_check.py
from fastapi import APIRouter, HTTPException
from database.session import get_db
import redis

router = APIRouter()

@router.get("/health")
async def health_check():
    try:
        # Check database
        db = next(get_db())
        db.execute("SELECT 1")
        
        # Check Redis
        redis_client = redis.Redis(host='redis', port=6379)
        redis_client.ping()
        
        # Check LLM services
        ollama_status = check_ollama()
        openai_status = check_openai()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "ollama": ollama_status,
            "openai": openai_status
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

### Logging Configuration
```python
# logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logHandler)
    
    return logger
```

### Prometheus Metrics
```python
# metrics.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response
```

## Security Configuration

### SSL/TLS Setup
```nginx
# nginx.conf
server {
    listen 80;
    server_name scholargraph.ai;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name scholargraph.ai;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Firewall Configuration
```bash
# UFW setup
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Backend only accessible via reverse proxy
```

## Backup and Recovery

### Database Backup
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
pg_dump -h postgres -U scholargraph scholargraph > $BACKUP_DIR/scholargraph_$DATE.sql

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/scholargraph_$DATE.sql s3://scholargraph-backups/

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -name "scholargraph_*.sql" -mtime +30 -delete
```

### Disaster Recovery
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop services
docker-compose down

# Restore database
psql -h postgres -U scholargraph -d scholargraph < $BACKUP_FILE

# Start services
docker-compose up -d

# Verify restoration
curl -f http://localhost:8000/health || exit 1
```

## Performance Optimization

### Database Optimization
```sql
-- PostgreSQL optimization
CREATE INDEX CONCURRENTLY idx_topic_scores_subject_score ON topic_scores(subject, probability_score DESC);
CREATE INDEX CONCURRENTLY idx_chat_messages_session_created ON chat_messages(session_id, created_at);

-- Partition large tables
CREATE TABLE chat_messages_2024 PARTITION OF chat_messages
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### Caching Strategy
```python
# cache.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            
            return result
        return wrapper
    return decorator
```

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Test connection
psql -h localhost -U scholargraph -d scholargraph
```

#### LLaMA Connection Issues
```bash
# Check Ollama status
docker-compose logs ollama

# Test LLaMA
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.1:8b", "prompt": "Hello"}'
```

#### Frontend Build Errors
```bash
# Clear Next.js cache
rm -rf .next
npm run build

# Check Node.js version
node --version  # Should be 18+
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check database queries
docker-compose logs postgres | grep "slow query"

# Profile application
python -m cProfile -o profile.stats main.py
```

This comprehensive deployment guide ensures ScholarGraph AI can be deployed reliably in any environment, from development to production cloud deployments.
