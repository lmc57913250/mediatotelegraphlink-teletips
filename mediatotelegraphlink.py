from pyrogram import Client, filters
from pyrogram.types import Message
import os

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本21** 已启动\n直接在讨论组里发图片/视频，我会给你 Telegram 链接")

@app.on_message(filters.media)
async def get_link(client, message: Message):
    try:
        # 获取文件直链（Telegram 永久链接）
        if message.photo:
            file_id = message.photo.file_id
            file_type = "图片"
        elif message.video:
            file_id = message.video.file_id
            file_type = "视频"
        elif message.document:
            file_id = message.document.file_id
            file_type = "文件"
        else:
            file_type = "媒体"
            file_id = message.media.file_id if hasattr(message.media, 'file_id') else "未知"

        # 生成可访问链接
        link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.id}"   # 频道讨论组链接

        await message.reply(f"✅ **{file_type} 链接**\n\n🔗 {link}\n\nFile ID: `{file_id}`")
        
    except Exception as e:
        await message.reply(f"❌ 获取链接失败: {str(e)}")

print("✅ 版本21 已启动 - 只提取链接")
app.run()
