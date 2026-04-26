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

DISCUSSION_ID = -1002208209157   # 你的讨论组ID

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本43** 已启动\n所有链接统一从讨论组提取\n1. 频道发封面（会自动转到讨论组）\n2. 讨论组继续发图片\n3. 发完后输入 /telegraph")

# 在讨论组里收集媒体
@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global current_cover, collected_media

    if message.chat.id != DISCUSSION_ID:
        return

    if current_cover is None:
        # 第一条媒体 = 封面
        current_cover = message
        collected_media = []
        print(f"[DEBUG] 封面已记录 (讨论组消息ID: {message.id})")
    else:
        # 后续媒体
        collected_media.append(message)
        print(f"[DEBUG] 收集内容图片 (消息ID: {message.id})")

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global current_cover, collected_media

    if not current_cover:
        return await message.reply("❌ 请先在频道发一张封面图（会自动出现在讨论组）")

    all_media = [current_cover] + collected_media

    links = []
    for i, msg in enumerate(all_media):
        if msg.photo or msg.video or msg.document:
            # 统一使用讨论组ID生成链接
            link = f"https://t.me/c/{str(DISCUSSION_ID)[4:]}/{msg.id}"
            links.append(f"第 {i+1} 张 → {link}")

    text = f"📸 **提取完成**（共 {len(links)} 张，全部来自讨论组）\n\n" + "\n".join(links)
    await message.reply(text)

    # 清空准备下一组
    current_cover = None
    collected_media = []

print("✅ 版本43 已启动（统一讨论组链接）")
app.run()
