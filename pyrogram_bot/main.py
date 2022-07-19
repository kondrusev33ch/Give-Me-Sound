"""
Reference:
    https://github.com/MR-JINN-OF-TG/Song-Downloader/blob/main/bot.py
"""

from __future__ import unicode_literals

from pyrogram import Client, filters
from pyrogram.types import Message
from database import Database

import os
import asyncio
import aiohttp
import yt_dlp

# Globals
DB = Database()
DURATION_LIMIT = 230  # minutes
GREETINGS_STICKER = "CAACAgIAAxkBAAEV1v1iyrxsNVrlxCNEi6GyMChcHr5BVAACuxAAAiY-6ErCecbdBCCJrCkE"  # pepe
START_TEXT = """`Hey {}! 
Send me YT link to the video, you want to get the sound of, and I will return an audio file of this video.
It may take some time (depends of the video length). 
Maximum length of the video is 3 hours and 50 minutes.`
"""

# Youtube downloader options
YDL_OPTIONS = {"format": "bestaudio/best",
               "prefer_ffmpeg": True,
               "geo_bypass": True,
               "nocheckcertificate": True,
               "quiet": True,
               "outtmpl": "%(id)s.mp3",
               "postprocessors": [{"key": "FFmpegExtractAudio",
                                   "preferredcodec": "mp3",
                                   "preferredquality": "192"}]}

# Init bot client. All keys can be obtained here https://my.telegram.org/auth?to=apps
BOT = Client("Audio Downloader Bot",
             bot_token=os.environ.get("BOT_TOKEN"),
             api_id=int(os.environ.get("API_ID")),
             api_hash=os.environ.get("API_HASH"))


async def user_in_db(u_id: int) -> bool:
    """
    Function to check if user is in database, and register if user is not in database.
    :param u_id:  telegram user identifier number.
    :return: is user registered in database.
    """

    if not await DB.is_user_exist(u_id):
        await DB.add_user(u_id)

    return await DB.is_user_exist(u_id)


@BOT.on_message(filters.private & filters.command(["start"]))
async def start_message(client, message: Message):
    """
    Instructions to do on user message "/start".
    :param client: default argument, that we do not need here.
    :param message: telegram respond with all needed information.
    :return: none.
    """

    await user_in_db(message.from_user.id)  # check user in db
    await message.reply_sticker(GREETINGS_STICKER)  # send sticker
    await message.reply_text(text=START_TEXT.format(message.from_user.mention),  # send information message
                             disable_web_page_preview=True)


@BOT.on_message(filters.private & filters.command(["status"]))
async def status(client, message: Message):
    """
    Instructions to do on user message "/status"
    :param client: default argument, that we do not need here.
    :param message: telegram respond with all needed information.
    :return: none.
    """

    await user_in_db(message.from_user.id)  # check user in db
    total_users = await DB.total_users_count()  # get amount of bot users
    text = f"**GMS Status\nTotal users hit start:** `{total_users}`"
    await message.reply_text(text=text,  # send status message
                             disable_web_page_preview=True)


@BOT.on_message(filters.text & filters.private)
async def yt_sound(client, message: Message):
    """
    Main function that processes all text messages from the user.
    :param client: bot client.
    :param message: telegram respond with all needed information.
    :return: none.
    """

    u_id = message.from_user.id  # get user identifier

    if not await user_in_db(u_id):  # check user exist
        await message.reply_text("**[ ! ]** Error, cannot add you to the user list...")
        return

    if await DB.get_is_downloading_status(u_id):  # check "is downloading" status
        await message.reply_text("**[ ! ]** Another download is in progress, try again after sometime...")
        return

    url = message.text  # get message text from the user

    pablo = await client.send_message(  # inform the user that his request is being processed
        message.chat.id,
        f"**[ i ]** Finding {url} from youtube servers. Please wait...")

    # Chek, is the text a link
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                status_code = resp.status
        if not url or status_code != 200:
            raise Exception('Invalid Link')
    except Exception as _:
        await pablo.edit(f"**[ ! ]** {url} is **invalid**.")
        return

    # Download an mp3 from the YouTube video
    try:
        await DB.update_is_downloading_status(u_id, True)  # change "is downloading" status
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, False)
            duration = round(info["duration"] / 60)

            if duration > DURATION_LIMIT:  # check for duration limit
                await pablo.edit(
                    f"**[ ! ]** Video duration is too long.\nVideo: {duration} min\nLimit: {DURATION_LIMIT} min")
                await DB.update_is_downloading_status(u_id, False)
                return

            await pablo.edit(f"""**[ i ]** Downloading **"{info['title']}"**\nPlease wait...""")
            ydl_data = ydl.extract_info(url, download=True)  # download file

    except Exception as ex:
        await pablo.edit(f"**[ ! ]** Failed to download\n`{ex}`")
        await DB.update_is_downloading_status(u_id, False)
        return

    file_name = f"{ydl_data['id']}.mp3"
    caption = f"**Title:** `{ydl_data['title']}`\n" + \
              f"**Link:** {url}\n" \
              f"**Source:** `{ydl_data['channel']}`"

    # Send audio file to the user with extra information
    try:
        with open(file_name, "rb") as af:
            await client.send_audio(
                message.chat.id,
                audio=af,
                duration=ydl_data["duration"],
                file_name=ydl_data["title"],
                performer=ydl_data['channel'],
                caption=caption)
    except Exception as ex:
        await pablo.edit(f"**[ ! ]** Failed to upload\n`{ex}`")

    await pablo.delete()
    await DB.update_is_downloading_status(u_id, False)

    # Delete downloaded mp3 file from the disk
    if os.path.exists(file_name):
        os.remove(file_name)


if __name__ == '__main__':
    BOT.run()
