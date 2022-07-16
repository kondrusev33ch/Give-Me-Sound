import asyncio
from client import TgClient
from typing import Optional


# ======================================================================================================================
class Poller:
    def __init__(self, token: str, queue: asyncio.Queue):
        self.tg_client = TgClient(token)
        self.queue = queue
        self._task: Optional[asyncio.Task] = None

    async def _worker(self):
        offset = 0
        while True:
            res = await self.tg_client.get_updates(offset=offset, timeout=60)  # get all messages from the telegram
            for u in res["result"]:
                offset = u["update_id"] + 1
                print(u)
                self.queue.put_nowait(u)  # put messages to the queue

    async def start(self):
        self._task = asyncio.create_task(self._worker())

    async def stop(self):
        self._task.cancel()
