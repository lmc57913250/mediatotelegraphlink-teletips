from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import os
import time

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

states = {}

keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")]
], resize_keyboard=True)

async def safe_private_reply(user_id, text):
    if user_id:
        try:
            await app.send_message(user_id, text)
        except:
            pass

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = getattr(message, 'from_user', None)
    user_id = user_id.id if user_id else None
    
    await message.reply("✅ **版本73** 已启动\n私信同步已开启", reply_markup=keyboard)
    await safe_private_reply(user_id, "✅ 机器人已就绪，所有提取结果都会在这里同步显示")

@app.on_message(filters.text & filters.group)
async def handle_buttons(client, message: Message):
    global states
    text = message.text.strip()
    did = message.chat.id
    user = getattr(message, 'from_user', None)
    user_id = user.id if user else None

    if text == "开始新收集":
        states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已开启新收集")
        await safe_private_reply(user_id, "✅ 已开启新收集模式\n请发送封面图")

    elif text == "提取链接":
        if did not in states or not states[did].get("groups"):
            await message.reply("❌ 当前没有内容")
            await safe_private_reply(user_id, "❌ 当前没有正在收集的内容")
            return

        output = []
        for g_idx, group in enumerate(states[did]["groups"], 1):
            title = group.get("title", f"第 {g_idx} 组")
            output.append(f"【{title}】")
            for i, msg in enumerate(group["messages"], 1):
                link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
                output.append(f"第 {i} 张 → {link}")
            output.append("─" * 40)

        result_text = "\n".join(output)
        await message.reply(result_text)
        await safe_private_reply(user_id, result_text)

        states[did] = {"groups": [], "current": None, "last_time": 0}

    elif text == "清空当前":
        if did in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已清空")
        await safe_private_reply(user_id, "✅ 已清空当前记录")

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

print("✅ 版本73 已启动（稳定版）")
app.run()
