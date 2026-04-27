from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
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

keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")],
    [KeyboardButton("刷新群组列表")]
], resize_keyboard=True)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    global bot_groups
    bot_groups.clear()
    async for dialog in client.get_dialogs():
        if dialog.chat.type in ["supergroup", "group"]:
            bot_groups[dialog.chat.id] = dialog.chat.title or f"群组 {dialog.chat.id}"
    
    await message.reply(
        "✅ **版本94** 已启动\n\n"
        f"已自动刷新群组列表，共找到 {len(bot_groups)} 个群组\n\n"
        "点击「开始新收集」选择群组",
        reply_markup=keyboard
    )

# ==================== 识别群组链接/ID ====================
@app.on_message(filters.text & filters.private)
async def handle_private(client, message: Message):
    global states, user_current_group, bot_groups
    text = message.text.strip()
    user_id = message.from_user.id

    if "t.me/" in text:
        try:
            if "/+" in text:
                chat = await client.get_chat(text)
            else:
                username = text.split("t.me/")[1].split("/")[0]
                chat = await client.get_chat(username)
            
            bot_groups[chat.id] = chat.title or f"群组 {chat.id}"
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
            await message.reply(f"✅ 已添加群组: {bot_groups[gid]}")
        except Exception as e:
            await message.reply(f"❌ 添加群组失败: {e}")
        return

    if text == "刷新群组列表":
        bot_groups.clear()
        async for dialog in client.get_dialogs():
            if dialog.chat.type in ["supergroup", "group"]:
                bot_groups[dialog.chat.id] = dialog.chat.title or f"群组 {dialog.chat.id}"
        await message.reply(f"✅ 已刷新，共找到 {len(bot_groups)} 个群组")
        return

    if text == "开始新收集":
        if not bot_groups:
            await message.reply("❌ 机器人还没有加入任何群组\n请点击「刷新群组列表」\n或者直接输入群组链接/ID")
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
            
            copy_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 复制本组", callback_data=f"copy_group_{did}_{g_idx-1}")]
            ])
            
            await message.reply(output.strip(), reply_markup=copy_keyboard)

    elif text == "清空当前":
        did = user_current_group.get(user_id)
        if did and did in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已清空当前记录")

# ==================== 群组选择 ====================
@app.on_callback_query(filters.regex(r"select_group_(-?\d+)"))
async def handle_group_select(client, callback):
    global user_current_group, states
    user_id = callback.from_user.id
    group_id = int(callback.data.split("_")[2])
    
    user_current_group[user_id] = group_id
    group_name = bot_groups.get(group_id, f"群组 {group_id}")
    
    states[group_id] = {"groups": [], "current": None, "last_time": 0}
    
    await callback.message.edit_text(
        f"✅ 已选择群组: {group_name}\n"
        f"✅ 已开启新收集模式\n\n"
        f"请在群组发送封面图"
    )
    await callback.answer()

# ==================== 一键复制功能 ====================
@app.on_callback_query(filters.regex(r"copy_group_(-?\d+)_(\d+)"))
async def handle_copy_group(client, callback):
    did = int(callback.data.split("_")[2])
    group_idx = int(callback.data.split("_")[3])
    
    if did not in states or group_idx >= len(states[did].get("groups", [])):
        await callback.answer("❌ 内容已过期，请重新提取", show_alert=True)
        return
    
    group = states[did]["groups"][group_idx]
    title = group.get("title", f"第 {group_idx+1} 组")
    clean_title = title.replace("【", "").replace("】", "")
    
    output = f"{clean_title}\n"
    for i, msg in enumerate(group["messages"], 1):
        link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
        output += f"第 {i} 张 → {link}\n"
    
    await callback.message.reply(f"📋 已复制内容：\n\n{output.strip()}")
    await callback.answer("✅ 已复制到剪贴板")

# ==================== 媒体处理（封面条 + 所有讨论条 = 一组） ====================
@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id
    if did not in states:
        return

    state = states[did]
    now = time.time()

    # 判断是否是新封面条（带说明文字的消息）
    caption = (message.caption or "").strip()
    has_caption = len(caption) > 0

    # 提取标题（封面条第一行）
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state.get('groups', []))+1} 组"

    if has_caption:
        # 新封面条 → 开始新的一组（只提取第一张）
        new_group = {"title": title, "messages": [message]}
        if "groups" not in state:
            state["groups"] = []
        state["groups"].append(new_group)
        state["current"] = new_group
        print(f"[DEBUG] 新封面条开始: {title} | MsgID: {message.id}")
    else:
        # 讨论条 → 属于当前封面条的组（只提取第一张）
        if state.get("current"):
            # 只添加第一张（如果当前组还没有添加过）
            if len(state["current"]["messages"]) == 0:
                state["current"]["messages"].append(message)
            print(f"[DEBUG] 添加到当前组: {message.id} | 当前组共有 {len(state['current']['messages'])} 张")

    state["last_time"] = now

print("✅ 版本94 已启动（最终版）")
app.run()
