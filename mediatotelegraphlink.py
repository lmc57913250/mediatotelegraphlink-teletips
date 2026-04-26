from pyrogram import Client, filters
from pyrogram.types import Message
from telegraph import Telegraph
import os
import asyncio

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本20** 已启动\n**使用方法**：直接在私聊或群里发图片/视频，然后发送 /telegraph")

@app.on_message(filters.command("telegraph"))
async def make_telegraph(client, message: Message):
    # 收集最近回复或连续的消息中的媒体
    messages = []
    if message.reply_to_message:
        messages.append(message.reply_to_message)
    
    # 如果没有回复，就收集最近几条
    if not messages:
        async for msg in client.get_chat_history(message.chat.id, limit=30):
            if msg.media:
                messages.append(msg)
            if len(messages) >= 30:
                break

    if not messages:
        return await message.reply("未找到媒体，请发图片/视频后发送 /telegraph")

    await message.reply(f"🔄 版本20 - 找到 {len(messages)} 条媒体，正在生成 Telegraph...")

    try:
        urls = []
        for m in messages:
            if not m.media:
                continue
            try:
                # 尝试获取文件并上传
                file = await m.download(in_memory=True)
                file_bytes = file.getvalue() if hasattr(file, 'getvalue') else file.read() if hasattr(file, 'read') else file
                uploaded = upload_file(file_bytes)
                urls.append(f"https://telegra.ph{uploaded[0]}")
                await asyncio.sleep(0.8)
            except:
                continue

        telegraph = Telegraph()
        telegraph.create_account(short_name="COSER")

        html = "<h1>COSER 写真</h1><br>"
        for url in urls:
            if url.endswith(('.jpg','.jpeg','.png','.gif')):
                html += f'<img src="{url}"><br><br>'
            else:
                html += f'<video src="{url}" controls></video><br><br>'

        page = telegraph.create_page(title="COSER 写真", html_content=html, author_name="COSER Archive")

        await message.reply(f"🎉 **生成完成！**\n\n🔗 {page['url']}")

    except Exception as e:
        await message.reply(f"❌ 出错: {str(e)}")

print("✅ 版本20 已启动")
app.run()
