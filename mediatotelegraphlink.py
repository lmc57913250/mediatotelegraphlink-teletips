from pyrogram import Client, filters
from pyrogram.types import Message
import os
import time

app = Client(
    "COSERBot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

states = {}   # discussion_id → state

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本53** 已启动\n宽松识别模式 + 调试")

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states

    did = message.chat.id
    chat_type = message.chat.type
    now = time.time()

    print(f"[DEBUG] 收到媒体消息 | ChatID: {did} | Type: {chat_type} | MsgID: {message.id}")

    if did not in states:
        states[did] = {"cover": None, "firsts": [], "last_time": 0}
        print(f"[DEBUG] 新讨论组已注册: {did}")

    state = states[did]

    if state["cover"] is None:
        state["cover"] = message
        state["firsts"] = [message]
        state["last_time"] = now
        print(f"[DEBUG] ✅ 封面已成功记录: {message.id}")
    else:
        interval = now - state["last_time"]
        if interval > 0.1:
            state["firsts"].append(message)
            print(f"[DEBUG] ✅ 新组第一张 (间隔 {interval:.2f}s): {message.id}")
        else:
            print(f"[DEBUG] 同一组忽略 (间隔 {interval:.2f}s)")
        state["last_time"] = now

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global states

    did = message.chat.id

    if did not in states or states[did]["cover"] is None:
        return await message.reply("❌ 请先在讨论组发一张封面图")

    state = states[did]
    links = []
    for i, msg in enumerate(state["firsts"]):
        link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
        links.append(f"第 {i+1} 张 → {link}")

    text = f"📸 **提取完成**（共 {len(links)} 组第一张）\n\n" + "\n".join(links)
    await message.reply(text)

    states[did] = {"cover": None, "firsts": [], "last_time": 0}

print("✅ 版本53 已启动（宽松调试版）")
app.run()
