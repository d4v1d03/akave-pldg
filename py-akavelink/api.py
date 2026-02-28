from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid
import asyncpg
import os
from worker import create_bucket_task

app = FastAPI(title="Akave Platform - Minimal MVP")

db_pool = None


class BucketCreateRequest(BaseModel):
    bucket_name: str


class BucketCreateResponse(BaseModel):
    job_id: str
    bucket_name: str
    status: str  # queued, processing, completed, failed
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    bucket_name: str
    status: str
    tx_hash: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "akave_platform"),
        user=os.getenv("POSTGRES_USER", "akave"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        min_size=5,
        max_size=20
    )
    print("✅ Database connection pool initialized")


@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()
    print("🔒 Database connection pool closed")


@app.get("/")
async def root():
    return {
        "service": "Akave Platform MVP",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


@app.post("/buckets", response_model=BucketCreateResponse)
async def create_bucket(request: BucketCreateRequest):
    if len(request.bucket_name) < 3:
        raise HTTPException(status_code=400, detail="Bucket name must be at least 3 characters")
    
    if not request.bucket_name.isalnum() and "-" not in request.bucket_name:
        raise HTTPException(status_code=400, detail="Bucket name must be alphanumeric (hyphens allowed)")
    
    job_id = str(uuid.uuid4())
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO bucket_jobs (id, bucket_name, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
            """, job_id, request.bucket_name, "queued", datetime.utcnow(), datetime.utcnow())
        
        create_bucket_task.delay(job_id, request.bucket_name)
        
        return BucketCreateResponse(
            job_id=job_id,
            bucket_name=request.bucket_name,
            status="queued",
            message="Bucket creation job queued successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue bucket creation: {str(e)}")


@app.get("/buckets/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, bucket_name, status, tx_hash, error, created_at, updated_at
                FROM bucket_jobs
                WHERE id = $1
            """, job_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=str(row['id']),
            bucket_name=row['bucket_name'],
            status=row['status'],
            tx_hash=row['tx_hash'],
            error=row['error'],
            created_at=row['created_at'].isoformat(),
            updated_at=row['updated_at'].isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/buckets")
async def list_buckets():
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT bucket_name, tx_hash, created_at
                FROM bucket_jobs
                WHERE status = 'completed'
                ORDER BY created_at DESC
            """)
        
        return {
            "buckets": [
                {
                    "name": row['bucket_name'],
                    "tx_hash": row['tx_hash'],
                    "created_at": row['created_at'].isoformat()
                }
                for row in rows
            ],
            "count": len(rows)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
