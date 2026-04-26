from pyrogram import Client, filters
from pyrogram.types import Message
import os
import time

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

current_cover = None
collected_firsts = []
last_media_time = 0
DISCUSSION_ID = -1002208209157

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本49** 已启动\n小于 0.1秒 = 同一组，大于 0.1秒 = 新组")

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global current_cover, collected_firsts, last_media_time

    if message.chat.id != DISCUSSION_ID:
        return

    now = time.time()

    if current_cover is None:
        current_cover = message
        collected_firsts = [message]
        last_media_time = now
        print(f"[DEBUG] 封面: {message.id}")
    else:
        interval = now - last_media_time
        if interval > 0.1:          # 大于 0.1 秒 = 新的一组
            collected_firsts.append(message)
            print(f"[DEBUG] 新组第一张 (间隔 {interval:.2f}秒): {message.id}")
        else:
            print(f"[DEBUG] 同一组，忽略 (间隔 {interval:.2f}秒): {message.id}")
        
        last_media_time = now

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global current_cover, collected_firsts

    if not current_cover:
        return await message.reply("❌ 请先发封面")

    links = []
    for i, msg in enumerate(collected_firsts):
        link = f"https://t.me/c/{str(DISCUSSION_ID)[4:]}/{msg.id}"
        links.append(f"第 {i+1} 张 → {link}")

    text = f"📸 **提取完成**（共 {len(links)} 组第一张）\n\n" + "\n".join(links)
    await message.reply(text)

    current_cover = None
    collected_firsts = []
    last_media_time = 0

print("✅ 版本49 已启动（0.1秒严格区分）")
app.run()
