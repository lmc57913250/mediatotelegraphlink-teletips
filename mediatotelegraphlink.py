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

@app.on_message(filters.command("telegraph"))
async def make_telegraph(client, message: Message):
    print(f"[DEBUG] 收到 /telegraph 命令！ Chat: {message.chat.id} Thread: {message.message_thread_id}")
    
    thread_id = message.message_thread_id
    if not thread_id and message.reply_to_message:
        thread_id = message.reply_to_message.message_thread_id

    print(f"[DEBUG] 最终 thread_id = {thread_id}")

    if not thread_id:
        return await message.reply("❌ 请在讨论组线程里使用")

    await message.reply("🔄 已收到命令，正在收集媒体... (调试模式)")

    try:
        topic = await client.get_discussion_message(message.chat.id, thread_id)
        print(f"[DEBUG] 成功获取封面消息 ID: {topic.id}")

        messages = [topic]
        async for msg in client.get_chat_history(message.chat.id, limit=400, offset_id=topic.id):
            if msg.message_thread_id == thread_id and msg.media:
                messages.append(msg)

        print(f"[DEBUG] 共收集 {len(messages)} 条消息")

        # ... 后面代码保持不变（为了不让代码太长，我这里省略了后面的上传部分，你可以用之前的）

        messages.sort(key=lambda m: m.date)

        title = "COSER 写真"
        for m in messages:
            if m.text and m.text.strip():
                title = m.text.split('\n')[0][:100]
                break

        await message.reply(f"找到 {len(messages)} 条媒体，开始生成...")

        # （上传和生成 Telegraph 的代码保持和上次一样，这里省略以节省篇幅）

        telegraph = Telegraph()
        telegraph.create_account(short_name="COSER")

        html = f"<h1>{title}</h1><br>"
        # ... 上传循环省略 ...

        page = telegraph.create_page(title=title, html_content=html, author_name="COSER Archive")
        await message.reply(f"✅ **生成完成！**\n\n🔗 {page['url']}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        await message.reply(f"❌ 出错: {str(e)}")

print("Bot is alive! 调试模式已开启")
app.run()
