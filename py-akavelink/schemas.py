from datetime import datetime
from enum import Enum 
from typing import Optional 

from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    queued = "queued"
    processing="processing"
    completed="completed"
    failed="failed"

class BucketCreateRequest(BaseModel):
    bucket_name: str = Field(..., min_length=3, max_length=255, regex= r'^[a-zA-Z0-9-]+$')
    
class BucketCreateResponse(BaseModel): 
    job_id: str 
    bucket_name: str
    status: JobStatus
    node_response: str 
    
class JobStatusResponse(BaseModel):
    job_id: str
    bucket_name: str
    status: JobStatus
    tx_hash: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime