# TeamAI Deployment Guide for MBZUAI

## Quick Start (Local Development)

```bash
# 1. Clone and setup
cd teamAI
cp .env.production.example .env
# Edit .env with your API keys

# 2. Run with Docker
docker-compose up -d

# 3. Access at http://localhost:8001
```

## Deployment Options for MBZUAI

### Option 1: Azure Container Apps (Recommended)

**Best for**: Production deployment with auto-scaling, managed SSL, and easy integration with Azure services.

**Why Azure?**
- MBZUAI likely has existing Azure infrastructure
- Container Apps provides serverless container hosting
- Built-in HTTPS, custom domains, and auto-scaling
- Integrates with Azure Monitor for logging

**Estimated Cost**: ~$20-50/month for moderate usage

**Steps**:
```bash
# 1. Install Azure CLI and login
az login

# 2. Create resource group
az group create --name teamai-rg --location uaenorth

# 3. Create Container Registry
az acr create --resource-group teamai-rg --name teamaiacr --sku Basic

# 4. Build and push image
az acr build --registry teamaiacr --image teamai:latest .

# 5. Create Container App
az containerapp create \
  --name teamai \
  --resource-group teamai-rg \
  --image teamaiacr.azurecr.io/teamai:latest \
  --target-port 8001 \
  --ingress external \
  --env-vars "K2_API_KEY=..." "NOTION_API_KEY=..." \
  --cpu 1.0 --memory 2.0Gi
```

---

### Option 2: AWS App Runner

**Best for**: Simple deployment with automatic scaling and managed infrastructure.

**Why AWS?**
- Very simple deployment from Docker image
- Automatic scaling based on traffic
- Built-in HTTPS and load balancing

**Estimated Cost**: ~$25-60/month

**Steps**:
```bash
# 1. Push to ECR
aws ecr create-repository --repository-name teamai
docker tag teamai:latest <account>.dkr.ecr.region.amazonaws.com/teamai:latest
docker push <account>.dkr.ecr.region.amazonaws.com/teamai:latest

# 2. Create App Runner service via console or CLI
aws apprunner create-service --service-name teamai \
  --source-configuration imageRepository={imageIdentifier=...,imageRepositoryType=ECR}
```

---

### Option 3: Google Cloud Run

**Best for**: Serverless deployment with pay-per-use pricing.

**Why GCP?**
- Pay only when requests are being processed
- Automatic HTTPS and custom domain support
- Good for variable/bursty traffic

**Estimated Cost**: ~$10-40/month (usage-based)

**Steps**:
```bash
# 1. Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/teamai

# 2. Deploy
gcloud run deploy teamai \
  --image gcr.io/PROJECT_ID/teamai \
  --platform managed \
  --region us-central1 \
  --set-env-vars "K2_API_KEY=...,NOTION_API_KEY=..."
```

---

### Option 4: DigitalOcean App Platform

**Best for**: Simple, affordable deployment for small to medium scale.

**Why DigitalOcean?**
- Very simple deployment from GitHub or Docker
- Predictable pricing
- Good documentation

**Estimated Cost**: ~$12-25/month (Basic tier)

**Steps**:
1. Connect your GitHub repository
2. Select Docker as the build type
3. Configure environment variables
4. Deploy

---

### Option 5: Self-Hosted on MBZUAI Infrastructure

**Best for**: Full control, data sovereignty, on-premise requirements.

**Requirements**:
- Linux server with Docker installed
- 2+ CPU cores, 4GB+ RAM
- SSL certificate (Let's Encrypt recommended)

**Steps**:
```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh

# 2. Clone repo and configure
git clone https://github.com/your-org/teamai.git
cd teamai
cp .env.production.example .env
nano .env  # Configure API keys

# 3. Deploy with docker-compose
docker-compose --profile production up -d

# 4. Setup SSL with Certbot (if needed)
certbot --nginx -d teamai.mbzuai.ac.ae
```

---

## Recommended Architecture for Production

```
                    ┌─────────────────┐
                    │   CloudFlare    │
                    │   (CDN + WAF)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Load Balancer  │
                    │  (HTTPS term.)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │  TeamAI   │  │  TeamAI   │  │  TeamAI   │
        │ Instance 1│  │ Instance 2│  │ Instance 3│
        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Shared Volume  │
                    │  (SQLite/Chroma)│
                    └─────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │  K2 API   │  │   Notion  │  │   SMTP    │
        │ (LLM360)  │  │    API    │  │  (Gmail)  │
        └───────────┘  └───────────┘  └───────────┘
```

## Environment Variables Checklist

| Variable | Required | Description |
|----------|----------|-------------|
| `K2_API_KEY` | Yes | LLM360 K2 API key |
| `NOTION_API_KEY` | Yes | Notion integration token |
| `NOTION_DATABASE_ID` | Yes | Tasks Tracker database ID |
| `SMTP_USER` | Optional | Email for notifications |
| `SMTP_PASS` | Optional | Gmail App Password |
| `TEAMAI_EMAIL` | Optional | Email forwarding inbox |

## Health Checks

The application exposes health endpoints:
- `GET /api/openclaw/status` - Overall system status
- `GET /` - Frontend availability

## Monitoring Recommendations

1. **Logging**: Use CloudWatch, Azure Monitor, or GCP Logging
2. **Metrics**: Track API response times, error rates
3. **Alerts**: Set up alerts for:
   - API error rate > 5%
   - Response time > 30s
   - Disk usage > 80%

## Backup Strategy

```bash
# Backup data volume
docker run --rm -v teamai-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/teamai-backup-$(date +%Y%m%d).tar.gz /data

# Restore
docker run --rm -v teamai-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/teamai-backup-YYYYMMDD.tar.gz -C /
```

## Security Hardening

1. Enable API key authentication in production
2. Configure CORS to only allow your domain
3. Use HTTPS (SSL/TLS) everywhere
4. Rotate API keys periodically
5. Enable rate limiting (already configured in nginx.conf)

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/teamai/issues
- Internal: teamai@mbzuai.ac.ae
