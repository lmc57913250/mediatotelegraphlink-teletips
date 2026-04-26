from pyrogram import Client, filters
from pyrogram.types import Message
import os
import asyncio
import time

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本23** 已启动\n发图片时，我会**只提取每组的第一张链接**")

last_time = 0
current_group_first = None

@app.on_message(filters.media)
async def collect_first_of_group(client, message: Message):
    global last_time, current_group_first
    
    now = time.time()
    
    # 超过8秒视为新的一组
    if now - last_time > 8:
        if current_group_first:
            link = f"https://t.me/c/{str(current_group_first.chat.id)[4:]}/{current_group_first.id}"
            await current_group_first.reply(f"📸 **第1张链接**\n{link}")
        
        current_group_first = message   # 新组的第一张
    
    else:
        # 同一组，不做任何回复，只记录第一张
        if current_group_first is None:
            current_group_first = message
    
    last_time = now

print("✅ 版本23 已启动 - 只提取每组第一张链接")
app.run()
