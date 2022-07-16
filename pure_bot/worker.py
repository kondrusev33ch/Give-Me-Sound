import asyncio
from client import TgClient


# ======================================================================================================================
class Worker:
    def __init__(self, token: str, queue: asyncio.Queue, concurrent_workers: int):
        self.tg_client = TgClient(token)
        self.queue = queue
        self.concurrent_workers = concurrent_workers
        self._tasks: List[asyncio.Task] = []

    async def handle_update(self, upd):
        """
        Use data from the message to generate answer.
        :param upd: user message.
        :return: none.
        """

        user_id = upd["message"]["from"]["id"]
        chat_id = upd["message"]["chat"]["id"]
        url = upd["message"]["text"]
        await self.tg_client.get_audio(user_id, chat_id, url)

    async def _worker(self):
        """
        Get data from the que and work with it.
        :return: none.
        """

        while True:
            try:
                upd = await self.queue.get()
                await self.handle_update(upd)
            finally:
                self.queue.task_done()

    async def start(self):
        self._tasks = [asyncio.create_task(self._worker()) for _ in range(self.concurrent_workers)]

    async def stop(self):
        await self.queue.join()
        for t in self._tasks:
            t.cancel()
