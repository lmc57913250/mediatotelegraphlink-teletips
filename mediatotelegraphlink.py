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
    await message.reply("✅ **版本70** 已启动\n加强转发调试", reply_markup=keyboard)

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
    is_new_cover = (message.reply_to_message is None)

    caption = (message.caption or "").strip()
    title = caption.split('\n')[0][:100] if caption else f"第 {len(state['groups'])+1} 组"

    if is_new_cover:
        new_group = {"title": title, "messages": [message], "cover_url": None}
        state["groups"].append(new_group)
        state["current"] = new_group
        
        # 自动转发
        try:
            await message.forward("img_mom_bot")
            print(f"[DEBUG] ✅ 成功转发封面到 @img_mom_bot | MsgID: {message.id}")
        except Exception as e:
            print(f"[DEBUG] ❌ 转发失败: {e}")
    else:
        if state["current"] is not None:
            interval = now - state["last_time"]
            if interval > 0.02:
                state["current"]["messages"].append(message)
    
    state["last_time"] = now

# 接收 @img_mom_bot 的回复
@app.on_message(filters.chat("img_mom_bot"))
async def handle_imgmom_reply(client, message: Message):
    global states
    print(f"[DEBUG] 收到 @img_mom_bot 消息: {message.text[:300] if message.text else '无文字内容'}")

    if not message.text or "Successfully uploaded image" not in message.text:
        return

    match = re.search(r'https?://[^\s]+', message.text)
    if match:
        url = match.group(0)
        print(f"[DEBUG] ✅ 提取到顶图链接: {url}")

        # 给最后一个组加上顶图
        for did, state in list(states.items()):
            if state["groups"] and state["groups"][-1].get("cover_url") is None:
                state["groups"][-1]["cover_url"] = url
                print(f"[DEBUG] ✅ 已保存顶图到第 {len(state['groups'])} 组")
                return

print("✅ 版本70 已启动")
app.run()
