# Give-Me-Sound (async telegram bot)
**All references are in the code**

## Main Idea
Since in Russia there is no more youtube premium, and listen podcasts or music (from YT) with off screen is imposible, I decided to create a bot to download audio files from the YT and send them back to you, so you can listen them without any restrictions.

## How to use
Send a YT video link to the bot, and you will get an mp3 file of this video.  
<img src="https://user-images.githubusercontent.com/85990934/179368649-1f837715-8f7b-43b9-a50c-4f1a6405b4db.jpg" width="240">

## Realisation
I tried two async versions: 
 - First one is pyrogram_bot (with pyrogram lib obviously).
 - Second is pure_bot, where I tried to communicate with telegram api directly. Some functional is missin (/start, /status and description).

## Problem
yt_dlp can not be async.

## Possible improvements 
 - Use multiprocessing...
