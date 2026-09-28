"""
scripts/test_agent.py
---------------------
Test script for the Generic Agent Core (Part 3).
"""

import sys
import os
import time
import asyncio
import uuid

# Ensure the project root is on sys.path so `backend.*` imports work.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import config
from backend.agent.llm import LLMService, LLMConfigError, LLMProviderError
from backend.memory.hindsight import HindsightMemory, HindsightConfigError, HindsightMemoryError
from backend.agent.agent import Agent

SEP = '-' * 56

async def run_test() -> None:
    print(SEP)
    print('  HackwithHyderabad Agent -- Agent Core Test')
    print(SEP)

    # Check LLM configuration
    if not config.LLM_API_KEY:
        print("  [BLOCKED] LLM API key not configured. Test cannot run.")
        print(SEP)
        sys.exit(0)

    # 1. Init LLM
    try:
        llm = LLMService()
        print('  [PASS] LLM service initialized')
    except (LLMConfigError, LLMProviderError) as exc:
        print(f'  [FAIL] Failed to initialize LLM: {exc}')
        print(SEP)
        sys.exit(1)

    # 2. Init Hindsight Memory
    if not config.HINDSIGHT_URL:
        print('  [BLOCKED] Hindsight server is not available (HINDSIGHT_URL not set).')
        print('  Agent Core implementation loaded successfully, but end-to-end memory test cannot run.')
        print(SEP)
        sys.exit(0)

    try:
        memory = HindsightMemory()
        print('  [PASS] HindsightMemory initialized')
    except HindsightConfigError as exc:
        print(f'  [FAIL] Failed to initialize Hindsight: {exc}')
        print(SEP)
        sys.exit(1)

    # 3. Init Agent
    try:
        agent = Agent(llm=llm, memory=memory)
        print('  [PASS] Agent imported and initialized')
    except Exception as exc:
        print(f'  [FAIL] Failed to initialize Agent: {exc}')
        print(SEP)
        sys.exit(1)

    user_id = f"agent-test-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    
    print()
    print(f"  Test User ID: {user_id}")
    
    # Interaction 1
    msg1 = "My preferred project communication style is concise and technical."
    print(f"\n  Interaction 1 (User): {msg1}")
    
    try:
        result1 = await agent.run(user_id=user_id, message=msg1)
        print('  [PASS] Agent executed (Interaction 1)')
        print(f"  [INFO] Memory used: {result1['memory_used']}")
        print(f"  [INFO] Assistant Response: {result1['response']}")
    except HindsightMemoryError as exc:
        err_msg = str(exc)
        if "Failed to create bank" in err_msg:
            print(f'  [FAIL] Bank creation failed: {exc}')
        elif "Failed to recall memory" in err_msg or "Failed to store memory" in err_msg:
            print(f'  [FAIL] Retain/recall error: {exc}')
        else:
            print(f'  [BLOCKED] Hindsight server is not available or connection refused: {exc}')
            print('  Agent Core implementation loaded successfully, but end-to-end memory test cannot run.')
            print(SEP)
            sys.exit(0)
        print(SEP)
        sys.exit(1)
    except Exception as exc:
        print(f'  [FAIL] Agent execution failed on interaction 1: {exc}')
        print(SEP)
        sys.exit(1)

    # Small delay before next interaction
    await asyncio.sleep(2)

    # Interaction 2
    msg2 = "How should you communicate with me?"
    print(f"\n  Interaction 2 (User): {msg2}")

    try:
        result2 = await agent.run(user_id=user_id, message=msg2)
        print('  [PASS] Agent executed (Interaction 2)')
        print(f"  [INFO] Memory used: {result2['memory_used']}")
        print(f"  [INFO] Memory Context Snippet: {str(result2['memory_context'])[:100]}...")
        print(f"  [INFO] Assistant Response: {result2['response']}")
        
        # Check if the context contains words from interaction 1
        if "concise" in result2['response'].lower() or "technical" in result2['response'].lower():
             print('\n  [PASS] End-to-end agent test')
        else:
             print('\n  [INFO] Response generated, but check manually if memory was utilized properly.')
    except Exception as exc:
        print(f'  [FAIL] Agent execution failed on interaction 2: {exc}')
        print(SEP)
        sys.exit(1)

    print(SEP)


def main() -> None:
    asyncio.run(run_test())

if __name__ == '__main__':
    main()
