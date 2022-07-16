"""
References:
    https://habr.com/ru/company/kts/blog/598575/
"""

import datetime
import asyncio
import os

from poller import Poller
from worker import Worker

TOKEN = os.getenv('TOKEN')


# ======================================================================================================================
class Bot:
    def __init__(self, token: str, n: int):
        self.queue = asyncio.Queue()
        self.poller = Poller(token, self.queue)
        self.worker = Worker(token, self.queue, n)

    async def start(self):
        await self.poller.start()
        await self.worker.start()

    async def stop(self):
        await self.poller.stop()
        await self.worker.stop()


# ======================================================================================================================
def run():
    loop = asyncio.get_event_loop()
    bot = Bot(TOKEN, 4)
    try:
        print('Bot has been started')
        loop.create_task(bot.start())
        loop.run_forever()  # endless loop for the bot
    except:  # any exception
        print("\nstopping", datetime.datetime.now())
        loop.run_until_complete(bot.stop())  # graceful exit
        print('bot has been stopped', datetime.datetime.now())


# ======================================================================================================================
if __name__ == '__main__':
    run()
