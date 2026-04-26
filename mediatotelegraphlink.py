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
    await message.reply("✅ **版本30** 已启动\n1. 在频道发一张封面图（任意图片）\n2. 在讨论组线程发图片\n3. 发完后输入 /telegraph")

# 任何频道里的媒体都视为封面
@app.on_message(filters.channel & filters.media)
async def set_cover(client, message: Message):
    global current_cover, collected_media
    current_cover = message
    collected_media = []
    await message.reply("📌 **封面已记录**，现在可以在讨论组线程发图片了")

# 收集讨论组里的媒体
@app.on_message(filters.media)
async def collect_media(client, message: Message):
    global collected_media
    if message.chat.type in ["supergroup", "group"]:
        if current_cover:
            collected_media.append(message)

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global current_cover, collected_media

    if not current_cover:
        return await message.reply("❌ 请先在**频道**发一张封面图")

    all_media = [current_cover] + collected_media

    links = []
    for i, msg in enumerate(all_media):
        if msg.photo or msg.video or msg.document:
            link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.id}"
            links.append(f"第 {i+1} 张 → {link}")

    if not links:
        return await message.reply("未找到媒体")

    text = "📸 **提取完成**（封面 + 讨论组媒体）\n\n" + "\n".join(links)
    await message.reply(text)

    # 清空准备下一组
    current_cover = None
    collected_media = []

print("✅ 版本30 已启动")
app.run()
