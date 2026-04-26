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
public_usernames = {}   # discussion_id → public username (如 K4pRI9UlIm0zNjI1)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本56** 已启动\n自动转换公开链接（适合Telegra.ph）")

# 自动获取公开用户名
async def get_public_username(client, discussion_id):
    if discussion_id in public_usernames:
        return public_usernames[discussion_id]
    
    try:
        chat = await client.get_chat(discussion_id)
        if chat.username:
            public_usernames[discussion_id] = chat.username
            print(f"[DEBUG] 获取到公开用户名: {chat.username}")
            return chat.username
    except:
        pass
    return None

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
        if interval > 0.02:
            state["firsts"].append(message)
        state["last_time"] = now

@app.on_message(filters.command("telegraph"))
async def generate(client, message: Message):
    global states

    did = message.chat.id
    if did not in states or states[did]["cover"] is None:
        return await message.reply("❌ 请先在讨论组发一张封面图")

    state = states[did]
    
    # 获取公开用户名
    public_name = await get_public_username(client, did)
    
    links = []
    for i, msg in enumerate(state["firsts"]):
        if public_name:
            link = f"https://t.me/{public_name}/{msg.id}"
            link_type = "公开链接"
        else:
            link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
            link_type = "私人链接"
        links.append(f"第 {i+1} 张 → {link} ({link_type})")

    text = f"📸 **提取完成**（共 {len(links)} 组第一张）\n\n" + "\n".join(links)
    await message.reply(text)

    states[did] = {"cover": None, "firsts": [], "last_time": 0}

print("✅ 版本56 已启动（自动公开链接）")
app.run()
