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
    await message.reply("✅ **版本29** 已启动\n1. 在频道发一张封面图\n2. 在讨论组线程发图片\n3. 发完后输入 /telegraph")

# 任何媒体消息都检查
@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global current_cover, collected_media

    # 如果是频道消息，认为是封面
    if message.chat.type == "channel":
        current_cover = message
        collected_media = []
        await message.reply("📌 已记录封面，开始新的一组")
        return

    # 如果是 supergroup（讨论组），收集媒体
    if message.chat.type == "supergroup" or message.chat.type == "group":
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

    text = "📸 **提取完成**（封面 + 讨论组媒体）\n\n" + "\n".join(links)
    await message.reply(text)

    # 清空
    current_cover = None
    collected_media = []

print("✅ 版本29 已启动")
app.run()
