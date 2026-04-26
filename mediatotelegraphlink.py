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

# 支持多个讨论组独立运行
states = {}   # discussion_id → {"cover": None, "firsts": [], "last_time": 0}

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本52** 已启动\n✅ 只在讨论组工作\n✅ 第一条媒体=封面\n✅ 之后每组取第一张")

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states

    if message.chat.type != "supergroup":
        return

    did = message.chat.id
    now = time.time()

    if did not in states:
        states[did] = {"cover": None, "firsts": [], "last_time": 0}

    state = states[did]

    if state["cover"] is None:
        # 第一条媒体 = 封面
        state["cover"] = message
        state["firsts"] = [message]
        state["last_time"] = now
        print(f"[DEBUG] 新讨论组 {did} - 封面已记录: {message.id}")
    else:
        interval = now - state["last_time"]
        if interval > 0.1:          # 大于0.1秒 = 新的一组
            state["firsts"].append(message)
            print(f"[DEBUG] 新组第一张 (间隔 {interval:.2f}s): {message.id}")
        # else: 同一组，忽略
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

    # 清空当前讨论组
    states[did] = {"cover": None, "firsts": [], "last_time": 0}

print("✅ 版本52 已启动（纯讨论组模式）")
app.run()
