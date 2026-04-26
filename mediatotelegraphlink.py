from pyrogram import Client, filters
from pyrogram.types import Message
from telegraph import upload_file, Telegraph
import os
import asyncio

app = Client(
    "COSER_Telegraph",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("COSER 写真打包机器人已启动\n在讨论组线程里发送 /telegraph 即可打包")

@app.on_message(filters.command("telegraph"))
async def make_telegraph(client, message: Message):
    # 获取线程ID（支持直接发命令或回复）
    thread_id = message.message_thread_id
    if not thread_id and message.reply_to_message:
        thread_id = message.reply_to_message.message_thread_id

    if not thread_id:
        return await message.reply("❌ 请在**频道帖子的讨论组线程**里使用 /telegraph")

    await message.reply("🔄 正在收集该线程的所有媒体...")

    try:
        # 获取封面（频道主帖）
        topic = await client.get_discussion_message(message.chat.id, thread_id)
        messages = [topic]

        # 收集线程内媒体
        async for msg in client.get_chat_history(message.chat.id, limit=400, offset_id=topic.id):
            if msg.message_thread_id == thread_id and msg.media:
                messages.append(msg)

        messages.sort(key=lambda x: x.date)

        # 取标题
        title = "COSER 写真"
        for m in messages:
            if m.text and m.text.strip():
                title = m.text.split('\n')[0][:100]
                break

        await message.reply(f"✅ 找到 {len(messages)} 条媒体，开始上传...")

        urls = []
        for m in messages:
            if not m.media:
                continue
            try:
                file = await m.download(in_memory=True)
                file_bytes = file.getvalue() if hasattr(file, "getvalue") else bytes(file.read()) if hasattr(file, "read") else file
                uploaded = upload_file(file_bytes)
                urls.append(f"https://telegra.ph{uploaded[0]}")
                await asyncio.sleep(0.7)
            except:
                continue

        # 生成 Telegraph
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

print("✅ Bot is alive! Ready for /telegraph")
app.run()
