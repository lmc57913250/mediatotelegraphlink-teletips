from pyrogram import Client, filters
from pyrogram.types import Message
import os

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

@app.on_message(filters.command("id"))
async def show_id(client, message: Message):
    chat_id = message.chat.id
    await message.reply(f"**当前聊天 ID：**\n`{chat_id}`\n\n类型：{message.chat.type}")

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("发送 /id 查看当前聊天ID")

print("调试版已启动，发送 /id 测试")
app.run()
