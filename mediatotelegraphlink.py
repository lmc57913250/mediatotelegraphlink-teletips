from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
import json

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

states = {}
user_current_group = {}
bot_groups = {}

# 读取群组列表
if os.path.exists("bot_groups.json"):
    with open("bot_groups.json", "r", encoding="utf-8") as f:
        bot_groups = json.load(f)

# 主菜单
keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")],
    [KeyboardButton("添加群组")]
], resize_keyboard=True)

# 启动
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply(
        "✅ **版本107（单图稳定版）** 已启动\n\n"
        "相册只提取第一张\n\n"
        "点击「开始新收集」选择群组",
        reply_markup=keyboard
    )

# 私聊处理
@app.on_message(filters.text & filters.private)
async def handle_private(client, message: Message):
    global states, user_current_group, bot_groups
    text = message.text.strip()
    user_id = message.from_user.id

    if text == "添加群组":
        await message.reply("请输入群组链接或ID（以 -100 开头）：")
        return

    # 添加群组（链接）
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
            await message.reply(f"❌ 添加群组失败: {e}")
        return

    # 添加群组（ID）
    if text.startswith("-100") and text[1:].isdigit():
        gid = int(text)
        try:
            chat = await client.get_chat(gid)
            bot_groups[gid] = chat.title or f"群组 {gid}"

            with open("bot_groups.json", "w", encoding="utf-8") as f:
                json.dump(bot_groups, f, ensure_ascii=False, indent=2)

            await message.reply(f"✅ 已添加群组: {bot_groups[gid]}")
        except Exception as e:
            await message.reply(f"❌ 添加群组失败: {e}")
        return

    # 开始收集
    if text == "开始新收集":
        if not bot_groups:
            await message.reply("❌ 请先添加群组")
            return

        buttons = []
        for gid, gname in bot_groups.items():
            buttons.append([InlineKeyboardButton(gname, callback_data=f"select_group_{gid}")])

        await message.reply("请选择群组：", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # 提取链接
    if text == "提取链接":
        did = user_current_group.get(user_id)

        if not did or did not in states:
            await message.reply("❌ 没有数据")
            return

        for g_idx, group in enumerate(states[did]["groups"], 1):
            title = group.get("title", f"第 {g_idx} 组")
            output = f"{title}\n"

            for i, msg in enumerate(group["messages"], 1):
                chat = await client.get_chat(did)

if chat.username:
    link = f"https://t.me/{chat.username}/{msg.id}"
else:
    link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
                output += f"第 {i} 张 → {link}\n"

            await message.reply(output.strip())

    # 清空
    elif text == "清空当前":
        did = user_current_group.get(user_id)
        if did:
            states[did] = {"groups": [], "cover_map": {}, "processed_albums": set()}
        await message.reply("✅ 已清空")

# 选择群组
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
# ⭐ 核心逻辑（只取相册第一张）
# =========================
@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    did = message.chat.id

    if did not in states:
        return

    state = states[did]

    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state['groups'])+1} 组"

    # ===== 相册 =====
    if message.media_group_id:
        gid = message.media_group_id

        # 已处理过 → 跳过
        if gid in state["processed_albums"]:
            return

        state["processed_albums"].add(gid)

        # 👉 只取第一张
        first_msg = message

        if not first_msg.reply_to_message:
            new_group = {
                "title": title,
                "messages": [first_msg],
                "cover_id": first_msg.id
            }

            state["groups"].append(new_group)
            state["cover_map"][first_msg.id] = len(state["groups"]) - 1

        else:
            reply_id = first_msg.reply_to_message.id

            if reply_id in state["cover_map"]:
                idx = state["cover_map"][reply_id]
                state["groups"][idx]["messages"].append(first_msg)

        return

    # ===== 单图 =====
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

print("✅ 版本107 已启动（相册只取第一张）")
app.run()
