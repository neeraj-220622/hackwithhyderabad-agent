"""
scripts/test_api.py
-------------------
Integration tests for the FastAPI layer (Part 4).
"""

import sys
import os

# Ensure the project root is on sys.path so `backend.*` imports work.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.main import app

# We use the FastAPI TestClient to test the routes without spinning up a real server on a port.
# Note: TestClient does run the lifespan events in newer FastAPI/Starlette versions, 
# so it will attempt to initialize the Agent Core.

client = TestClient(app)

SEP = '-' * 56

def run_tests():
    print(SEP)
    print('  HackwithHyderabad Agent -- FastAPI Test')
    print(SEP)

    # 1. /health
    response = client.get("/api/health")
    if response.status_code == 200 and response.json().get("status") == "ok":
        print('  [PASS] API health')
    else:
        print(f'  [FAIL] API health returned {response.status_code}: {response.text}')
        sys.exit(1)

    # 2. Empty user_id / invalid request
    response = client.post("/api/agent/chat", json={"user_id": "", "message": "hello"})
    if response.status_code in [400, 422]:
        print('  [PASS] Request validation (empty user_id)')
    else:
        print(f'  [FAIL] Expected validation error, got {response.status_code}: {response.text}')
        sys.exit(1)

    # 3. Empty message / invalid request
    response = client.post("/api/agent/chat", json={"user_id": "user1", "message": "   "})
    if response.status_code in [400, 422]:
        print('  [PASS] Request validation (empty message)')
    else:
        print(f'  [FAIL] Expected validation error, got {response.status_code}: {response.text}')
        sys.exit(1)

    # 4. Valid Request
    # This may fail with 503 if Hindsight server is not running (which is expected).
    response = client.post("/api/agent/chat", json={"user_id": "test-user-api", "message": "What is your purpose?"})
    
    if response.status_code == 200:
        data = response.json()
        if "response" in data and "memory_used" in data:
            print('  [PASS] End-to-end agent API')
        else:
            print(f'  [FAIL] Unexpected response structure: {data}')
            sys.exit(1)
    elif response.status_code == 503:
        print('  [BLOCKED] Agent end-to-end because Hindsight server is unavailable')
        print(f'            (API returned 503: {response.json()["detail"]})')
    else:
        print(f'  [FAIL] Expected 200 or 503, got {response.status_code}: {response.text}')
        sys.exit(1)

    print(SEP)

if __name__ == '__main__':
    # Context manager ensures lifespan events (startup/shutdown) are triggered
    with client:
        run_tests()
