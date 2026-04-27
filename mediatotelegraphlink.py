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

# 自定义键盘
keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("开始新收集")],
    [KeyboardButton("提取链接")],
    [KeyboardButton("清空当前")]
], resize_keyboard=True, one_time_keyboard=False)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply(
        "✅ **机器人已就绪**\n\n"
        "使用下方快捷按钮操作：\n"
        "• 「开始新收集」→ 开始记录封面和图片\n"
        "• 「提取链接」→ 提取当前收集的链接\n"
        "• 「清空当前」→ 重置本次记录",
        reply_markup=keyboard
    )

@app.on_message(filters.text)
async def handle_text_commands(client, message: Message):
    global states
    text = message.text.strip()
    did = message.chat.id

    if text == "开始新收集":
        if did not in states:
            states[did] = {"cover": None, "firsts": [], "last_time": 0}
        states[did]["cover"] = None
        states[did]["firsts"] = []
        await message.reply("✅ **已开启新收集**\n请先发送一张封面图")
        
    elif text == "提取链接":
        if did not in states or states[did]["cover"] is None:
            await message.reply("❌ 当前没有正在收集的内容\n请先点击「开始新收集」")
            return

        state = states[did]
        links = []
        for i, msg in enumerate(state["firsts"]):
            link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
            links.append(link)

        output = "\n".join(links) if links else "暂无链接"
        await message.reply(f"📸 **提取完成**（共 {len(links)} 组）\n\n{output}")

    elif text == "清空当前":
        if did in states:
            states[did] = {"cover": None, "firsts": [], "last_time": 0}
        await message.reply("✅ 已清空当前收集记录")

    # 处理普通文字（可用于提取标题）
    elif did in states and states[did]["cover"] is not None and not states[did].get("title_set"):
        title = text.split('\n')[0].strip()[:100]
        if title:
            states[did]["title"] = title
            states[did]["title_set"] = True

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id
    now = time.time()

    if did not in states or states[did]["cover"] is None:
        return   # 没开启收集时忽略媒体

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

print("✅ 版本58 已启动（底部快捷键盘）")
app.run()
