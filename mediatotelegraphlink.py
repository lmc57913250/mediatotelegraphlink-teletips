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

# 支持多个讨论组：每个讨论组独立保存自己的状态
states = {}   # discussion_id → {"cover": Message, "firsts": list, "last_time": float}

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本51** 已启动\n✅ 自动识别多个频道+讨论组\n✅ 每组只提取第一张\n✅ 所有链接统一用讨论组ID")

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states

    # 只处理讨论组的消息（频道封面会自动转发到讨论组）
    if message.chat.type != "supergroup":
        return

    discussion_id = message.chat.id
    now = time.time()

    # 如果这个讨论组是第一次出现，初始化状态
    if discussion_id not in states:
        states[discussion_id] = {"cover": None, "firsts": [], "last_time": 0}
        print(f"[DEBUG] 新讨论组已识别: {discussion_id}")

    state = states[discussion_id]

    if state["cover"] is None:
        # 第一条媒体消息 = 封面
        state["cover"] = message
        state["firsts"] = [message]
        state["last_time"] = now
        print(f"[DEBUG] 封面已记录 (讨论组 {discussion_id} - Msg {message.id})")
    else:
        # 时间间隔判断每组第一张
        interval = now - state["last_time"]
        if interval > 0.1:   # 大于0.1秒 = 新的一组
            state["firsts"].append(message)
            print(f"[DEBUG] 新组第一张 (间隔 {interval:.2f}秒): {message.id}")
        else:
            print(f"[DEBUG] 同一组忽略 (间隔 {interval:.2f}秒)")
        
        state["last_time"] = now

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global states

    discussion_id = message.chat.id

    if discussion_id not in states or states[discussion_id]["cover"] is None:
        return await message.reply("❌ 请先在对应频道发一张封面图（会自动转到讨论组）")

    state = states[discussion_id]
    firsts = state["firsts"]

    links = []
    for i, msg in enumerate(firsts):
        link = f"https://t.me/c/{str(discussion_id)[4:]}/{msg.id}"
        links.append(f"第 {i+1} 张 → {link}")

    text = f"📸 **提取完成**（共 {len(links)} 组第一张，讨论组ID: {discussion_id}）\n\n" + "\n".join(links)
    await message.reply(text)

    # 清空当前讨论组的状态，准备下一轮
    states[discussion_id] = {"cover": None, "firsts": [], "last_time": 0}

print("✅ 版本51 已启动（支持多个频道+讨论组自动识别）")
app.run()
