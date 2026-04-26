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

collected_groups = []   # 存储每组的第一张消息
last_time = 0

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ **版本23** 已启动\n发完一组图片后，输入 /telegraph 我会只提取**每组的第一张**链接")

@app.on_message(filters.media)
async def collect_first_per_group(client, message: Message):
    global last_time
    
    now = time.time()
    
    # 如果超过 10 秒没有新消息，认为是新的一组
    if now - last_time > 10:
        # 保存上一组的第一张
        if 'current_first' in globals() and current_first:
            collected_groups.append(current_first)
    
    # 更新当前组的第一张
    if 'current_first' not in globals() or now - last_time > 10:
        global current_first
        current_first = message
    
    last_time = now

@app.on_message(filters.command("telegraph"))
async def send_links(client, message: Message):
    global collected_groups, current_first
    
    if 'current_first' in globals() and current_first:
        collected_groups.append(current_first)
    
    if not collected_groups:
        return await message.reply("还没有收集到图片")

    links = []
    for i, msg in enumerate(collected_groups):
        link = f"https://t.me/c/{str(msg.chat.id)[4:]}/{msg.id}"
        links.append(f"第 {i+1} 组 → {link}")

    text = "📸 **提取完成**（每组只取第一张）\n\n" + "\n".join(links)
    await message.reply(text)
    
    # 清空，准备下一次
    collected_groups = []
    if 'current_first' in globals():
        current_first = None

print("✅ 版本23 已启动 - 按组提取第一张")
app.run()
