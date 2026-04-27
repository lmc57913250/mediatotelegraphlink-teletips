from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
import re

# 1. 先定义 app
app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

states = {}
user_current_group = {}
bot_groups = {}

keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")],
    [KeyboardButton("刷新群组列表")]
], resize_keyboard=True)

# 2. 然后定义装饰器
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    # ... 代码

@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    # ... 代码

print("✅ 机器人已启动")
app.run()
