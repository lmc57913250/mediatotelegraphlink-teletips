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
user_mode = {}  # ⭐ 新增：模式控制

if os.path.exists("bot_groups.json"):
    with open("bot_groups.json", "r", encoding="utf-8") as f:
        bot_groups = json.load(f)

keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")],
    [KeyboardButton("添加群组")],
    [KeyboardButton("线程提取模式")]  # ⭐ 新按钮
], resize_keyboard=True)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("✅ 版本110 已启动", reply_markup=keyboard)

# =========================
# 私聊
# =========================
@app.on_message(filters.text & filters.private)
async def handle_private(client, message: Message):
    global user_mode

    text = message.text.strip()
    user_id = message.from_user.id

    # =========================
    # ⭐ 模式切换
    # =========================
    if text == "线程提取模式":
        user_mode[user_id] = "thread"
        await message.reply("✅ 已进入线程提取模式，请发送消息链接")
        return

    # =========================
    # ⭐ 线程提取模式
    # =========================
    if user_mode.get(user_id) == "thread" and text.startswith("http"):
        user_mode[user_id] = None  # 用一次就退出

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

            # ⭐ 正确方式：拉历史筛选
            replies = []
            async for msg in client.get_chat_history(chat_id, limit=1000):
                if msg.reply_to_message_id == msg_id:
                    replies.append(msg)

            replies.sort(key=lambda x: x.id)

            # ⭐ 处理逻辑（只取相册首图）
            result = []
            processed_albums = set()

            if root_msg.media:
                result.append(root_msg)

            for msg in replies:
                if not msg.media:
                    continue

                if msg.media_group_id:
                    if msg.media_group_id in processed_albums:
                        continue
                    processed_albums.add(msg.media_group_id)

                result.append(msg)

            # 输出
            output = f"线程提取（共 {len(result)} 张）\n"

            for i, msg in enumerate(result, 1):
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
    # 原有逻辑（完全不受影响）
    # =========================

    if text == "添加群组":
        await message.reply("请输入群组链接或ID")
        return

    if "t.me/" in text:
        try:
            username = text.split("t.me/")[1].split("/")[0]
            chat = await client.get_chat(username)

            bot_groups[chat.id] = chat.title

            with open("bot_groups.json", "w", encoding="utf-8") as f:
                json.dump(bot_groups, f, ensure_ascii=False, indent=2)

            await message.reply(f"✅ 已添加群组: {chat.title}")
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
            output = f"{group.get('title','')}\n"

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

    await callback.message.edit_text("✅ 已选择群组")
    await callback.answer()

# =========================
# 收集逻辑（不变）
# =========================
@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    did = message.chat.id

    if did not in states:
        return

    state = states[did]

    if message.media_group_id:
        gid = message.media_group_id

        if gid in state["processed_albums"]:
            return

        state["processed_albums"].add(gid)

    if not message.reply_to_message:
        new_group = {
            "title": "新组",
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

print("✅ 版本110 已启动（线程模式修复）")
app.run()
