# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Set Up Environment

```bash
cd /Users/amitpandey/pldg/akave/project

# Copy environment template
cp .env.example .env

# Edit .env and add your Akave private key
nano .env  # or use your preferred editor
```

Required: Add your `AKAVE_PRIVATE_KEY` in `.env`

### Step 2: Start Services

```bash
# Start all services (API, Worker, PostgreSQL, Redis)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 3: Test the API

```bash
# Test health
curl http://localhost:8000/health

# Create a bucket
curl -X POST http://localhost:8000/buckets \
  -H "Content-Type: application/json" \
  -d '{"bucket_name": "my-test-bucket"}'

# Save the job_id from response, then check status:
curl http://localhost:8000/buckets/jobs/{job_id}

# List all buckets
curl http://localhost:8000/buckets
```

### Step 4: Run Automated Tests

```bash
# Install httpx for testing
pip install httpx requests

# Run test suite
python test_api.py
```

## 📊 What Happens Behind the Scenes?

1. **API receives request** → Creates job in PostgreSQL → Returns job_id instantly
2. **Redis queue** → Holds the job
3. **Celery worker** → Picks up job → Calls Akave SDK → Creates bucket on blockchain
4. **Database updated** → Status changes: queued → processing → completed
5. **You poll** → GET /buckets/jobs/{job_id} to see progress

## 🔍 Monitoring

### Check Worker Status
```bash
# Worker logs
docker-compose logs -f worker

# API logs
docker-compose logs -f api
```

### Database Queries
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U akave -d akave_platform

# Check jobs
SELECT bucket_name, status, created_at FROM bucket_jobs;

# Count by status
SELECT status, COUNT(*) FROM bucket_jobs GROUP BY status;
```

### Redis Inspection
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check queue length
LLEN celery

# View keys
KEYS *
```

## 🛠️ Troubleshooting

### API not starting?
```bash
docker-compose logs api
# Check for port conflicts on 8000
```

### Worker not processing?
```bash
# Restart worker
docker-compose restart worker

# Check environment variables
docker-compose exec worker env | grep AKAVE
```

### Database issues?
```bash
# Reinitialize database
docker-compose down -v
docker-compose up -d
```

## 📈 Scaling

```bash
# Run 3 workers in parallel
docker-compose up -d --scale worker=3

# Check all workers
docker-compose ps worker
```

## 🧹 Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (deletes database data)
docker-compose down -v
```

## 📝 Project Structure

```
project/
├── api.py              # FastAPI application
├── celery_app.py       # Celery configuration
├── worker.py           # Worker tasks
├── schema.sql          # Database schema
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Service orchestration
├── Dockerfile          # Container image
├── test_api.py         # Test suite
└── README.md           # Full documentation
```

## 🎯 Next Steps

1. ✅ Create buckets via API
2. 📊 Add monitoring dashboard
3. 📁 Implement file upload
4. 🧊 Integrate Apache Iceberg
5. ☸️ Deploy to Kubernetes

---

