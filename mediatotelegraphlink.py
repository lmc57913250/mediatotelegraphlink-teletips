from pyrogram import Client, filters
from pyrogram.types import Message
from telegraph import upload_file, Telegraph
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
    await message.reply("✅ 机器人已就绪\n**使用方法**：在讨论组线程里**回复任意一条消息**，然后发送 /telegraph")

@app.on_message(filters.command("telegraph"))
async def make_telegraph(client, message: Message):
    # 使用回复的消息作为起点
    if not message.reply_to_message:
        return await message.reply("❌ 请**回复**线程里的任意一条消息，然后发送 /telegraph")

    thread_id = getattr(message.reply_to_message, 'message_thread_id', None) or getattr(message, 'message_thread_id', 1)

    await message.reply("🔄 正在收集该线程的媒体...")

    try:
        messages = []

        # 从回复的消息开始向上收集（Bot 可用的方式）
        current = message.reply_to_message
        messages.append(current)

        # 尝试收集后续消息（有限次数）
        for _ in range(300):
            if not current.reply_to_message:
                break
            current = await client.get_messages(message.chat.id, current.reply_to_message.id)
            if current.media:
                messages.append(current)

        # 再尝试收集前面的一些消息
        async for msg in client.get_chat_history(message.chat.id, limit=100, offset_id=message.reply_to_message.id):
            if getattr(msg, 'message_thread_id', None) == thread_id and msg.media:
                messages.append(msg)
            if len(messages) > 300:
                break

        messages = list(dict.fromkeys(messages))  # 去重
        messages.sort(key=lambda m: m.date)

        title = "COSER 写真"
        for m in messages:
            if m.text and m.text.strip():
                title = m.text.split('\n')[0][:100]
                break

        await message.reply(f"✅ 找到 {len(messages)} 条媒体，开始上传...")

        urls = []
        for m in messages:
            if not m.media: continue
            try:
                file = await m.download(in_memory=True)
                file_bytes = file.getvalue() if hasattr(file, 'getvalue') else file.read() if hasattr(file, 'read') else file
                uploaded = upload_file(file_bytes)
                urls.append(f"https://telegra.ph{uploaded[0]}")
                await asyncio.sleep(0.7)
            except:
                continue

        telegraph = Telegraph()
        telegraph.create_account(short_name="COSER")

        html = f"<h1>{title}</h1><br>"
        for url in urls:
            if url.endswith(('.jpg','.jpeg','.png','.gif')):
                html += f'<img src="{url}"><br><br>'
            else:
                html += f'<video src="{url}" controls></video><br><br>'

        page = telegraph.create_page(title=title, html_content=html, author_name="COSER Archive")

        await message.reply(f"🎉 **生成完成！**\n\n🔗 {page['url']}")

    except Exception as e:
        await message.reply(f"❌ 出错: {str(e)}")

print("✅ 最终实用版已启动")
app.run()
