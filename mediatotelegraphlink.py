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

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("✅ **版本65** 已启动\n标题提取已修复", reply_markup=keyboard)

@app.on_message(filters.text)
async def handle_buttons(client, message: Message):
    global states
    text = message.text.strip()
    did = message.chat.id

    if text == "开始新收集":
        states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已开启收集模式")

    elif text == "提取链接":
        if did not in states or not states[did]["groups"]:
            await message.reply("❌ 当前没有内容")
            return

        output = []
        for g_idx, group in enumerate(states[did]["groups"], 1):
            title = group.get("title", f"第 {g_idx} 组")
            output.append(f"【{title}】")
            for i, msg in enumerate(group["messages"], 1):
                link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
                output.append(f"第 {i} 张 → {link}")
            output.append("─" * 30)

        await message.reply("\n".join(output))

        states[did] = {"groups": [], "current": None, "last_time": 0}

    elif text == "清空当前":
        if did in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已清空")

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id
    if did not in states:
        return

    state = states[did]
    now = time.time()

    is_new_cover = message.reply_to_message is None

    # 提取标题（封面说明的第一行）
    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state['groups'])+1} 组"

    if is_new_cover:
        # 新封面
        new_group = {
            "title": title,
            "messages": [message]
        }
        state["groups"].append(new_group)
        state["current"] = new_group
    else:
        if state["current"] is not None:
            interval = now - state["last_time"]
            if interval > 0.02:
                state["current"]["messages"].append(message)
    
    state["last_time"] = now

print("✅ 版本65 已启动（标题提取稳定版）")
app.run()
