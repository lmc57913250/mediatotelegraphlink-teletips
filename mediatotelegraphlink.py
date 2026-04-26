from pyrogram import Client, filters
from pyrogram.types import Message
import os

app = Client(
    "DebugBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

# 任何消息都打印调试信息
@app.on_message()
async def any_message(client, message: Message):
    print(f"[DEBUG] 收到消息 - Chat:{message.chat.id} Thread:{message.message_thread_id} Text:{message.text}")

# 专门捕捉 /telegraph
@app.on_message(filters.command("telegraph"))
async def telegraph_cmd(client, message: Message):
    print(f"[DEBUG] 成功触发 /telegraph 命令！ Thread ID: {message.message_thread_id}")
    await message.reply("✅ Bot 已收到 /telegraph 命令！\n\n正在尝试收集媒体...")

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("调试版 Bot 已启动\n直接在讨论组线程发 /telegraph 测试")

print("🚀 极简调试版 Bot 已启动")
app.run()
