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

states = {}

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本54** 已启动\n新组判断阈值 0.05秒（更敏感）")

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states

    did = message.chat.id
    now = time.time()

    if did not in states:
        states[did] = {"cover": None, "firsts": [], "last_time": 0}

    state = states[did]

    if state["cover"] is None:
        state["cover"] = message
        state["firsts"] = [message]
        state["last_time"] = now
    else:
        interval = now - state["last_time"]
        if interval > 0.05:          # ← 这里改成 0.05秒
            state["firsts"].append(message)
            print(f"[DEBUG] 新组第一张 (间隔 {interval:.3f}秒): {message.id}")
        else:
            print(f"[DEBUG] 同一组忽略 (间隔 {interval:.3f}秒): {message.id}")
        
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

print("✅ 版本54 已启动（0.05秒敏感模式）")
app.run()
