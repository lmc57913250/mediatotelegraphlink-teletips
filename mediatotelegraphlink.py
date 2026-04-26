from pyrogram import Client, filters
from pyrogram.types import Message
import os

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

collected_media = []   # 临时存储最近收到的媒体消息

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本22** 已启动\n发完图片后，输入 /telegraph 我会提取**每条消息的第一张链接**")

@app.on_message(filters.media)
async def collect_media(client, message: Message):
    global collected_media
    collected_media.append(message)
    # 只保留最近100条，防止内存占用
    if len(collected_media) > 100:
        collected_media = collected_media[-100:]

@app.on_message(filters.command("telegraph"))
async def extract_first_of_each(client, message: Message):
    global collected_media
    if not collected_media:
        return await message.reply("目前没有收集到媒体，请先发图片")

    first_links = []
    for msg in collected_media:
        if msg.photo or msg.video or msg.document:
            link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.id}"
            first_links.append(link)

    if not first_links:
        return await message.reply("未找到媒体")

    text = "📸 **提取完成**（每条消息只取第一张）\n\n" + "\n".join([f"第{i+1}条 → {link}" for i, link in enumerate(first_links)])

    await message.reply(text)
    
    # 清空缓存，准备下一次
    collected_media = []

print("✅ 版本22 已启动 - 只提取每组第一张")
app.run()
