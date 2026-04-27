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

async def private_reply(user_id: int, text: str):
    try:
        await app.send_message(user_id, text, reply_markup=keyboard)
    except:
        pass

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await private_reply(message.from_user.id, 
        "✅ **机器人已就绪**（版本71 零痕迹版）\n\n"
        "所有操作和结果只会在这里显示\n"
        "请使用下方按钮：")

# ==================== 按钮处理（群组完全不发消息） ====================
@app.on_message(filters.text & filters.group)
async def handle_buttons(client, message: Message):
    global states
    text = message.text.strip()
    did = message.chat.id
    user_id = message.from_user.id

    if text == "开始新收集":
        states[did] = {"groups": [], "current": None, "last_time": 0}
        await private_reply(user_id, "✅ **已开启新收集**\n请在群组发送封面图")

    elif text == "提取链接":
        if did not in states or not states[did].get("groups"):
            await private_reply(user_id, "❌ 当前没有正在收集的内容")
            return

        output = []
        for g_idx, group in enumerate(states[did]["groups"], 1):
            title = group.get("title", f"第 {g_idx} 组")
            output.append(f"【{title}】")
            for i, msg in enumerate(group["messages"], 1):
                link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
                output.append(f"第 {i} 张 → {link}")
            output.append("─" * 40)

        await private_reply(user_id, "\n".join(output))

        states[did] = {"groups": [], "current": None, "last_time": 0}

    elif text == "清空当前":
        if did in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        await private_reply(user_id, "✅ 已清空当前记录")

# ==================== 媒体处理（完全静默） ====================
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

print("✅ 版本71 已启动（群组零痕迹 + 私人窗口）")
app.run()
