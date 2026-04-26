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
    await message.reply("✅ 机器人已就绪\n在讨论组线程里发 /telegraph")

@app.on_message(filters.command("telegraph"))
async def make_telegraph(client, message: Message):
    thread_id = getattr(message, 'message_thread_id', None)
    if not thread_id and message.reply_to_message:
        thread_id = getattr(message.reply_to_message, 'message_thread_id', None)
    if not thread_id:
        thread_id = 1

    await message.reply(f"🔄 检测到线程 (ID: {thread_id})，正在收集媒体...")

    try:
        messages = []

        # 直接从线程里拉取最近 400 条消息（不使用 get_discussion_message）
        async for msg in client.get_chat_history(message.chat.id, limit=400):
            if getattr(msg, 'message_thread_id', None) == thread_id:
                messages.append(msg)

        if not messages:
            return await message.reply("未找到任何消息")

        # 按时间排序
        messages.sort(key=lambda m: m.date)

        # 提取标题（第一条有文字的消息第一行）
        title = "COSER 写真"
        for m in messages:
            if m.text and m.text.strip():
                title = m.text.split('\n')[0][:100]
                break

        await message.reply(f"✅ 找到 {len(messages)} 条消息，开始上传...")

        urls = []
        for m in messages:
            if not m.media: 
                continue
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

print("✅ 最终绕过限制版已启动")
app.run()
