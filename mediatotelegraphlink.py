from pyrogram import Client, filters
from pyrogram.types import Message
from telegraph import Telegraph
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
    await message.reply("✅ **版本17** 已启动\n**使用方法**：在讨论组线程里**回复任意一条消息**，然后发送 /telegraph")

@app.on_message(filters.command("telegraph"))
async def make_telegraph(client, message: Message):
    if not message.reply_to_message:
        return await message.reply("❌ 请**回复**线程里任意一条消息，然后发送 /telegraph")

    await message.reply("🔄 版本17 - 正在收集 Telegram 链接...")

    try:
        messages = []
        current = message.reply_to_message
        messages.append(current)

       
