# Docker Deployment Guide

Complete guide for running Reader3 in Docker containers.

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1. Create config.json with your AI provider
cp config.example.json config.json
# Edit config.json with your API key

# 2. Start the application
docker-compose up -d

# 3. Access at http://localhost:8123
```

### Option 2: Docker CLI

```bash
# Build image
docker build -t reader3 .

# Run container
docker run -d \
  -p 8123:8123 \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/books_data:/app/data \
  -v $(pwd)/reader_data.db:/app/reader_data.db \
  --name reader3-app \
  reader3
```

## Configuration

### Environment Variables

You can use environment variables instead of config.json:

```bash
docker run -d \
  -p 8123:8123 \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -v $(pwd)/books_data:/app/data \
  --name reader3-app \
  reader3
```

### Using .env File

```bash
# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Docker Compose will automatically load .env
docker-compose up -d
```

## Docker Compose Profiles

### Default (Main App Only)

```bash
docker-compose up -d
```

### With Ollama (Local AI)

```bash
# Start app + Ollama
docker-compose --profile ollama up -d

# Pull a model in Ollama
docker exec -it reader3-ollama ollama pull llama3.1

# Update config.json to use Ollama:
{
  "ai": {
    "provider": "ollama",
    "model": "llama3.1",
    "base_url": "http://ollama:11434"
  }
}
```

## Volume Management

### Persistent Data

The following directories should be mounted as volumes:

```yaml
volumes:
  - ./books_data:/app/data          # Processed EPUB books
  - ./config.json:/app/config.json  # AI configuration
  - ./reader_data.db:/app/reader_data.db  # Flashcard database
  - ./epub_files:/app/epub_files    # Optional: Source EPUB files
```

### Backup Data

```bash
# Backup database
docker exec reader3-app cp /app/reader_data.db /app/data/backup.db
docker cp reader3-app:/app/data/backup.db ./backup.db

# Backup all data
docker run --rm \
  -v reader3_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/reader3-backup.tar.gz /data
```

### Restore Data

```bash
# Restore database
docker cp ./backup.db reader3-app:/app/reader_data.db
docker-compose restart
```

## Processing EPUB Files

### Method 1: Mount EPUB Directory

```bash
# Add EPUB files to epub_files/ directory
cp ~/Downloads/dracula.epub epub_files/

# Enter container
docker exec -it reader3-app bash

# Process EPUB
cd /app
python reader3.py epub_files/dracula.epub

# Exit container
exit
```

### Method 2: Copy Files In

```bash
# Copy EPUB into container
docker cp dracula.epub reader3-app:/app/dracula.epub

# Process it
docker exec reader3-app python reader3.py /app/dracula.epub

# Clean up source file
docker exec reader3-app rm /app/dracula.epub
```

### Method 3: Helper Script

Create `process_book.sh`:

```bash
#!/bin/bash
EPUB_FILE=$1

if [ -z "$EPUB_FILE" ]; then
  echo "Usage: ./process_book.sh <epub_file>"
  exit 1
fi

docker cp "$EPUB_FILE" reader3-app:/app/temp.epub
docker exec reader3-app python reader3.py /app/temp.epub
docker exec reader3-app rm /app/temp.epub

echo "Book processed successfully!"
```

Usage:
```bash
chmod +x process_book.sh
./process_book.sh ~/Downloads/dracula.epub
```

## Health Checks

The container includes health checks:

```bash
# Check container health
docker ps

# View health check logs
docker inspect reader3-app | grep Health -A 10

# Manual health check
docker exec reader3-app python -c "import requests; print(requests.get('http://localhost:8123/').status_code)"
```

## Logs and Debugging

### View Logs

```bash
# Follow logs
docker-compose logs -f

# View specific service
docker-compose logs -f reader3

# Last 100 lines
docker-compose logs --tail=100

# With Docker CLI
docker logs -f reader3-app
```

### Debug Mode

```bash
# Run with debug output
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up

# Or with Docker CLI
docker run -it --rm \
  -p 8123:8123 \
  -v $(pwd)/config.json:/app/config.json:ro \
  -e PYTHONDONTWRITEBYTECODE=1 \
  reader3 \
  python -u server.py
