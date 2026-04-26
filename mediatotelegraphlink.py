# Copyright © 2022 TeLe TiPs. Modified for COSER workflow by Grok

from pyrogram import Client, filters
from pyrogram.types import Message
from telegraph import upload_file, Telegraph
import os
import asyncio

teletips = Client(
    "MediaToTelegraphLink",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

@teletips.on_message(filters.command('start') & filters.private)
async def start(client, message):
    await message.reply("在频道讨论组的线程里回复任意消息发送 /telegraph 即可打包生成 Telegraph 帖子")

@teletips.on_message(filters.command('telegraph'))
async def make_telegraph(client, message):
    if not message.reply_to_message:
        return await message.reply("请**回复**线程里的任意一条消息，然后发送 /telegraph")

    thread_id = message.reply_to_message.message_thread_id or message.message_thread_id
    if not thread_id:
        return await message.reply("请在频道帖子的讨论组线程里使用此命令")

    await message.reply("正在收集该线程的所有媒体，请稍等...")

    try:
        # 获取频道主帖（封面）
        topic = await client.get_discussion_message(message.chat.id, thread_id)
        messages = [topic]

        # 获取线程内后续消息（最多300条）
        async for msg in client.get_chat_history(message.chat.id, limit=300, offset_id=topic.id):
            if msg.message_thread_id == thread_id and msg.media:
                messages.append(msg)

        if len(messages) < 1:
            return await message.reply("未找到媒体")

        # 按时间排序
        messages.sort(key=lambda m: m.date)

        # 取封面下面第一行文字作为标题
        title = "COSER 写真"
        for m in messages:
            if m.text:
                title = m.text.split('\n')[0][:100]
                break

        await message.reply(f"找到 {len(messages)} 条媒体，开始上传...")

        # 上传所有媒体
        telegraph_urls = []
        for m in messages:
            if not m.media:
                continue
            try:
                file = await m.download(in_memory=True)
                file_bytes = file.getvalue() if hasattr(file, 'getvalue') else file.read() if hasattr(file, 'read') else file
                uploaded = upload_file(file_bytes)
                telegraph_urls.append(f"https://telegra.ph{uploaded[0]}")
                await asyncio.sleep(0.8)
            except Exception as e:
                print(f"上传失败: {e}")
                continue

        # 创建 Telegraph 页面
        telegraph = Telegraph()
        telegraph.create_account(short_name="COSER")

        html_content = f"<h1>{title}</h1><br>"
        for url in telegraph_urls:
            if url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                html_content += f'<img src="{url}"><br><br>'
            else:
                html_content += f'<video src="{url}" controls></video><br><br>'

        page = telegraph.create_page(
            title=title,
            html_content=html_content,
            author_name="Your COSER Archive"
        )

        await message.reply(f"✅ **生成完成！**\n\n🔗 {page['url']}")

    except Exception as e:
        await message.reply(f"出错: {str(e)}")

print("Bot is alive! Ready for /telegraph in threads.")
teletips.run()
