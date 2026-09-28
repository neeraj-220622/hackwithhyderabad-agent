"""
scripts/test_hindsight.py
-------------------------
Live smoke-test for the Hindsight memory service.

Run from the project root with venv active:

    python scripts/test_hindsight.py

Behaviour:
- If Hindsight is configured   -> connects, stores a unique test memory, recalls it, checks the result.
- If Hindsight is unconfigured -> prints setup instructions and exits cleanly.
"""

import sys
import os
import uuid
import time
import asyncio

# Ensure the project root is on sys.path so `backend.*` imports work.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import config
from backend.memory.hindsight import HindsightMemory, HindsightConfigError, HindsightMemoryError

SEP = '-' * 56

async def run_test() -> None:
    print(SEP)
    print('  HackwithHyderabad Agent -- Hindsight Memory Test')
    print(SEP)
    url_status = 'SET [OK]' if config.HINDSIGHT_URL else 'NOT SET [MISSING]'
    print(f'  Hindsight URL : {url_status}')
    print(SEP)

    if not config.HINDSIGHT_URL:
        print()
        print('  [SKIP] HINDSIGHT_URL is not configured.')
        print()
        print('  To run the live test:')
        print('  1. Open .env')
        print('  2. Set HINDSIGHT_URL=<your Hindsight server URL>')
        print('  3. Run this script again.')
        print()
        print('  Implementation is ready -- live test skipped.')
        print(SEP)
        sys.exit(0)

    # Unique test marker
    timestamp = int(time.time())
    unique_marker = f"HACKWITHHYDERABAD_HINDSIGHT_TEST_2026_{timestamp}"
    test_statement = f"The project team is testing Hindsight memory. Test marker: {unique_marker}"
    test_query = "What test marker was stored by the project team?"
    bank_id = "hackathon-test"
    
    print()
    print(f'  Bank ID       : {bank_id}')
    print(f'  Unique Marker : {unique_marker}')
    print()

    try:
        memory = HindsightMemory()
    except HindsightConfigError as exc:
        print(f'  [FAIL] {exc}')
        print(SEP)
        sys.exit(1)

    try:
        # 1. Store
        print('  -> Storing memory...')
        await memory.remember(bank_id=bank_id, content=test_statement)
        print('  -> Memory stored.')
    except HindsightMemoryError as exc:
        print(f'  [FAIL] Could not connect to Hindsight at {config.HINDSIGHT_URL}')
        print(f'         Details: {exc}')
        print(SEP)
        sys.exit(1)

    try:
        # 2. Recall
        print(f'  -> Recalling memory with query: "{test_query}"')
        results = await memory.recall(bank_id=bank_id, query=test_query)
    except HindsightMemoryError as exc:
        print(f'  [FAIL] Could not connect to Hindsight at {config.HINDSIGHT_URL}')
        print(f'         Details: {exc}')
        print(SEP)
        sys.exit(1)

    results_str = str(results)
    print()
    print(f'  Recall Results Snippet:\n  {results_str[:500]}...')
    print()

    # Verify that the unique marker appears somewhere in the returned recall response
    if unique_marker in results_str:
        print(f'  [PASS] Hindsight store + recall verified')
        print(SEP)
        sys.exit(0)
    else:
        print(f'  [FAIL] Hindsight recall did not return the stored marker')
        print(SEP)
        sys.exit(1)


def main() -> None:
    asyncio.run(run_test())

if __name__ == '__main__':
    main()
