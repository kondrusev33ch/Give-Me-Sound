import os
import datetime
import motor.motor_asyncio

DB_URI = os.environ.get("DB_URI")
DB_NAME = os.environ.get("DB_NAME")


class Database:
    def __init__(self):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.db = self._client[DB_NAME]
        self.d_col = self.db.users

    @staticmethod
    def new_user(u_id: int):
        return {"id": u_id, "is_downloading": False, "join_date": datetime.date.today().isoformat()}

    async def add_user(self, u_id: int):
        user = self.new_user(u_id)
        await self.d_col.insert_one(user)

    async def is_user_exist(self, u_id) -> bool:
        user = await self.d_col.find_one({"id": int(u_id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.d_col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.d_col.find({})
        return all_users

    async def delete_user(self, u_id: int):
        await self.d_col.delete_many({"id": u_id})

    async def get_is_downloading_status(self, u_id: int):
        status = await self.d_col.find_one({"id": u_id})
        return status["is_downloading"]

    async def update_is_downloading_status(self, u_id: int, status: bool):
        await self.d_col.update_one({"id": u_id}, {"$set": {"is_downloading": status}})

if __name__ == '__main__':
    pass
