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
collected_firsts = []   # 只存每组第一张

DISCUSSION_ID = -1002208209157

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本44** 已启动\n只提取每组第一张（讨论组统一链接）")

# 在讨论组处理媒体
@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global current_cover, collected_firsts

    if message.chat.id != DISCUSSION_ID:
        return

    if current_cover is None:
        # 第一条 = 封面
        current_cover = message
        collected_firsts = [message]
        print(f"[DEBUG] 封面记录: {message.id}")
    else:
        # 后续每条消息只记录第一张（即这条消息本身）
        collected_firsts.append(message)
        print(f"[DEBUG] 收集第 {len(collected_firsts)} 组第一张: {message.id}")

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global current_cover, collected_firsts

    if not current_cover:
        return await message.reply("❌ 请先在频道发一张封面图")

    links = []
    for i, msg in enumerate(collected_firsts):
        if msg.photo or msg.video or msg.document:
            link = f"https://t.me/c/{str(DISCUSSION_ID)[4:]}/{msg.id}"
            links.append(f"第 {i+1} 张 → {link}")

    text = f"📸 **提取完成**（共 {len(links)} 组第一张）\n\n" + "\n".join(links)
    await message.reply(text)

    # 清空
    current_cover = None
    collected_firsts = []

print("✅ 版本44 已启动（每组第一张模式）")
app.run()
