from pyrogram import Client, filters
from pyrogram.types import Message
import os
import asyncio

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本22** 已启动\n发图片时我会自动按组提取**每组第一张**的链接")

last_message_time = 0
current_group = []

@app.on_message(filters.media)
async def collect_media(client, message: Message):
    global last_message_time, current_group
    
    import time
    now = time.time()
    
    # 如果间隔超过 8 秒，认为是新的一组
    if now - last_message_time > 8:
        if current_group:
            await send_group_links(client, message)
        current_group = []
    
    current_group.append(message)
    last_message_time = now

async def send_group_links(client, message):
    global current_group
    if not current_group:
        return
    
    links = []
    for i, msg in enumerate(current_group):
        if msg.photo or msg.video or msg.document:
            link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.id}"
            links.append(f"**第 {len(links)+1} 组** → {link}")
    
    if links:
        text = "📸 **提取完成**（每组只取第一张）\n\n" + "\n".join(links)
        await message.reply(text)
    
    current_group = []

print("✅ 版本22 已启动 - 按组提取第一张链接")
app.run()
