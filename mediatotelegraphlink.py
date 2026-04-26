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

# 存储每组的第一张消息
group_first_messages = []
last_message_time = 0

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本24** 已启动\n发完一组图片后，输入 /telegraph 我会提取**每组第一张**的链接")

@app.on_message(filters.media)
async def collect_first(client, message: Message):
    global last_message_time
    
    now = time.time()
    
    # 超过10秒视为新的一组
    if now - last_message_time > 10:
        # 保存上一组的第一张（如果有）
        if 'current_first' in globals() and current_first is not None:
            group_first_messages.append(current_first)
    
    # 更新当前组的第一张
    global current_first
    current_first = message
    
    last_message_time = now

@app.on_message(filters.command("telegraph"))
async def send_first_links(client, message: Message):
    global group_first_messages, current_first
    
    # 把最后一组也加上
    if 'current_first' in globals() and current_first is not None:
        group_first_messages.append(current_first)
    
    if not group_first_messages:
        return await message.reply("目前没有收集到图片")

    links = []
    for i, msg in enumerate(group_first_messages):
        link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.id}"
        links.append(f"第 {i+1} 组 → {link}")

    text = "📸 **提取完成**（每组只取第一张）\n\n" + "\n".join(links)
    await message.reply(text)
    
    # 清空，准备下次使用
    group_first_messages = []
    if 'current_first' in globals():
        current_first = None

print("✅ 版本24 已启动")
app.run()
