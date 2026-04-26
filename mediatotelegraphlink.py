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

# 任何消息都回复（用于调试）
@app.on_message()
async def debug_all(client, message: Message):
    print(f"[DEBUG] 收到消息 | Chat:{message.chat.id} | Thread:{getattr(message, 'message_thread_id', 'None')} | Text:{message.text}")
    if message.text and message.text.strip().lower() == "/start":
        await message.reply("✅ 调试版机器人已在线！\n直接在讨论组线程发 /telegraph 测试")

# 主功能
@app.on_message(filters.command("telegraph"))
async def make_telegraph(client, message: Message):
    print(f"[DEBUG] /telegraph 命令被触发！")
    
    thread_id = getattr(message, 'message_thread_id', None)
    if not thread_id and message.reply_to_message:
        thread_id = getattr(message.reply_to_message, 'message_thread_id', None)

    if not thread_id:
        return await message.reply("❌ 请在**频道讨论组的线程**里使用 /telegraph")

    await message.reply("🔄 正在收集媒体...")

    try:
        topic = await client.get_discussion_message(message.chat.id, thread_id)
        messages = [topic]

        async for msg in client.get_chat_history(message.chat.id, limit=300, offset_id=topic.id):
            if getattr(msg, 'message_thread_id', None) == thread_id and msg.media:
                messages.append(msg)

        messages.sort(key=lambda m: m.date)

        title = "COSER 写真"
        for m in messages:
            if m.text and m.text.strip():
                title = m.text.split('\n')[0][:100]
                break

        await message.reply(f"找到 {len(messages)} 条媒体，开始上传...")

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

print("✅ 极简调试版已启动")
app.run()
