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
bot_messages = {}   # 记录机器人自己在群组发送的消息ID，用于清空时删除

keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")]
], resize_keyboard=True)

async def send_and_record(client, chat_id: int, text: str):
    """发送消息并记录ID，用于后续删除"""
    msg = await client.send_message(chat_id, text, reply_markup=keyboard)
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    bot_messages[chat_id].append(msg.id)
    return msg

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await send_and_record(client, message.chat.id, "✅ **机器人已就绪**（版本70）\n使用下方按钮操作")

@app.on_message(filters.text & filters.group)
async def handle_buttons(client, message: Message):
    global states, bot_messages
    text = message.text.strip()
    did = message.chat.id
    user_id = message.from_user.id

    if text == "开始新收集":
        states[did] = {"groups": [], "current": None, "last_time": 0}
        await send_and_record(client, did, "✅ 已开启新收集模式")

    elif text == "提取链接":
        if did not in states or not states[did].get("firsts"):
            await send_and_record(client, did, "❌ 当前没有正在收集的内容")
            return

        links = [f"https://t.me/c/{str(did)[4:]}/{msg.id}" for msg in states[did]["firsts"]]
        output = "\n".join(links)
        await send_and_record(client, did, f"📸 **提取完成**（共 {len(links)} 组）\n\n{output}")

        states[did] = {"groups": [], "current": None, "last_time": 0}

    elif text == "清空当前":
        if did in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        
        # 删除机器人自己之前发送的所有消息
        if did in bot_messages:
            for msg_id in bot_messages[did]:
                try:
                    await client.delete_messages(did, msg_id)
                except:
                    pass
            bot_messages[did] = []
        
        await send_and_record(client, did, "✅ 已清空当前记录并删除机器人消息")

# 媒体处理（静默）
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

print("✅ 版本70 已启动（清空时删除机器人消息）")
app.run()
