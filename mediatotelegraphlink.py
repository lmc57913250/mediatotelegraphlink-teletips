from pyrogram import Client, filters
from pyrogram.types import Message
import os

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

# 存储当前正在处理的封面和媒体
current_cover = None
collected_media = []

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本26** 已启动\n**使用方法**：\n1. 在频道发一张封面图\n2. 在讨论组线程发图片\n3. 发完后输入 /telegraph")

# 检测频道主帖（封面）
@app.on_message(filters.chat_type.channel & filters.media)
async def detect_cover(client, message: Message):
    global current_cover, collected_media
    current_cover = message
    collected_media = []  # 新封面开始新的一组
    await message.reply("📌 已检测到封面图，开始新的一组收集")

# 收集讨论组线程里的媒体
@app.on_message(filters.media)
async def collect_media(client, message: Message):
    global collected_media
    if message.chat.type == "supergroup":   # 讨论组
        collected_media.append(message)

@app.on_message(filters.command("telegraph"))
async def generate_links(client, message: Message):
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

    text = f"📸 **提取完成**（共 {len(links)} 张，每条取第一张）\n\n" + "\n".join(links)
    await message.reply(text)
    
    # 清空，准备下一组
    current_cover = None
    collected_media = []

print("✅ 版本26 已启动 - 封面 + 讨论组模式")
app.run()
