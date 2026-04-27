from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

states = {}
user_current_group = {}      # 用户ID -> 当前操作的群组ID
bot_groups = {}              # 群组ID -> 群组名称

keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")]
], resize_keyboard=True)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id
    await message.reply(
        "✅ **版本76** 已启动\n\n"
        "点击「开始新收集」选择群组\n"
        "其他操作直接点击按钮",
        reply_markup=keyboard
    )

# ==================== 自动记录机器人加入的群组 ====================
@app.on_message(filters.new_chat_members)
async def on_bot_added(client, message: Message):
    for member in message.new_chat_members:
        if member.id == (await client.get_me()).id:
            chat = message.chat
            bot_groups[chat.id] = chat.title or f"群组 {chat.id}"
            print(f"[DEBUG] 机器人加入群组: {chat.title} ({chat.id})")

# ==================== 群组选择菜单 ====================
@app.on_message(filters.text & filters.private)
async def handle_private(client, message: Message):
    global states, user_current_group, bot_groups
    text = message.text.strip()
    user_id = message.from_user.id

    if text == "开始新收集":
        if not bot_groups:
            await message.reply("❌ 机器人还没有加入任何群组\n请先把机器人拉进群并给管理员权限")
            return
        
        # 显示群组选择菜单
        keyboard = []
        for gid, gname in bot_groups.items():
            keyboard.append([InlineKeyboardButton(gname, callback_data=f"select_group_{gid}")])
        
        await message.reply(
            "请选择要操作的群组：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if text == "提取链接":
        did = user_current_group.get(user_id)
        if not did:
            await message.reply("❌ 请先点击「开始新收集」选择群组")
            return
        
        if did not in states or not states[did].get("groups"):
            await message.reply("❌ 当前没有正在收集的内容")
            return

        output = []
        for g_idx, group in enumerate(states[did]["groups"], 1):
            title = group.get("title", f"第 {g_idx} 组")
            output.append(f"【{title}】")
            for i, msg in enumerate(group["messages"], 1):
                link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
                output.append(f"第 {i} 张 → {link}")
            output.append("─" * 40)

        await message.reply("\n".join(output))

    elif text == "清空当前":
        did = user_current_group.get(user_id)
        if did and did in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已清空当前记录")

# ==================== 处理群组选择 ====================
@app.on_callback_query(filters.regex(r"select_group_(-?\d+)"))
async def handle_group_select(client, callback):
    global user_current_group
    user_id = callback.from_user.id
    group_id = int(callback.data.split("_")[2])
    
    user_current_group[user_id] = group_id
    group_name = bot_groups.get(group_id, f"群组 {group_id}")
    
    await callback.message.edit_text(f"✅ 已选择群组: {group_name}\n现在可以点击「开始新收集」开始操作")
    await callback.answer()

# ==================== 媒体处理 ====================
@app.on_message(filters.media & filters.group)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id
    if did not in states:
        return

    state = states[did]
    now = time.time()

    is_new_cover = (message.reply_to_message is None)

    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state.get('groups', []))+1} 组"

    if is_new_cover:
        new_group = {"title": title, "messages": [message]}
        if "groups" not in state:
            state["groups"] = []
        state["groups"].append(new_group)
        state["current"] = new_group
    else:
        if state.get("current"):
            interval = now - state.get("last_time", 0)
            if interval > 0.02:
                state["current"]["messages"].append(message)

    state["last_time"] = now

print("✅ 版本76 已启动（群组选择菜单）")
app.run()
