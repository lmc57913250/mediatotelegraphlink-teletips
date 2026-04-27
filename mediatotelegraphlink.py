from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import os
import time
import re

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
    await message.reply("✅ **版本68** 已启动\n顶图 + 标题提取已修复", reply_markup=keyboard)

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
            cover_url = group.get("cover_url", "未获取顶图")
            
            output.append(f"【{title}】")
            output.append(f"顶图: {cover_url}")
            output.append("")
            
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

# ==================== 媒体处理 ====================

@app.on_message(filters.media)
async def handle_media(client, message: Message):
    global states
    did = message.chat.id
    if did not in states:
        return

    state = states[did]
    now = time.time()

    is_new_cover = (message.reply_to_message is None)

    # 提取标题（封面说明第一行）
    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state['groups'])+1} 组"

    if is_new_cover:
        new_group = {
            "title": title,
            "messages": [message],
            "cover_url": None
        }
        state["groups"].append(new_group)
        state["current"] = new_group
        
        # 自动转发封面给图床机器人
        await message.forward("img_mom_bot")
    else:
        if state["current"] is not None:
            interval = now - state["last_time"]
            if interval > 0.02:
                state["current"]["messages"].append(message)
    
    state["last_time"] = now

# ==================== 接收图床机器人回复 ====================

@app.on_message(filters.chat("img_mom_bot"))
async def handle_imgmom_reply(client, message: Message):
    global states
    if not message.text:
        return

    # 更强的正则匹配
    match = re.search(r'https?://[^\s]+', message.text)
    if not match:
        return

    public_url = match.group(0)

    # 给最近一个没有顶图的组加上链接
    for did, state in list(states.items()):
        if state["groups"] and state["groups"][-1].get("cover_url") is None:
            state["groups"][-1]["cover_url"] = public_url
            print(f"[DEBUG] 顶图链接已保存: {public_url}")
            return   # 只处理一次

print("✅ 版本68 已启动（顶图 + 标题双修复）")
app.run()
