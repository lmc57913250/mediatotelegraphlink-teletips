from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
import re
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

if os.path.exists("bot_groups.json"):
    with open("bot_groups.json", "r", encoding="utf-8") as f:
        bot_groups = json.load(f)
else:
    bot_groups = {}

keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")],
    [KeyboardButton("添加群组")]
], resize_keyboard=True)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply(
        "✅ **版本103** 已启动\n\n"
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
        
        keyboard = []
        for gid, gname in bot_groups.items():
            keyboard.append([InlineKeyboardButton(gname, callback_data=f"select_group_{gid}")])
        
        await message.reply("请选择要操作的群组：", reply_markup=InlineKeyboardMarkup(keyboard))
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
        if did and did in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已清空当前记录")

@app.on_callback_query(filters.regex(r"select_group_(-?\d+)"))
async def handle_group_select(client, callback):
    global user_current_group, states
    user_id = callback.from_user.id
    group_id = int(callback.data.split("_")[2])
    
    user_current_group[user_id] = group_id
    group_name = bot_groups.get(group_id, f"群组 {group_id}")
    
    states[group_id] = {"groups": [], "cover_map": {}}
    
    await callback.message.edit_text(
        f"✅ 已选择群组: {group_name}\n"
        f"✅ 已开启新收集模式\n\n"
        f"请在群组发送封面图"
    )
    await callback.answer()

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

    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state.get('groups', []))+1} 组"

    if is_new_cover:
        if has_media_group:
            if state.get("current") and state["current"].get("media_group_id") == message.media_group_id:
                print(f"[DEBUG] 跳过封面相册的后续图片: {message.id}")
            else:
                new_group = {
                    "title": title,
                    "messages": [message],
                    "media_group_id": message.media_group_id,
                    "cover_id": message.id
                }
                if "groups" not in state:
                    state["groups"] = []
                state["groups"].append(new_group)
                state["current"] = new_group
                if "cover_map" not in state:
                    state["cover_map"] = {}
                state["cover_map"][message.id] = len(state["groups"]) - 1
                print(f"[DEBUG] 新封面相册开始: {title}")
        else:
            new_group = {
                "title": title,
                "messages": [message],
                "media_group_id": None,
                "cover_id": message.id
            }
            if "groups" not in state:
                state["groups"] = []
            state["groups"].append(new_group)
            state["current"] = new_group
            if "cover_map" not in state:
                state["cover_map"] = {}
            state["cover_map"][message.id] = len(state["groups"]) - 1
            print(f"[DEBUG] 新封面图片开始: {title}")
    else:
        if message.reply_to_message:
            reply_id = message.reply_to_message.id
            
            if "cover_map" in state and reply_id in state["cover_map"]:
                group_idx = state["cover_map"][reply_id]
                target_group = state["groups"][group_idx]
                
                if target_group.get("media_group_id") is not None and message.media_group_id is not None:
                    if message.media_group_id == target_group["media_group_id"]:
                        print(f"[DEBUG] 跳过讨论组相册的后续图片: {message.id}")
                    else:
                        target_group["messages"].append(message)
                        print(f"[DEBUG] 添加到封面 {reply_id} 的组: {message.id}")
                else:
                    if target_group.get("cover_id") == reply_id:
                        target_group["messages"].append(message)
                        print(f"[DEBUG] 添加到封面 {reply_id} 的组: {message.id}")
                    else:
                        if state.get("current"):
                            state["current"]["messages"].append(message)
                            print(f"[DEBUG] 兜底添加到当前组: {message.id}")
            else:
                if state.get("current"):
                    state["current"]["messages"].append(message)
                    print(f"[DEBUG] 兜底添加到当前组: {message.id}")

    state["last_time"] = now

print("✅ 版本103 已启动（严格检查 media_group_id）")
app.run()
