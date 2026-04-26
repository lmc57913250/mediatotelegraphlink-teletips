from pyrogram import Client, filters
from pyrogram.types import Message
import os

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

current_cover = None
collected_media = []

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本38** 已启动\n1. 频道发封面图\n2. 讨论组发图片\n3. 发完后输入 /telegraph")

# 任何媒体消息都检查
@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global current_cover, collected_media

    chat_id_str = str(message.chat.id)

    # 频道消息 → 记录为封面
    if chat_id_str.startswith('-100'):
        current_cover = message
        collected_media = []
        return   # 默默记录

    # 讨论组消息 → 收集
    if current_cover:
        collected_media.append(message)

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global current_cover, collected_media

    if not current_cover:
        return await message.reply("❌ 请先在频道发一张封面图")

    all_media = [current_cover] + collected_media

    links = []
    for i, msg in enumerate(all_media):
        if msg.photo or msg.video or msg.document:
            link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.id}"
            links.append(f"第 {i+1} 张 → {link}")

    if not links:
        return await message.reply("未找到媒体")

    text = "📸 **提取完成**（封面 + 每组第一张）\n\n" + "\n".join(links)
    await message.reply(text)

    # 清空
    current_cover = None
    collected_media = []

print("✅ 版本38 已启动")
app.run()
