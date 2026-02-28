# Akave Platform MVP

Async bucket creation platform using Akave decentralized storage with FastAPI + Celery.

## Quick Start

```bash
cp .env.example .env
nano .env
```
Add your `AKAVE_PRIVATE_KEY` in the .env file.

```bash
docker-compose up -d
```

## Create Your First Bucket

**Step 1: Create a bucket**
```bash
curl -X POST http://localhost:8000/buckets \
  -H "Content-Type: application/json" \
  -d '{"bucket_name": "my-first-bucket"}'
```

Example response:
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "bucket_name": "my-first-bucket",
  "status": "queued"
}
```

**Step 2: Copy the job_id and check status**

Replace `JOB_ID` with the actual job_id from Step 1:
```bash
curl http://localhost:8000/buckets/jobs/JOB_ID
```

Example:
```bash
curl http://localhost:8000/buckets/jobs/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

Status while processing:
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "bucket_name": "my-first-bucket",
  "status": "processing",
  "tx_hash": null
}
```

Status when completed:
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "bucket_name": "my-first-bucket",
  "status": "completed",
  "tx_hash": "0x1234567890abcdef..."
}
```

**Step 3: List all your buckets**
```bash
curl http://localhost:8000/buckets
```

Returns:
```json
{
  "buckets": [
    {
      "name": "my-first-bucket",
      "tx_hash": "0x1234567890abcdef...",
      "created_at": "2024-01-25T10:00:15"
    }
  ],
  "count": 1
}
```

### Complete Workflow Example

```bash
# Create bucket and save job_id
RESPONSE=$(curl -s -X POST http://localhost:8000/buckets \
  -H "Content-Type: application/json" \
  -d '{"bucket_name": "test-bucket"}')

# Extract job_id
JOB_ID=$(echo $RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
echo "Job ID: $JOB_ID"

# Wait and check status
sleep 5
curl http://localhost:8000/buckets/jobs/$JOB_ID
```

## Architecture

```
API (FastAPI) → Redis → Worker (Celery) → Akave Blockchain
       ↓                      ↓
   PostgreSQL           Job Updates
```

## Other Endpoints

**Health check:**
```bash
curl http://localhost:8000/health
```

**Service info:**
```bash
curl http://localhost:8000/
```

## Tech Stack

- **API**: FastAPI + uvicorn
- **Queue**: Celery + Redis
- **Database**: PostgreSQL 15
- **Storage**: Akave Python SDK

## Useful Commands

**View logs:**
```bash
docker-compose logs -f
docker-compose logs -f worker
docker-compose logs -f api
```

**Scale workers:**
```bash
docker-compose up -d --scale worker=3
```

**Stop/restart:**
```bash
docker-compose down
docker-compose restart
```

## Troubleshooting

**API not responding:**
```bash
docker-compose logs api
```

**Worker not processing:**
```bash
docker-compose logs worker
docker-compose restart worker
```

**Database issues:**
```bash
docker-compose down -v
docker-compose up -d
```
