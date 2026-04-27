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
    await message.reply("✅ **版本62** 已启动\n支持多组封面自动识别", reply_markup=keyboard)

@app.on_message(filters.text)
async def handle_buttons(client, message: Message):
    global states
    text = message.text.strip()
    did = message.chat.id

    if text == "开始新收集":
        states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已开启收集模式\n可连续传多个封面")

    elif text == "提取链接":
        if did not in states or not states[did]["groups"]:
            await message.reply("❌ 当前没有内容")
            return

        output = []
        for g_idx, group in enumerate(states[did]["groups"], 1):
            output.append(f"【第 {g_idx} 组】")
            for i, msg in enumerate(group, 1):
                link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
                output.append(f"第 {i} 张 → {link}")
            output.append("─" * 30)   # 分隔线

        await message.reply("\n".join(output))

        # 提取后清空
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

    # 关键判断：不带回复的消息 = 新封面
    is_new_cover = message.reply_to_message is None

    if is_new_cover:
        # 新封面 → 开始新的一组
        new_group = [message]
        state["groups"].append(new_group)
        state["current"] = new_group
        print(f"[DEBUG] 新封面组开始: {message.id}")
    else:
        # 带回复的消息 = 当前组的内容
        if state["current"] is not None:
            interval = now - state["last_time"]
            if interval > 0.02:
                state["current"].append(message)
                print(f"[DEBUG] 当前组添加: {message.id}")
    
    state["last_time"] = now

print("✅ 版本62 已启动（多组自动识别）")
app.run()
