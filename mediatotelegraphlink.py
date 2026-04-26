# Copyright ©️ 2022 TeLe TiPs. Modified for COSER workflow by Grok

from pyrogram import Client, filters
from pyrogram.types import Message
from telegraph import upload_file
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
    await message.reply("发送 /telegraph 到讨论组线程里即可打包生成 Telegraph 帖子")

@teletips.on_message(filters.command('telegraph'))
async def make_telegraph(client, message):
    if not message.reply_to_message:
        return await message.reply("请**回复**任意一条该线程的消息，然后发送 /telegraph")

    thread_id = message.reply_to_message.message_thread_id or message.message_thread_id
    if not thread_id:
        return await message.reply("请在频道讨论组的线程里使用此命令")

    await message.reply("正在收集该线程的所有媒体，请稍等...")

    try:
        # 获取频道主帖（封面）
        topic = await client.get_discussion_message(message.chat.id, thread_id)
        messages = [topic]  # 第一条是封面

        # 获取线程内后续消息（最多 300 条）
        async for msg in client.get_chat_history(message.chat.id, limit=300, offset_id=topic.id):
            if msg.message_thread_id == thread_id and msg.media:
                messages.append(msg)

        if len(messages) < 1:
            return await message.reply("未找到媒体")

        # 排序（按时间）
        messages.sort(key=lambda m: m.date)

        # 第一条文字作为标题（封面下面第一行）
        title = "COSER 写真"
        for m in messages:
            if m.text:
                title = m.text.split('\n')[0][:100]
                break

        await message.reply(f"找到 {len(messages)} 条媒体，开始上传 Telegraph...")

        # 上传所有媒体
        telegraph_urls = []
        for m in messages:
            if m.media:
                try:
                    file = await m.download(in_memory=True)
                    uploaded = upload_file(file)
                    telegraph_urls.append(f"https://telegra.ph{uploaded[0]}")
                except:
                    pass

        # 创建 Telegraph 页面
        from telegraph import Telegraph
        telegraph = Telegraph()
        telegraph.create_account(short_name="COSER")
        
        html_content = "<h1>" + title + "</h1><br>"
        for url in telegraph_urls:
            if url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                html_content += f'<img src="{url}"><br><br>'
            else:
                html_content += f'<video src="{url}" controls></video><br><br>'

        page = telegraph.create_page(title=title, html_content=html_content, author_name="YourName")

        await message.reply(f"✅ **生成完成！**\n\n🔗 {page['url']}")

    except Exception as e:
        await message.reply(f"出错: {str(e)}")

print("Bot is alive! Ready for /telegraph in threads.")
teletips.run()
