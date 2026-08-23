import os
import discord
import random
from datetime import datetime, timedelta
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- Cấu hình Server (Giữ bot online trên Render) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot đang chạy!"

# --- Biến lưu trữ & Cấu hình ID ---
ADMIN_ID = 1517328324618096711     # THAY BẰNG ID CỦA BẠN
LOG_CHANNEL_ID = 1540982626364559370 # THAY BẰNG ID KÊNH LOG CỦA BẠN

inventory = {}      
fish_storage = {}   
daily_check = {}    
cooldown_check = {} 
blacklist = {}      # Lưu {user_id: lí_do}

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} đã sẵn sàng!')

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    user_id = str(message.author.id)
    content = message.content.lower().strip()
    if not content: return

    # Lấy từ đầu tiên trong tin nhắn để kiểm tra lệnh
    command_name = content.split()[0]
    bot_commands = ['nhelp', 'ncauca', 'nfish', 'nbanca', 'nme', 'ndaily', 'nban', 'nunban']

    # Kiểm tra Blacklist: Nếu người dùng bị cấm và cố tình gõ lệnh
    if user_id in blacklist:
        if command_name in bot_commands:
            reason = blacklist[user_id]
            await message.channel.send(f"{message.author.mention} đã bị ban bởi Admin với lí do {reason}")
        return # Bỏ qua mọi tin nhắn của người này

    now = datetime.now()

    # 1. Lệnh nhelp
    if content == 'nhelp':
        await message.channel.send("📋 **Danh sách lệnh:**\n`ncauca`: Câu cá (Cooldown 3p)\n`nfish`: Xem số cá chưa bán\n`nbanca`: Bán toàn bộ cá lấy coin\n`nme`: Xem số dư coin\n`ndaily`: Nhận coin mỗi ngày")

    # 2. Lệnh ncauca 
    elif content == 'ncauca':
        last_time = cooldown_check.get(user_id)
        if last_time and now < last_time:
            wait_time = int((last_time - now).total_seconds() / 60) + 1
            await message.channel.send(f"{message.author.mention} Bạn đang thấm mệt, hãy nghỉ ngơi {wait_time} phút nữa rồi quay lại nhé!")
        else:
            if random.random() < 0.3:
                rac = ['một chiếc dép cũ', 'một cái áo rách', 'một mớ rác thải']
                await message.channel.send(f'{message.author.mention} Bạn quăng cần xuống... và câu được {random.choice(rac)}. Chán thế!')
            else:
                so_ca = random.randint(1, 10)
                fish_storage[user_id] = fish_storage.get(user_id, 0) + so_ca
                await message.channel.send(f'{message.author.mention} Bạn câu được {so_ca} con cá! Dùng `nbanca` để bán nhé.')
            
            cooldown_check[user_id] = now + timedelta(minutes=3)

    # 3. Lệnh nfish
    elif content == 'nfish':
        so_ca = fish_storage.get(user_id, 0)
        await message.channel.send(f"🐟 Bạn đang có {so_ca} con cá trong kho.")

    # 4. Lệnh nbanca
    elif content == 'nbanca':
        so_ca = fish_storage.get(user_id, 0)
        if so_ca > 0:
            coin = so_ca * 5  
            inventory[user_id] = inventory.get(user_id, 0) + coin
            fish_storage[user_id] = 0
            await message.channel.send(f"Bạn đã bán {so_ca} con cá và nhận được {coin} coin! Tổng số dư: {inventory[user_id]} coin.")
        else:
            await message.channel.send("Bạn không có cá để bán!")

    # 5. Lệnh nme
    elif content == 'nme':
        so_du = inventory.get(user_id, 0)
        await message.channel.send(f"💰 **Số dư của bạn:** {so_du} coin.")

    # 6. Lệnh ndaily
    elif content == 'ndaily':
        today = now.strftime("%Y-%m-%d")
        if daily_check.get(user_id) == today:
            await message.channel.send("Bạn đã nhận quà hôm nay rồi, mai quay lại nhé!")
        else:
            thuong = random.randint(1, 50)
            inventory[user_id] = inventory.get(user_id, 0) + thuong
            daily_check[user_id] = today
            await message.channel.send(f"Bạn nhận được {thuong} coin! Tổng số dư: {inventory[user_id]} coin.")

    # 7. Lệnh nsanggay
    elif content == 'nsanggay':
        await message.channel.send("cái gì v mẹ <:0GDroolingCat:1525444808972308540>")

    # 8. Lệnh nban và nunban
# 8. Lệnh nban và nunban
    elif command_name in ['nban', 'nunban']:
        if message.author.id != ADMIN_ID:
            await message.channel.send("Bạn không có quyền này!")
            return

        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        # Kiểm tra xem có tag ai không
        if not message.mentions:
            await message.channel.send("Hãy tag người dùng cần xử lý (VD: `nban @user lí do`)!")
            return

        target = message.mentions[0]
        target_id = str(target.id)

        if command_name == 'nban':
            # Tách tin nhắn để lấy lí do
            parts = message.content.split(' ', 2)
            reason = parts[2] if len(parts) > 2 else "không có lí do"

            if target_id in blacklist:
                await message.channel.send("Người này đã bị cấm trước đó rồi!")
            else:
                blacklist[target_id] = reason
                
                # Gửi vào kênh log
                if log_channel:
                    await log_channel.send(
                        f"🚫 **LOG BAN**\n"
                        f"- Người bị ban: {target.mention}\n"
                        f"- Người thực hiện: {message.author.mention}\n"
                        f"- Lí do: {reason}"
                    )
                # Phản hồi tại kênh hiện tại
                await message.channel.send(f"bạn đã ban {target.mention} với lí do {reason}")

        elif command_name == 'nunban':
            if target_id not in blacklist:
                await message.channel.send("Người này hiện không bị cấm!")
            else:
                del blacklist[target_id]
                
                # Gửi vào kênh log
                if log_channel:
                    await log_channel.send(
                        f"✅ **LOG UNBAN**\n"
                        f"- Người được gỡ ban: {target.mention}\n"
                        f"- Người thực hiện: {message.author.mention}"
                    )
                # Phản hồi tại kênh hiện tại
                await message.channel.send(f"Đã gỡ ban cho {target.mention}")

        elif content == "ngive":
            if not message.mentions:
                await message.channel.send("❌ Cú pháp không hợp lệ. Ví dụ: `ngive @user 100k gold")
                return

                 
bot.run(os.environ['DISCORD_TOKEN'])
