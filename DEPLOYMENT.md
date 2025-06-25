# ID-Circuit Deployment Guide

This guide provides step-by-step instructions for deploying the ID-Circuit system in various environments.

## Prerequisites

-   Python 3.8 or higher
-   SQLite3
-   pip (Python package manager)
-   Git (for cloning the repository)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ID-Circuit
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# The database will be automatically created on first run
python -m identity_factory
```

### 5. Start the Development Server

```bash
python start_api.py
```

The application will be available at:

-   Web Interface: http://localhost:8000
-   API Documentation: http://localhost:8000/docs
-   API Base URL: http://localhost:8000/api/v1

## Production Deployment

### Option 1: Direct Deployment

#### 1. Server Setup

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv nginx sqlite3

# Clone and setup application
git clone <repository-url>
cd ID-Circuit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Application

Create a configuration file `config.py`:

```python
import os

class ProductionConfig:
    # Database
    DATABASE_PATH = "/var/lib/id-circuit/identity_circuits.db"

    # Server
    HOST = "0.0.0.0"
    PORT = 8000
    WORKERS = 4

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "/var/log/id-circuit/app.log"
```

#### 3. Setup Systemd Service

Create `/etc/systemd/system/id-circuit.service`:

```ini
[Unit]
Description=ID-Circuit API Server
After=network.target

[Service]
Type=exec
User=id-circuit
Group=id-circuit
WorkingDirectory=/opt/id-circuit
Environment=PATH=/opt/id-circuit/venv/bin
ExecStart=/opt/id-circuit/venv/bin/python start_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4. Setup Nginx Reverse Proxy

Create `/etc/nginx/sites-available/id-circuit`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/id-circuit/static/;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/id-circuit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Start Services

```bash
# Create application user
sudo useradd -r -s /bin/false id-circuit

# Create directories
sudo mkdir -p /opt/id-circuit /var/lib/id-circuit /var/log/id-circuit
sudo chown -R id-circuit:id-circuit /opt/id-circuit /var/lib/id-circuit /var/log/id-circuit

# Start service
sudo systemctl enable id-circuit
sudo systemctl start id-circuit
```

### Option 2: Docker Deployment

#### 1. Create Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "start_api.py"]
```

#### 2. Create Docker Compose

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
    id-circuit:
        build: .
        ports:
            - "8000:8000"
        volumes:
            - ./data:/app/data
        environment:
            - DATABASE_PATH=/app/data/identity_circuits.db
        restart: unless-stopped

    nginx:
        image: nginx:alpine
        ports:
            - "80:80"
        volumes:
            - ./nginx.conf:/etc/nginx/nginx.conf
        depends_on:
            - id-circuit
        restart: unless-stopped
```

#### 3. Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f id-circuit
```

### Option 3: Cloud Deployment

#### AWS EC2 Deployment

1. **Launch EC2 Instance**:

    - Use Ubuntu 20.04 LTS
    - t3.medium or larger
    - Configure security groups for ports 80, 443, 22

2. **Install Dependencies**:

    ```bash
    sudo apt-get update
    sudo apt-get install python3 python3-pip python3-venv nginx sqlite3
    ```

3. **Deploy Application**:

    ```bash
    git clone <repository-url>
    cd ID-Circuit
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

4. **Configure Nginx and Systemd** (as in Option 1)

#### Google Cloud Platform

1. **Create Compute Engine Instance**:

    - Use Ubuntu 20.04 LTS
    - e2-medium or larger
    - Allow HTTP/HTTPS traffic

2. **Deploy using startup script**:

    ```bash
    #!/bin/bash
    apt-get update
    apt-get install -y python3 python3-pip nginx sqlite3

    git clone <repository-url>
    cd ID-Circuit
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Setup systemd service
    # ... (same as Option 1)
    ```

## Configuration

### Environment Variables

Set these environment variables for production:

```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_PATH="/var/lib/id-circuit/identity_circuits.db"
export LOG_LEVEL="INFO"
export MAX_EQUIVALENTS="10000"
export ENABLE_POST_PROCESSING="true"
```

### Database Configuration

For production, consider using PostgreSQL instead of SQLite:

1. Install PostgreSQL
2. Create database and user
3. Update database connection in `factory_manager.py`

### Security Considerations

1. **HTTPS**: Use Let's Encrypt or other SSL certificate
2. **Firewall**: Configure firewall rules
3. **Authentication**: Implement API authentication if needed
4. **Rate Limiting**: Add rate limiting to prevent abuse

## Monitoring and Logging

### Log Configuration

Configure logging in `factory_manager.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    handler = RotatingFileHandler(
        '/var/log/id-circuit/app.log',
        maxBytes=10000000,  # 10MB
        backupCount=5
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

### Health Checks

Add health check endpoint:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

### Monitoring

Consider using:

-   **Prometheus** for metrics collection
-   **Grafana** for visualization
-   **Sentry** for error tracking

## Backup and Recovery

### Database Backup

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/var/backups/id-circuit"
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 /var/lib/id-circuit/identity_circuits.db ".backup $BACKUP_DIR/backup_$DATE.db"
```

### Application Backup

```bash
# Backup application files
tar -czf /var/backups/id-circuit/app_$(date +%Y%m%d).tar.gz /opt/id-circuit/
```

## Troubleshooting

### Common Issues

1. **Database Permission Errors**:

    ```bash
    sudo chown -R id-circuit:id-circuit /var/lib/id-circuit/
    ```

2. **Port Already in Use**:

    ```bash
    sudo netstat -tulpn | grep :8000
    sudo kill -9 <PID>
    ```

3. **Memory Issues**:
    - Reduce `max_equivalents` in configuration
    - Monitor memory usage with `htop`

### Log Analysis

```bash
# Check application logs
sudo journalctl -u id-circuit -f

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX idx_circuits_dim_group ON circuits(dim_group_id);
CREATE INDEX idx_representatives_composition ON representatives(gate_composition);
```

### Application Tuning

1. **Worker Processes**: Adjust based on CPU cores
2. **Memory Limits**: Set appropriate memory limits
3. **Connection Pooling**: Configure database connection pooling

## Updates and Maintenance

### Application Updates

```bash
# Stop service
sudo systemctl stop id-circuit

# Backup current version
cp -r /opt/id-circuit /opt/id-circuit.backup

# Update code
cd /opt/id-circuit
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Start service
sudo systemctl start id-circuit
```

### Database Maintenance

```bash
# Optimize database
sqlite3 /var/lib/id-circuit/identity_circuits.db "VACUUM;"

# Check database integrity
sqlite3 /var/lib/id-circuit/identity_circuits.db "PRAGMA integrity_check;"
```

---

This deployment guide covers the most common deployment scenarios. For specific requirements or custom configurations, refer to the component documentation in `COMPONENTS.md`.
