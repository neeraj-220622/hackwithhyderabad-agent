import asyncio
from hindsight_client import Hindsight

c = Hindsight('http://localhost:8888')

async def test():
    try:
        await c.aget_bank_config('test1234')
    except Exception as e:
        print(repr(e), getattr(e, 'status', None))
        import traceback
        traceback.print_exc()

asyncio.run(test())
