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

# ==================== 私人回复函数 ====================
async def private_reply(user_id: int, text: str):
    try:
        await app.send_message(user_id, text)
    except:
        pass

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await private_reply(message.from_user.id, 
        "✅ **机器人已就绪**（版本68 零痕迹版）\n\n"
        "所有操作和结果只会在这里显示\n"
        "请使用下方快捷按钮操作：")
    # 不在群组回复任何消息
    await message.reply("✅ 已就绪", reply_markup=keyboard)  # 只显示一次键盘

# ==================== 按钮处理（只在群组触发，回复到私聊） ====================
@app.on_message(filters.text & filters.group)
async def handle_buttons(client, message: Message):
    global states
    text = message.text.strip()
    did = message.chat.id
    user_id = message.from_user.id

    if text == "开始新收集":
        if did not in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        states[did]["cover"] = None
        states[did]["firsts"] = []
        await private_reply(user_id, "✅ **已开启新收集**\n请在群组发送封面图")

    elif text == "提取链接":
        if did not in states or not states[did].get("firsts"):
            await private_reply(user_id, "❌ 当前没有正在收集的内容")
            return

        links = [f"https://t.me/c/{str(did)[4:]}/{msg.id}" for msg in states[did]["firsts"]]
        output = "\n".join(links)
        await private_reply(user_id, f"📸 **提取完成**（共 {len(links)} 组）\n\n{output}")

        # 自动重置
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

print("✅ 版本68 已启动（群组零痕迹版）")
app.run()