```

### Shell Access

```bash
# Bash shell in running container
docker exec -it reader3-app bash

# Start container with shell (for debugging)
docker run -it --rm reader3 bash
```

## Performance Tuning

### Resource Limits

```yaml
# docker-compose.yml
services:
  reader3:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Network Optimization

```bash
# Use host network for better performance
docker run -d --network host reader3
```

## Security

### Run as Non-Root User

Add to Dockerfile:
```dockerfile
RUN useradd -m -u 1000 reader && \
    chown -R reader:reader /app

USER reader
```

### Read-Only Filesystem

```bash
docker run -d \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /app/.cache \
  -v $(pwd)/data:/app/data \
  reader3
```

### Security Scanning

```bash
# Scan image for vulnerabilities
docker scan reader3

# Using Trivy
trivy image reader3
```

## Multi-Architecture Support

### Build for Multiple Platforms

```bash
# Build for AMD64 and ARM64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t reader3:latest \
  --push \
  .
```

### For Raspberry Pi

```bash
docker buildx build \
  --platform linux/arm/v7 \
  -t reader3:armv7 \
  .
```

## Production Deployment

### Using Docker Compose in Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  reader3:
    image: reader3:latest
    restart: always
    ports:
      - "127.0.0.1:8123:8123"  # Only localhost
    volumes:
      - reader3_data:/app/data
      - reader3_db:/app/reader_data.db
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123/"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  reader3_data:
  reader3_db:
```

Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Behind Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name reader.example.com;

    location / {
        proxy_pass http://localhost:8123;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### With SSL (Let's Encrypt)

```bash
# Using Traefik
docker-compose -f docker-compose.yml -f docker-compose.traefik.yml up -d
```

## Updating

### Update to Latest Version

```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build

# Restart with new image
docker-compose up -d

# Clean up old images
docker image prune
```

### Rolling Update (Zero Downtime)

```bash
# Build new image with different tag
docker build -t reader3:v2 .

# Start new container
docker run -d \
  -p 8124:8123 \
  -v reader3_data:/app/data \
  --name reader3-v2 \
  reader3:v2

# Test new version
curl http://localhost:8124/

# Switch traffic (update nginx/traefik)
# Then stop old container
docker stop reader3-app
docker rm reader3-app

# Rename new container
docker rename reader3-v2 reader3-app
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs reader3-app

# Check if port is in use
sudo netstat -tulpn | grep 8123

# Verify volumes
docker inspect reader3-app | grep Mounts -A 20
```

### Permission Issues

```bash
# Fix volume permissions
docker exec -it reader3-app chown -R $(id -u):$(id -g) /app/data

# Or from host
sudo chown -R $(id -u):$(id -g) ./books_data
```

### Database Locked

```bash
# Stop container
docker-compose down

# Check for stale locks
ls -la reader_data.db*

# Remove lock file if exists
rm reader_data.db-shm reader_data.db-wal

# Restart
docker-compose up -d
```

### Out of Memory

```bash
# Check container stats
docker stats reader3-app

# Increase memory limit
docker update --memory=2g reader3-app

# Or in docker-compose.yml
services:
  reader3:
    mem_limit: 2g
```

## Monitoring

### Prometheus Metrics (Future)

Add to your application:
```python
from prometheus_client import start_http_server, Counter

# Start metrics server
start_http_server(8000)
```

### Health Monitoring

```bash
# Simple health check script
while true; do
  if curl -f http://localhost:8123/ > /dev/null 2>&1; then
    echo "✓ Healthy"
  else
    echo "✗ Unhealthy - restarting"
    docker-compose restart
  fi
  sleep 60
done
```

## CI/CD Integration

### GitHub Actions

See `.github/workflows/docker.yml` for automated builds.

### Auto-Deploy on Push

```yaml
# .github/workflows/deploy.yml
- name: Deploy to server
  run: |
    ssh user@server 'cd /opt/reader3 && git pull && docker-compose up -d --build'
```

---

For more information, see the main [README.md](README.md)
