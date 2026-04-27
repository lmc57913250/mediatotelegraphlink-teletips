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
    await message.reply(
        "✅ **版本69** 已启动\n"
        "• 正常使用：点击「开始新收集」\n"
        "• 提取旧封面：回复旧封面消息 + 发送 /collect",
        reply_markup=keyboard
    )

# ==================== 按钮处理 ====================
@app.on_message(filters.text)
async def handle_buttons(client, message: Message):
    global states
    text = message.text.strip()
    did = message.chat.id

    if text == "开始新收集":
        states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已开启新收集模式")

    elif text == "提取链接":
        if did not in states or not states[did]["groups"]:
            await message.reply("❌ 当前没有内容")
            return
        # 输出逻辑（保持之前清晰格式）
        output = []
        for g_idx, group in enumerate(states[did]["groups"], 1):
            title = group.get("title", f"第 {g_idx} 组")
            output.append(f"【{title}】")
            for i, msg in enumerate(group["messages"], 1):
                link = f"https://t.me/c/{str(did)[4:]}/{msg.id}"
                output.append(f"第 {i} 张 → {link}")
            output.append("─" * 40)
        await message.reply("\n".join(output))
        states[did] = {"groups": [], "current": None, "last_time": 0}

    elif text == "清空当前":
        if did in states:
            states[did] = {"groups": [], "current": None, "last_time": 0}
        await message.reply("✅ 已清空")

# ==================== 新功能：回复旧封面 + /collect ====================
@app.on_message(filters.command("collect"))
async def collect_from_reply(client, message: Message):
    global states
    did = message.chat.id

    if not message.reply_to_message:
        await message.reply("❌ 请**回复**你要提取的封面消息，然后发送 /collect")
        return

    cover_msg = message.reply_to_message

    if did not in states:
        states[did] = {"groups": [], "current": None, "last_time": 0}

    # 提取标题
    caption = (cover_msg.caption or cover_msg.text or "").strip()
    title = caption.split('\n')[0][:100] if caption else "未设置标题"

    # 创建新组
    new_group = {
        "title": title,
        "messages": [cover_msg]
    }
    states[did]["groups"].append(new_group)
    states[did]["current"] = new_group

    await message.reply(f"✅ 已开始收集此封面下的回复\n标题：{title}\n正在等待你发图片...")

# ==================== 普通媒体收集（自动模式） ====================
@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id
    if did not in states or states[did]["current"] is None:
        return

    state = states[did]
    now = time.time()

    if now - state["last_time"] > 0.02:
        state["current"]["messages"].append(message)

    state["last_time"] = now

print("✅ 版本69 已启动（支持回复旧封面提取）")
app.run()
