@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id
    if did not in states:
        return

    state = states[did]
    now = time.time()

    is_new_cover = (message.reply_to_message is None)
    has_media_group = message.media_group_id is not None

    print(f"[DEBUG] 消息 ID: {message.id}")
    print(f"[DEBUG] 是否有回复: {message.reply_to_message is not None}")
    if message.reply_to_message:
        print(f"[DEBUG] 回复的 ID: {message.reply_to_message.id}")
    if message.media_group_id:
        print(f"[DEBUG] 媒体组 ID: {message.media_group_id}")
    else:
        print(f"[DEBUG] 没有媒体组 ID")
    
    # ... 其余代码保持不变
