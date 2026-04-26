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
collected_firsts = []   # 存储每组的第一张（包括封面）

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本33** 已启动\n1. 频道发封面图\n2. 讨论组发图片（可分多条）\n3. 发完后输入 /telegraph")

# 频道发图 → 封面
@app.on_message(filters.channel & filters.media)
async def set_cover(client, message: Message):
    global current_cover, collected_firsts
    current_cover = message
    collected_firsts = [message]   # 封面作为第一组第一张
    # 默默记录，不回复

# 讨论组发媒体 → 每条消息的第一张记录下来
@app.on_message(filters.media)
async def collect_first(client, message: Message):
    global collected_firsts
    if current_cover and message.chat.type in ["supergroup", "group"]:
        collected_firsts.append(message)   # 每条消息的第一张

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global current_cover, collected_firsts

    if not current_cover:
        return await message.reply("❌ 请先在频道发一张封面图")

    links = []
    for i, msg in enumerate(collected_firsts):
        if msg.photo or msg.video or msg.document:
            link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.id}"
            links.append(f"第 {i+1} 张 → {link}")

    if not links:
        return await message.reply("未找到媒体")

    text = "📸 **提取完成**（封面 + 每组第一张）\n\n" + "\n".join(links)
    await message.reply(text)

    # 清空准备下一组
    current_cover = None
    collected_firsts = []

print("✅ 版本33 已启动")
app.run()
