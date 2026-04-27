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
    await message.reply("✅ **机器人已就绪**（版本59）\n使用下方按钮操作", reply_markup=keyboard)

@app.on_message(filters.text)
async def handle_buttons(client, message: Message):
    global states
    text = message.text.strip()
    did = message.chat.id

    if text == "开始新收集":
        if did not in states:
            states[did] = {"cover": None, "firsts": [], "last_time": 0}
        states[did]["cover"] = None
        states[did]["firsts"] = []
        await message.reply("✅ **已开启新收集**\n请发送第一张封面图")

    elif text == "提取链接":
        if did not in states or not states[did]["firsts"]:
            await message.reply("❌ 当前没有正在收集的内容\n请先点击「开始新收集」并发送图片")
            return

        links = [f"https://t.me/c/{str(did)[4:]}/{msg.id}" for msg in states[did]["firsts"]]
        output = "\n".join(links)
        await message.reply(f"📸 **提取完成**（共 {len(links)} 张）\n\n{output}")

    elif text == "清空当前":
        if did in states:
            states[did] = {"cover": None, "firsts": [], "last_time": 0}
        await message.reply("✅ 已清空当前记录")

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id
    if did not in states:
        return  # 没开启收集就忽略

    state = states[did]
    now = time.time()

    if state["cover"] is None:
        state["cover"] = message
        state["firsts"] = [message]
        state["last_time"] = now
        await message.reply("📌 封面已记录，继续发送图片吧")
    else:
        interval = now - state["last_time"]
        if interval > 0.02:
            state["firsts"].append(message)
        state["last_time"] = now

print("✅ 版本59 已启动（修复收集逻辑）")
app.run()
