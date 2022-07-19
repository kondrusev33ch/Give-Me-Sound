import os
import aiohttp
import yt_dlp
from typing import Optional
from database import Database

# Globals
DURATION_LIMIT = 230  # minutes
OPTIONS = {"format": "bestaudio/best",
           "prefer_ffmpeg": True,
           "geo_bypass": True,
           "nocheckcertificate": True,
           "postprocessors": [{"key": "FFmpegExtractAudio",
                               "preferredcodec": "mp3",
                               "preferredquality": "192"}],
           "outtmpl": "%(id)s.mp3"}
DB = Database()


# ======================================================================================================================
async def user_in_db(u_id: int) -> bool:
    """
    Function to check if user is in database, and register if user is not in database.
    :param u_id:  telegram user identifier number.
    :return: is user registered in database.
    """

    if not await DB.is_user_exist(u_id):
        await DB.add_user(u_id)

    return await DB.is_user_exist(u_id)


# ======================================================================================================================
class TgClient:
    def __init__(self, token: str):
        self.token = token

    def get_url(self, method: str) -> str:
        """
        Generate a link to communicate to the telegram api.
        :param method: you can find all methods here https://core.telegram.org/methods.
        :return: a link.
        """

        return f"https://api.telegram.org/bot{self.token}/{method}"

    async def get_updates(self, offset: Optional[int] = None, timeout: int = 0) -> dict:
        """
        Get the user's message if it was sent to the bot. So it is checking telegram for a new messages.
        :param offset: each message has an id, and increases by 1 each time.
        :param timeout: seconds to wait for a new message.
        :return: message data.
        """

        url = self.get_url("getUpdates")
        params = {}
        if offset:
            params["offset"] = offset
        if timeout:
            params["timeout"] = timeout
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                return await resp.json()

    async def send_message(self, method: str, payload: dict, is_file: bool = False) -> dict:
        """
        Function for communicating with telegram API.
        :param method: you can find all methods here https://core.telegram.org/methods.
        :param payload: parameters to send.
        :param is_file: flag for sending files.
        :return: respond data.
        """

        url = self.get_url(method)
        async with aiohttp.ClientSession() as session:
            args = {"json": payload} if not is_file else {"data": payload}
            async with session.post(url, **args) as resp:
                res_dict = await resp.json()
                return res_dict

    @staticmethod
    async def is_valid_link(link: str) -> bool:
        """
        Check if message text is a valid link.
        :param link: message text.
        :return: valid or not.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                return response.status == 200

    async def get_audio(self, u_id: int, chat_id: int, url: str):
        """
        Function to download and send audio file to the user.
        :param u_id: user identifier for the database.
        :param chat_id: chat identifier, to know where to send audio file.
        :param url: message text.
        :return: none.
        """

        if not await user_in_db(u_id):  # check is user exist
            await self.send_message("sendMessage",
                                    {"chat_id": chat_id,
                                     "text": "[ ! ] Error, cannot add you to the user list..."})
            return

        if await DB.get_is_downloading_status(u_id):  # check "is downloading" status
            await self.send_message("sendMessage",
                                    {"chat_id": chat_id,
                                     "text": "[ i ] Another download is in progress, try again after sometime."})
            return

        if not await self.is_valid_link(url):  # check link is valid
            await self.send_message("sendMessage", {"chat_id": chat_id, "text": f"[ ! ] {url} is not valid"})
            return

        pablo = await self.send_message("sendMessage",  # send information message
                                        {"chat_id": chat_id,
                                         "text": f"[ i ] Finding {url} From Youtube Servers. Please Wait..."})
        message_id = pablo["result"]["message_id"]

        # Download mp3 file from the YouTube video
        try:
            await DB.update_is_downloading_status(u_id, True)
            with yt_dlp.YoutubeDL(OPTIONS) as ytdl:
                info = ytdl.extract_info(url, False)
                duration = round(info["duration"] / 60)

                if duration > DURATION_LIMIT:  # duration limit check
                    await self.send_message("editMessageText",
                                            {"chat_id": chat_id,
                                             "message_id": message_id,
                                             "text": f"[ ! ] Video is longer than {DURATION_LIMIT}" +
                                                     " minute(s) aren't allowed, the provided video is " +
                                                     f"{duration} minute(s)"})

                    await DB.update_is_downloading_status(u_id, False)  # download file
                    return

                await self.send_message("editMessageText",  # update information message
                                        {"chat_id": chat_id,
                                         "message_id": message_id,
                                         "text": "[ i ] Please wait. Downloading in process..."})
                ytdl_data = ytdl.extract_info(url, download=True)

        except Exception as ex:
            await self.send_message("editMessageText",
                                    {"chat_id": chat_id,
                                     "message_id": message_id,
                                     "text": f"[ ! ] Failed To Download\nError: {ex}"})
            await DB.update_is_downloading_status(u_id, False)
            return

        # Send audio file to the user
        file_name = f"{ytdl_data['id']}.mp3"
        try:
            with open(file_name, "rb") as mp3:
                payload = {"chat_id": str(chat_id),
                           "performer": ytdl_data["channel"],
                           "audio": mp3.read(),
                           "title": ytdl_data["title"],
                           "duration": str(ytdl_data["duration"]),
                           "parse_mode": "HTML"}
                await self.send_message("sendAudio",
                                        payload=payload,
                                        is_file=True)
                await self.send_message("editMessageText",  # update info message
                                        {"chat_id": chat_id,
                                         "message_id": message_id,
                                         "text": f"[ + ] {ytdl_data['title']}"})
        except Exception as ex:
            await self.send_message("editMessageText",
                                    {"chat_id": chat_id,
                                     "message_id": message_id,
                                     "text": f"[ ! ] Failed To Download\nError: {ex}"})

        await DB.update_is_downloading_status(u_id, False)  # update "is downloading" status
        if os.path.exists(file_name):  # remove mp3 file
            os.remove(file_name)


# ======================================================================================================================
if __name__ == '__main__':
    pass
