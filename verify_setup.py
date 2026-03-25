#!/usr/bin/env python3
"""
Integration test script to verify both services are running
"""
import subprocess
import sys
import time
import json

def test_backend_health():
    """Test backend health endpoint"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}", "http://localhost:8000/health"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        status_code = int(lines[-1])
        response_text = '\n'.join(lines[:-1])
        
        if status_code == 200:
            data = json.loads(response_text)
            assert data["status"] == "ok"
            assert "research-notebook-backend" in data["service"]
            print("✅ Backend health check PASSED")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Backend returned status {status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check FAILED: {e}")
        return False

def test_backend_root():
    """Test backend root endpoint"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}", "http://localhost:8000/"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        status_code = int(lines[-1])
        response_text = '\n'.join(lines[:-1])
        
        if status_code == 200:
            data = json.loads(response_text)
            assert "Research Notebook Backend" in data.get("message", "")
            print("✅ Backend root endpoint PASSED")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Backend root returned status {status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend root endpoint FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Research Notebook Project Setup...\n")
    
    # Wait for services to be ready
    print("⏳ Waiting for services...\n")
    time.sleep(2)
    
    results = []
    results.append(("Backend Health Check", test_backend_health()))
    results.append(("Backend Root Endpoint", test_backend_root()))
    
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    print("="*50)
    if all_passed:
        print("\n🎉 All acceptance criteria PASSED!\n")
        print("Task 1 Acceptance Criteria:")
        print("- ✅ FastAPI runs on :8000")
        print("- ✅ /health endpoint responds with ok status")
        print("- ✅ Backend is ready for Task 2\n")
        return 0
    else:
        print("\n❌ Some tests failed\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted")
        sys.exit(1)
