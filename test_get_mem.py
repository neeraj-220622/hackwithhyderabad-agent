import asyncio
from backend.memory.hindsight import HindsightMemory
async def test():
    m = HindsightMemory()
    await m.ensure_bank('api-memory-test')
    res = await m.get_memories('api-memory-test')
    if res:
        for r in res:
             print("text:", getattr(r, 'text', str(r)))
             print("type:", getattr(r, 'type', str(r)))
    else:
        print("Empty or no response")
    await m.close()
asyncio.run(test())
