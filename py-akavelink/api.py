from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from datetime import datetime
import uuid
import asyncpg
import os
import shutil
import tempfile
from worker import create_bucket_task
from schemas import BucketCreateRequest, BucketCreateResponse, JobStatus, JobStatusResponse, BucketDeleteRequest, BucketDeleteResponse, FileUploadRequest, FileUploadResponse

app = FastAPI(title="py-akavelink")

db_pool = None

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
    job_id = str(uuid.uuid4())
    created_at = datetime.now()    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO bucket_jobs (id, bucket_name, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
            """, job_id, request.bucket_name, "queued", created_at, created_at)
        
        create_bucket_task.delay(job_id, request.bucket_name)
        
        return BucketCreateResponse(
            job_id=job_id,
            bucket_name=request.bucket_name,
            status=JobStatus.queued,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue bucket creation: {str(e)}")

@app.post("/buckets/delete", response_model=BucketDeleteResponse)
async def delete_bucket(request: BucketDeleteRequest):
    job_id = str(uuid.uuid4())
    created_at = datetime.now()
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO bucket_jobs (id, bucket_name, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                job_id,
                request.bucket_name,
                "queued",
                created_at,
                created_at,
            )

        # TODO: implement delete_bucket_task in worker.py and call it here
        # delete_bucket_task.delay(job_id, request.bucket_name)

        return BucketDeleteResponse(
            job_id=job_id,
            bucket_name=request.bucket_name,
            status=JobStatus.queued,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue bucket deletion: {str(e)}",
        )

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
            status=JobStatus(row['status']),
            tx_hash=row['tx_hash'],
            error=row['error'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
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
    
@app.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(bucket_name: str = Form(...), file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    created_at = datetime.now()
    file_name = file.filename
    
    upload_dir = f"/tmp/akave_uploads/{job_id}"
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = f"{upload_dir}/{file_name}"
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO file_jobs (id, job_type, bucket_name, file_name, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                job_id,
                "upload",
                bucket_name,
                file_name,
                "queued",
            )
            
        # upload_file_task.delay(job_id, bucket_name, file_name, temp_path)  # TODO: wire in worker

        return FileUploadResponse(
            job_id=job_id,
            bucket_name=bucket_name,
            file_name=file_name,
            status=JobStatus.queued,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")