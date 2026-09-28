"""
scripts/test_llm.py
-------------------
Smoke-test for the LLM service.

Run from the project root with venv active:

    python scripts/test_llm.py

Behaviour:
- If LLM_API_KEY is set   -> makes a real API call and checks the response.
- If LLM_API_KEY is unset -> prints setup instructions and exits cleanly (no crash).
"""

import sys
import os

# Ensure the project root is on sys.path so `backend.*` imports work.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import config
from backend.agent.llm import LLMService, LLMConfigError, LLMProviderError

TEST_PROMPT = 'Reply with exactly: LLM_TEST_OK'
EXPECTED    = 'LLM_TEST_OK'
SEP         = '-' * 56


def main() -> None:
    print(SEP)
    print('  HackwithHyderabad Agent -- LLM Service Smoke Test')
    print(SEP)
    print(f'  Provider : {config.LLM_PROVIDER}')
    print(f'  Model    : {config.LLM_MODEL}')
    key_status = 'SET [OK]' if config.LLM_API_KEY else 'NOT SET [MISSING]'
    print(f'  API Key  : {key_status}')
    print(SEP)

    if not config.LLM_API_KEY:
        print()
        print('  [!] LLM_API_KEY is not configured.')
        print()
        print('  To run the live test:')
        print('  1. Copy .env.example -> .env')
        print('  2. Set LLM_PROVIDER=groq')
        print('  3. Set LLM_MODEL=llama-3.3-70b-versatile')
        print('  4. Set LLM_API_KEY=<your Groq key from console.groq.com>')
        print('  5. Run this script again.')
        print()
        print('  Implementation is ready -- live test skipped.')
        print(SEP)
        sys.exit(0)

    print()
    print(f'  Prompt: "{TEST_PROMPT}"')
    print()

    try:
        llm = LLMService()
        response = llm.generate(TEST_PROMPT)
    except (LLMConfigError, LLMProviderError) as exc:
        print(f'  [FAIL] {exc}')
        print(SEP)
        sys.exit(1)

    print(f'  Response: "{response}"')
    print()

    if EXPECTED in response:
        print(f'  [PASS] Response contains "{EXPECTED}"')
        print(SEP)
        sys.exit(0)
    else:
        print(f'  [FAIL] Expected response to contain "{EXPECTED}"')
        print(SEP)
        sys.exit(1)


if __name__ == '__main__':
    main()
