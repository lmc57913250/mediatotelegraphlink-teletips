@teletips.on_message(filters.command('telegraph'))
async def make_telegraph(client, message):
    """支持直接在线程里发 /telegraph，或回复任意消息"""
    # 获取线程ID（优先当前消息的线程，再尝试回复的消息）
    thread_id = message.message_thread_id
    if not thread_id and message.reply_to_message:
        thread_id = message.reply_to_message.message_thread_id

    if not thread_id:
        return await message.reply("请在**频道帖子的讨论组线程**里使用 /telegraph 命令")

    await message.reply("正在收集该线程的所有媒体，请稍等...")

    try:
        # 获取频道主帖（封面）
        topic = await client.get_discussion_message(message.chat.id, thread_id)
        messages = [topic]

        # 获取线程内后续所有带媒体的消息
        async for msg in client.get_chat_history(message.chat.id, limit=300, offset_id=topic.id):
            if msg.message_thread_id == thread_id and msg.media:
                messages.append(msg)

        if len(messages) <= 1:
            return await message.reply("线程里没有找到足够的媒体")

        # 按时间排序
        messages.sort(key=lambda m: m.date)

        # 取标题（封面下面第一行文字）
        title = "COSER 写真"
        for m in messages:
            if m.text and m.text.strip():
                title = m.text.split('\n')[0][:100]
                break

        await message.reply(f"找到 {len(messages)} 条媒体，开始上传 Telegraph...")

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
