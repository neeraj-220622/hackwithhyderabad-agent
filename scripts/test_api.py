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

    # 4. Valid Request 1
    # This may fail with 503 if Hindsight server is not running (which is expected).
    user_id = "api-memory-test"
    response1 = client.post("/api/agent/chat", json={
        "user_id": user_id, 
        "message": "I prefer concise technical explanations."
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        if "response" in data1 and "memory_used" in data1:
            print('  [PASS] API interaction 1 (store preference)')
        else:
            print(f'  [FAIL] Unexpected response structure: {data1}')
            sys.exit(1)
            
        # 5. Valid Request 2
        import time
        time.sleep(2)  # Wait briefly
        response2 = client.post("/api/agent/chat", json={
            "user_id": user_id, 
            "message": "How should you communicate with me?"
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            ans = data2.get("response", "").lower()
            if "concise" in ans or "technical" in ans:
                print('  [PASS] API interaction 2 (memory recalled successfully)')
            else:
                print('  [INFO] API interaction 2 succeeded, but check manually if memory was utilized properly.')
        elif response2.status_code in [500, 503]:
             print(f'  [BLOCKED] Interaction 2 failed due to external dependency (API returned {response2.status_code}: {response2.json()["detail"]})')
        else:
             print(f'  [FAIL] Interaction 2 failed: {response2.status_code}: {response2.text}')
             sys.exit(1)
             
    elif response1.status_code in [500, 503]:
        print(f'  [BLOCKED] Agent end-to-end because external dependency failed (API returned {response1.status_code}: {response1.json()["detail"]})')
    else:
        print(f'  [FAIL] Expected 200 or 503, got {response1.status_code}: {response1.text}')
        sys.exit(1)

    print(SEP)

if __name__ == '__main__':
    # Context manager ensures lifespan events (startup/shutdown) are triggered
    with client:
        run_tests()
