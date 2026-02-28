from celery_app import celery_app
from akavesdk import SDK, SDKConfig
import asyncpg
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_job_status(job_id: str, status: str, tx_hash: str = None, error: str = None):
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "akave_platform"),
        user=os.getenv("POSTGRES_USER", "akave"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )
    
    try:
        await conn.execute("""
            UPDATE bucket_jobs
            SET status = $1, tx_hash = $2, error = $3, updated_at = $4
            WHERE id = $5
        """, status, tx_hash, error, datetime.utcnow(), job_id)
    finally:
        await conn.close()


def get_akave_sdk():
    private_key = os.getenv("AKAVE_PRIVATE_KEY")
    if not private_key:
        raise ValueError("AKAVE_PRIVATE_KEY environment variable not set")
    
    config = SDKConfig(
        address=os.getenv("AKAVE_NODE_ADDRESS", "connect.akave.ai:5500"),
        private_key=private_key,
        max_concurrency=5,
        block_part_size=128 * 1024,
        use_connection_pool=True,
        connection_timeout=30
    )
    
    return SDK(config)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def create_bucket_task(self, job_id: str, bucket_name: str):
    import asyncio
    
    logger.info(f"[Job {job_id}] Starting bucket creation: {bucket_name}")
    
    try:
        asyncio.run(update_job_status(job_id, "processing"))
        
        logger.info(f"[Job {job_id}] Initializing Akave SDK...")
        sdk = get_akave_sdk()
        ipc = sdk.ipc()
        
        logger.info(f"[Job {job_id}] Checking if bucket exists...")
        existing_bucket = ipc.view_bucket(None, bucket_name)
        
        if existing_bucket:
            logger.info(f"[Job {job_id}] Bucket already exists")
            asyncio.run(update_job_status(
                job_id,
                "completed",
                tx_hash="existing",
                error=None
            ))
            sdk.close()
            return {"status": "completed", "message": "Bucket already exists"}
        
        # Create bucket
        logger.info(f"[Job {job_id}] Creating bucket on Akave...")
        result = ipc.create_bucket(None, bucket_name)
        
        logger.info(f"[Job {job_id}] Bucket created successfully!")
        logger.info(f"[Job {job_id}] Transaction ID: {result.id}")
        
        asyncio.run(update_job_status(
            job_id,
            "completed",
            tx_hash=result.id,
            error=None
        ))
        
        sdk.close()
        
        return {
            "status": "completed",
            "bucket_name": bucket_name,
            "tx_hash": result.id
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Job {job_id}] Bucket creation failed: {error_msg}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"[Job {job_id}] Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        # Maximum retries, mark as failed now
        asyncio.run(update_job_status(
            job_id,
            "failed",
            tx_hash=None,
            error=error_msg
        ))
        
        raise
