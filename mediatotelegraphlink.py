@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id

    if did not in states:
        return

    state = states[did]

    # 初始化
    if "groups" not in state:
        state["groups"] = []
    if "cover_map" not in state:
        state["cover_map"] = {}
    if "processed_albums" not in state:
        state["processed_albums"] = set()

    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state['groups'])+1} 组"

    # =========================
    # ✅ 相册：只取第一张
    # =========================
    if message.media_group_id:
        gid = message.media_group_id

        # 已处理过 → 直接跳过
        if gid in state["processed_albums"]:
            return

        # 标记为已处理
        state["processed_albums"].add(gid)

        # 👉 当前这条就是“第一张”
        first_msg = message

        # ===== 新封面 =====
        if not first_msg.reply_to_message:
            new_group = {
                "title": title,
                "messages": [first_msg],  # ✅ 只放一张
                "media_group_id": gid,
                "cover_id": first_msg.id
            }

            state["groups"].append(new_group)
            state["cover_map"][first_msg.id] = len(state["groups"]) - 1
            state["current"] = new_group

            print(f"[DEBUG] 新封面（相册首图）: {title}")

        # ===== 回复封面 =====
        else:
            reply_id = first_msg.reply_to_message.id

            if reply_id in state["cover_map"]:
                idx = state["cover_map"][reply_id]
                state["groups"][idx]["messages"].append(first_msg)
                print(f"[DEBUG] 相册首图加入组 {reply_id}")

        return

    # =========================
    # ✅ 单图处理（不变）
    # =========================
    if not message.reply_to_message:
        new_group = {
            "title": title,
            "messages": [message],
            "media_group_id": None,
            "cover_id": message.id
        }

        state["groups"].append(new_group)
        state["cover_map"][message.id] = len(state["groups"]) - 1
        state["current"] = new_group

        print(f"[DEBUG] 新封面: {title}")
        return

    reply_id = message.reply_to_message.id

    if reply_id in state["cover_map"]:
        idx = state["cover_map"][reply_id]
        state["groups"][idx]["messages"].append(message)
        print(f"[DEBUG] 添加到组 {reply_id}")
