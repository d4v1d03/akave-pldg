-- Database Schema for Akave Platform MVP
-- PostgreSQL 15+

-- Bucket creation jobs table
CREATE TABLE IF NOT EXISTS bucket_jobs (
    id UUID PRIMARY KEY,
    bucket_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- queued, processing, completed, failed
    tx_hash VARCHAR(255),          -- Blockchain transaction hash
    error TEXT,                    -- Error message if failed
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_bucket_jobs_status ON bucket_jobs(status);
CREATE INDEX IF NOT EXISTS idx_bucket_jobs_created ON bucket_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bucket_jobs_bucket_name ON bucket_jobs(bucket_name);

-- Unique constraint on bucket name for completed jobs
CREATE UNIQUE INDEX IF NOT EXISTS idx_bucket_jobs_unique_completed 
ON bucket_jobs(bucket_name) 
WHERE status = 'completed';
