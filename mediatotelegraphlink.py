from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
import re
import json
import asyncio  # ✅ 已帮你加好

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
        "✅ **版本106（稳定版）** 已启动\n\n"
        "点击「开始新收集」选择群组\n"
        "如果群组列表为空，请点击「添加群组」并输入群组链接或ID",
        reply_markup=keyboard
    )

@app.on_message(filters.text & filters.private)
async def handle_private(client, message: Message):
    global states, user_current_group, bot_groups
    text = message.text.strip()
    user_id = message.from_user.id

    if text == "添加群组":
        await message.reply("请输入群组链接或ID（以 -100 开头）：")
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
            return
        except Exception as e:
            await message.reply(f"❌ 添加群组失败: {e}")
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
            await message.reply(f"❌ 添加群组失败: {e}")
        return

    if text == "开始新收集":
        if not bot_groups:
            await message.reply("❌ 机器人还没有加入任何群组\n请点击「添加群组」并输入群组链接或ID")
            return

        keyboard_inline = []
        for gid, gname in bot_groups.items():
            keyboard_inline.append([InlineKeyboardButton(gname, callback_data=f"select_group_{gid}")])

        await message.reply("请选择要操作的群组：", reply_markup=InlineKeyboardMarkup(keyboard_inline))
        return

    if text == "提取链接":
        did = user_current_group.get(user_id)
        if not did:
            await message.reply("❌ 请先点击「开始新收集」选择群组")
            return

        if did not in states or not states[did].get("groups"):
            await message.reply("❌ 当前没有正在收集的内容")
            return

        for g_idx, group in enumerate(states[did]["groups"], 1):
            title = group.get("title", f"第 {g_idx} 组")
            clean_title = title.replace("【", "").replace("】", "")

            output = f"{clean_title}\n"
            for i, msg in enumerate(group["messages"], 1):
                link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
                output += f"第 {i} 张 → {link}\n"

            await message.reply(output.strip())

    elif text == "清空当前":
        did = user_current_group.get(user_id)
        if did:
            states[did] = {"groups": [], "cover_map": {}, "album_cache": {}}
        await message.reply("✅ 已清空当前记录")

@app.on_callback_query(filters.regex(r"select_group_(-?\d+)"))
async def handle_group_select(client, callback):
    global user_current_group, states
    user_id = callback.from_user.id
    group_id = int(callback.data.split("_")[2])

    user_current_group[user_id] = group_id
    group_name = bot_groups.get(group_id, f"群组 {group_id}")

    states[group_id] = {"groups": [], "cover_map": {}, "album_cache": {}}

    await callback.message.edit_text(
        f"✅ 已选择群组: {group_name}\n"
        f"✅ 已开启新收集模式\n\n"
        f"请在群组发送封面图"
    )
    await callback.answer()

# =========================
# ⭐ 核心优化后的收集逻辑
# =========================
@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id

    if did not in states:
        return

    state = states[did]

    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state['groups'])+1} 组"

    # ===== 相册处理 =====
    if message.media_group_id:
        gid = message.media_group_id

        if gid not in state["album_cache"]:
            state["album_cache"][gid] = []

        state["album_cache"][gid].append(message)

        await asyncio.sleep(0.5)

        album = state["album_cache"].get(gid)
        if not album:
            return

        if album[0].id != message.id:
            return

        first_msg = album[0]

        if not first_msg.reply_to_message:
            new_group = {
                "title": title,
                "messages": album.copy(),
                "media_group_id": gid,
                "cover_id": first_msg.id
            }

            state["groups"].append(new_group)
            state["cover_map"][first_msg.id] = len(state["groups"]) - 1
            state["current"] = new_group

        else:
            reply_id = first_msg.reply_to_message.id

            if reply_id in state["cover_map"]:
                idx = state["cover_map"][reply_id]
                state["groups"][idx]["messages"].extend(album)

        del state["album_cache"][gid]
        return

    # ===== 单图 =====
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
        return

    reply_id = message.reply_to_message.id

    if reply_id in state["cover_map"]:
        idx = state["cover_map"][reply_id]
        state["groups"][idx]["messages"].append(message)

print("✅ 版本106 已启动（稳定相册版）")
app.run()
