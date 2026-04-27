from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import re

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

states = {}
user_current_group = {}
bot_groups = {}

if os.path.exists("bot_groups.json"):
    with open("bot_groups.json", "r", encoding="utf-8") as f:
        bot_groups = json.load(f)

keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")],
    [KeyboardButton("添加群组")]
], resize_keyboard=True)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply(
        "✅ **版本109（线程提取版）** 已启动\n\n"
        "✔ 相册只取第一张\n"
        "✔ 自动公开链接\n"
        "✔ 支持线程提取（直接发链接）",
        reply_markup=keyboard
    )

# =========================
# ⭐ 私聊处理
# =========================
@app.on_message(filters.text & filters.private)
async def handle_private(client, message: Message):
    global states, user_current_group, bot_groups
    text = message.text.strip()
    user_id = message.from_user.id

    # =========================
    # ⭐ 线程提取（新功能）
    # =========================
    if text.startswith("http"):
        await message.reply("⏳ 正在提取线程...")

        try:
            match = re.search(r"t\.me/(.+?)/(\d+)", text)
            if not match:
                await message.reply("❌ 链接格式错误")
                return

            chat_input = match.group(1)
            msg_id = int(match.group(2))

            if chat_input.startswith("c/"):
                chat_id = int("-100" + chat_input.split("/")[1])
            else:
                chat = await client.get_chat(chat_input)
                chat_id = chat.id

            chat = await client.get_chat(chat_id)

            root_msg = await client.get_messages(chat_id, msg_id)

            # 收集回复
            replies = []
            async for msg in client.search_messages(chat_id, reply_to_message_id=msg_id):
                replies.append(msg)

            replies.sort(key=lambda x: x.id)

            # =========================
            # ⭐ 按你的规则处理
            # =========================
            result_msgs = []
            processed_albums = set()

            # 封面
            if root_msg.media:
                result_msgs.append(root_msg)

            # 回复
            for msg in replies:

                # 只处理媒体
                if not msg.media:
                    continue

                # 相册只取第一张
                if msg.media_group_id:
                    if msg.media_group_id in processed_albums:
                        continue
                    processed_albums.add(msg.media_group_id)
                    result_msgs.append(msg)
                else:
                    result_msgs.append(msg)

            # =========================
            # 输出
            # =========================
            output = f"线程提取（共 {len(result_msgs)} 张）\n"

            for i, msg in enumerate(result_msgs, 1):

                if chat.username:
                    link = f"https://t.me/{chat.username}/{msg.id}"
                else:
                    link = f"https://t.me/c/{str(chat_id)[4:]}/{msg.id}"

                output += f"第 {i} 张 → {link}\n"

            await message.reply(output)

        except Exception as e:
            await message.reply(f"❌ 提取失败: {e}")

        return

    # =========================
    # 原有功能（不变）
    # =========================

    if text == "添加群组":
        await message.reply("请输入群组链接或ID（-100开头）：")
        return

    if "t.me/" in text:
        try:
            if "/+" in text:
                chat = await client.get_chat(text)
            else:
                username = text.split("t.me/")[1].split("/")[0]
                chat = await client.get_chat(username)

            bot_groups[chat.id] = chat.title or f"群组 {chat.id}"

            with open("bot_groups.json", "w", encoding="utf-8") as f:
                json.dump(bot_groups, f, ensure_ascii=False, indent=2)

            await message.reply(f"✅ 已添加群组: {bot_groups[chat.id]}")
        except Exception as e:
            await message.reply(f"❌ 添加失败: {e}")
        return

    if text.startswith("-100") and text[1:].isdigit():
        gid = int(text)
        try:
            chat = await client.get_chat(gid)
            bot_groups[gid] = chat.title or f"群组 {gid}"

            with open("bot_groups.json", "w", encoding="utf-8") as f:
                json.dump(bot_groups, f, ensure_ascii=False, indent=2)

            await message.reply(f"✅ 已添加群组: {bot_groups[gid]}")
        except Exception as e:
            await message.reply(f"❌ 添加失败: {e}")
        return

    if text == "开始新收集":
        if not bot_groups:
            await message.reply("❌ 请先添加群组")
            return

        buttons = []
        for gid, gname in bot_groups.items():
            buttons.append([InlineKeyboardButton(gname, callback_data=f"select_group_{gid}")])

        await message.reply("请选择群组：", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if text == "提取链接":
        did = user_current_group.get(user_id)

        if not did or did not in states:
            await message.reply("❌ 没有数据")
            return

        chat = await client.get_chat(did)

        for g_idx, group in enumerate(states[did]["groups"], 1):
            title = group.get("title", f"第 {g_idx} 组")
            output = f"{title}\n"

            for i, msg in enumerate(group["messages"], 1):

                if chat.username:
                    link = f"https://t.me/{chat.username}/{msg.id}"
                else:
                    link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"

                output += f"第 {i} 张 → {link}\n"

            await message.reply(output.strip())

    elif text == "清空当前":
        did = user_current_group.get(user_id)
        if did:
            states[did] = {"groups": [], "cover_map": {}, "processed_albums": set()}
        await message.reply("✅ 已清空")

# =========================
# 群选择
# =========================
@app.on_callback_query(filters.regex(r"select_group_(-?\d+)"))
async def handle_group_select(client, callback):
    user_id = callback.from_user.id
    group_id = int(callback.data.split("_")[2])

    user_current_group[user_id] = group_id

    states[group_id] = {
        "groups": [],
        "cover_map": {},
        "processed_albums": set()
    }

    await callback.message.edit_text("✅ 已选择群组，开始收集\n请发送封面图")
    await callback.answer()

# =========================
# ⭐ 收集逻辑（相册只取第一张）
# =========================
@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    did = message.chat.id

    if did not in states:
        return

    state = states[did]

    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state['groups'])+1} 组"

    if message.media_group_id:
        gid = message.media_group_id

        if gid in state["processed_albums"]:
            return

        state["processed_albums"].add(gid)

        if not message.reply_to_message:
            new_group = {
                "title": title,
                "messages": [message],
                "cover_id": message.id
            }

            state["groups"].append(new_group)
            state["cover_map"][message.id] = len(state["groups"]) - 1

        else:
            reply_id = message.reply_to_message.id

            if reply_id in state["cover_map"]:
                idx = state["cover_map"][reply_id]
                state["groups"][idx]["messages"].append(message)

        return

    if not message.reply_to_message:
        new_group = {
            "title": title,
            "messages": [message],
            "cover_id": message.id
        }

        state["groups"].append(new_group)
        state["cover_map"][message.id] = len(state["groups"]) - 1
        return

    reply_id = message.reply_to_message.id

    if reply_id in state["cover_map"]:
        idx = state["cover_map"][reply_id]
        state["groups"][idx]["messages"].append(message)

print("✅ 版本109 已启动（线程+相册首图）")
app.run()
