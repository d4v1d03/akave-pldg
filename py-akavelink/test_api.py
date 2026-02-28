#!/usr/bin/env python3
import requests
import time
import sys

API_BASE = "http://localhost:8000"


def test_health():
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        print("✅ Health check passed")
        print(f"   Response: {response.json()}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False


def test_create_bucket(bucket_name):
    print(f"\n🔍 Creating bucket: {bucket_name}")
    response = requests.post(
        f"{API_BASE}/buckets",
        json={"bucket_name": bucket_name}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Bucket creation job queued")
        print(f"   Job ID: {data['job_id']}")
        print(f"   Status: {data['status']}")
        return data['job_id']
    else:
        print(f"❌ Bucket creation failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_job_status(job_id):
    print(f"\n🔍 Polling job status: {job_id}")
    
    max_attempts = 30  #approx 1 minute of attempts
    for attempt in range(max_attempts):
        response = requests.get(f"{API_BASE}/buckets/jobs/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            print(f"   [{attempt+1}] Status: {status}")
            
            if status == "completed":
                print("✅ Bucket created successfully!")
                print(f"   TX Hash: {data['tx_hash']}")
                return True
            elif status == "failed":
                print(f"❌ Bucket creation failed")
                print(f"   Error: {data.get('error', 'Unknown error')}")
                return False
            
            time.sleep(2)
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    
    print("⏱️  Timeout waiting for job completion")
    return False


def test_list_buckets():
    print("\n🔍 Listing all buckets...")
    response = requests.get(f"{API_BASE}/buckets")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} bucket(s)")
        for bucket in data['buckets']:
            print(f"   - {bucket['name']} (TX: {bucket['tx_hash'][:16]}...)")
        return True
    else:
        print(f"❌ List buckets failed: {response.status_code}")
        return False


def main():
    print("=" * 60)
    print("Akave Platform - API Test Suite")
    print("=" * 60)
    
    if not test_health():
        print("\n❌ Health check failed. Is the API running?")
        print("   Run: docker-compose up -d")
        sys.exit(1)
    
    bucket_name = f"test-bucket-{int(time.time())}"
    job_id = test_create_bucket(bucket_name)
    
    if not job_id:
        print("\n❌ Failed to create bucket job")
        sys.exit(1)
    
    if not test_job_status(job_id):
        print("\n❌ Bucket creation did not complete successfully")
        sys.exit(1)
    
    test_list_buckets()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API. Is it running?")
        print("   Run: docker-compose up -d")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
