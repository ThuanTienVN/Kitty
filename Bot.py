import os
import discord
import random
import secrets
from datetime import datetime, timedelta
from discord.ext import commands
from flask import Flask
from threading import Thread
import aiosqlite
import asyncio

# --- Định nghĩa hàm tạo Database trước ---
async def init_db():
    async with aiosqlite.connect("database.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 0
            )
        """)
        await db.commit()

# --- Khởi tạo Flask App cho Web Server ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot đang chạy!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- Biến lưu trữ & Cấu hình ID ---
ADMIN_ID = 1517328324618096711
LOG_CHANNEL_ID = 1540982626364559370

inventory = {}
fish_storage = {}
daily_check = {}
cooldown_check = {}
blacklist = {}
gift_codes = {}

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)


@bot.event
async def on_ready():
    # Tự động tạo file database.db ngay khi bot vừa khởi động
    await init_db()
    print(f'Bot {bot.user} đã sẵn sàng và Database đã được tạo!')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = str(message.author.id)
    content = message.content.lower().strip()

    if not content:
        return

    # Lấy command đầu tiên trong tin nhắn
    command_name = content.split()[0]

    bot_commands = [
        'nhelp',
        'ncauca',
        'nfish',
        'nbanca',
        'nme',
        'ndaily',
        'nban',
        'nunban',
        'nsanggay',
        'ntaogiftcode',
        'ngiftcode',
        'nuser',
        'meow',
        'bum',
        'chim',
        'khoan',
        'job',
        'njob',
        'bruh'
    ]

    # --- Danh sách các lệnh kinh tế/tương tác sẽ bị cấm khi bị ban ---
    restricted_commands = ['ncauca', 'nfish', 'nbanca', 'nme', 'ndaily', 'ngiftcode']

    # --- Kiểm tra Blacklist ---
    if user_id in blacklist:
        if command_name in bot_commands:
            if command_name in restricted_commands:
                reason = blacklist[user_id]
                await message.channel.send(
                    f"{message.author.mention} Bạn đã bị ban bởi Admin với lí do: `{reason}` nên không thể sử dụng lệnh này!"
                )
            else:
                reason = blacklist[user_id]
                await message.channel.send(
                    f"{message.author.mention} đã bị ban bởi Admin với lí do {reason}"
                )
        return

    now = datetime.now()

    # 1. Lệnh nhelp
    if command_name == 'nhelp':
        await message.channel.send(
            "📋 **Danh sách lệnh:**\n"
            "`ncauca`: Câu cá (Cooldown 3p)\n"
            "`nfish`: Xem số cá chưa bán\n"
            "`nbanca`: Bán toàn bộ cá lấy coin\n"
            "`nme`: Xem thông tin của bản thân\n"
            "`ndaily`: Nhận coin mỗi ngày\n"
            "`ngiftcode <mã>`: Đổi giftcode\n"
            "`nuser @user`: Xem thông tin người dùng\n"
        )

    # 2. Lệnh ncauca
    elif command_name == 'ncauca':
        last_time = cooldown_check.get(user_id)

        if last_time and now < last_time:
            wait_time = int((last_time - now).total_seconds() / 60) + 1
            await message.channel.send(
                f"{message.author.mention} Bạn đang thấm mệt, "
                f"hãy nghỉ ngơi {wait_time} phút nữa rồi quay lại nhé!"
            )
        else:
            if random.random() < 0.3:
                rac = [
                    'một chiếc dép cũ',
                    'một cái áo rách',
                    'một mớ rác thải'
                ]
                await message.channel.send(
                    f'{message.author.mention} Bạn quăng cần xuống... '
                    f'và câu được {random.choice(rac)}. Chán thế!'
                )
            else:
                so_ca = random.randint(1, 10)
                fish_storage[user_id] = fish_storage.get(user_id, 0) + so_ca
                await message.channel.send(
                    f'{message.author.mention} Bạn câu được {so_ca} con cá! '
                    f'Dùng `nbanca` để bán nhé.'
                )

            cooldown_check[user_id] = now + timedelta(minutes=3)

    # 3. Lệnh nfish
    elif command_name == 'nfish':
        so_ca = fish_storage.get(user_id, 0)
        await message.channel.send(f"🐟 Bạn đang có {so_ca} con cá trong kho.")

    # 4. Lệnh nbanca
    elif command_name == 'nbanca':
        so_ca = fish_storage.get(user_id, 0)
        if so_ca > 0:
            coin = so_ca * 5
            inventory[user_id] = inventory.get(user_id, 0) + coin
            fish_storage[user_id] = 0
            await message.channel.send(
                f"Bạn đã bán {so_ca} con cá và nhận được {coin} coin! "
                f"Tổng số dư: {inventory[user_id]} coin."
            )
        else:
            await message.channel.send("Bạn không có cá để bán!")

    # 5. Lệnh nme
    elif command_name == 'nme':
        so_du = inventory.get(user_id, 0)
        await message.channel.send(f"💰 **Số dư của bạn:** {so_du} coin.")

    # 6. Lệnh ndaily
    elif command_name == 'ndaily':
        today = now.strftime("%Y-%m-%d")
        if daily_check.get(user_id) == today:
            await message.channel.send("Bạn đã nhận quà hôm nay rồi, mai quay lại nhé!")
        else:
            thuong = random.randint(1, 50)
            inventory[user_id] = inventory.get(user_id, 0) + thuong
            daily_check[user_id] = today
            await message.channel.send(
                f"Bạn nhận được {thuong} coin! "
                f"Tổng số dư: {inventory[user_id]} coin."
            )

    # 7. Lệnh nsanggay
    elif command_name == 'nsanggay':
        await message.channel.send("cái gì v mẹ <:0GDroolingCat:1525444808972308540>")

    # 8. Lệnh nban / nunban
    elif command_name in ['nban', 'nunban']:
        if message.author.id != ADMIN_ID:
            await message.channel.send("Bạn không có quyền này!")
            return

        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        if not message.mentions:
            await message.channel.send("Hãy tag người dùng cần xử lý (VD: `nban @user lí do`)!")
            return

        target = message.mentions[0]
        target_id = str(target.id)

        # --- BAN ---
        if command_name == 'nban':
            parts = message.content.split(' ', 2)
            reason = parts[2] if len(parts) > 2 else "không có lí do"

            if target_id in blacklist:
                await message.channel.send("Người này đã bị cấm trước đó rồi!")
            else:
                blacklist[target_id] = reason
                if log_channel:
                    await log_channel.send(
                        f"🚫 **LOG BAN**\n"
                        f"- Người bị ban: {target.mention}\n"
                        f"- Người thực hiện: {message.author.mention}\n"
                        f"- Lí do: {reason}"
                    )
                await message.channel.send(f"bạn đã ban {target.mention} với lí do {reason}")

        # --- UNBAN ---
        elif command_name == 'nunban':
            if target_id not in blacklist:
                await message.channel.send("Người này hiện không bị cấm!")
            else:
                del blacklist[target_id]
                if log_channel:
                    await log_channel.send(
                        f"✅ **LOG UNBAN**\n"
                        f"- Người được gỡ ban: {target.mention}\n"
                        f"- Người thực hiện: {message.author.mention}"
                    )
                await message.channel.send(f"Đã gỡ ban cho {target.mention}")

    # 9. Tạo giftcode
    elif command_name == 'ntaogiftcode':
        if message.author.id != ADMIN_ID:
            await message.channel.send("Bạn không có quyền này!")
            return

        parts = message.content.split()
        if len(parts) not in [2, 3] or not parts[1].isdigit():
            await message.channel.send(
                "Cú pháp: `ntaogiftcode <số coin> [số lượt đổi]`\n"
                "Ví dụ: `ntaogiftcode 100 5`"
            )
            return

        reward = int(parts[1])
        uses = int(parts[2]) if len(parts) == 3 and parts[2].isdigit() else None
        if reward <= 0 or (len(parts) == 3 and uses is None) or (uses is not None and uses <= 0):
            await message.channel.send("Số coin và số lượt đổi phải lớn hơn 0.")
            return

        code = f"MEOW-{secrets.token_hex(4).upper()}"
        gift_codes[code] = {"reward": reward, "uses_left": uses}
        uses_text = "không giới hạn" if uses is None else str(uses)
        await message.channel.send(
            f"Đã tạo giftcode: `{code}`\n"
            f"Phần thưởng: **{reward} coin** | Lượt đổi: **{uses_text}**"
        )

    # 10. Đổi giftcode
    elif command_name == 'ngiftcode':
        parts = message.content.split()
        if len(parts) != 2:
            await message.channel.send("Cú pháp: `ngiftcode <mã>`")
            return

        code = parts[1].upper()
        giftcode = gift_codes.get(code)
        if giftcode is None:
            await message.channel.send("Giftcode không tồn tại hoặc đã hết hạn.")
            return

        if giftcode["uses_left"] is not None:
            if user_id in giftcode.get("claimed_by", set()):
                await message.channel.send("Bạn đã đổi giftcode này rồi!")
                return
            giftcode.setdefault("claimed_by", set()).add(user_id)
            giftcode["uses_left"] -= 1

        inventory[user_id] = inventory.get(user_id, 0) + giftcode["reward"]
        await message.channel.send(
            f"🎁 Bạn đã đổi giftcode thành công và nhận được "
            f"**{giftcode['reward']} coin**! Tổng số dư: {inventory[user_id]} coin."
        )

        if giftcode["uses_left"] == 0:
            del gift_codes[code]

    # 11. Job command
    elif command_name in ['job', 'njob']:
        await message.channel.send("Đi kiếm việc làm đi, bot ko có chức năng đó! :h_:")

    # 12. Lệnh nuser
    elif command_name == 'nuser':
        await message.channel.send("đang tét")

    # Lệnh xàm
    elif command_name == 'meow':
        if os.path.exists("meow.png"):
            await message.channel.send(file=discord.File("meow.png"))

    elif command_name == 'bruh':
        if os.path.exists("bruh.png"):
            await message.channel.send(file=discord.File("bruh.png"))

    elif command_name == 'ntilgay':
        await message.channel.send("Đúng thật <:meomeo:1541455263507153046>")

    elif command_name == 'bum':
        await message.channel.send("https://cdn.discordapp.com/attachments/1505482821580619918/1537259392603258970/buhflipexplode.gif")

    elif command_name == 'chim':
        await message.channel.send("https://klipy.com/gifs/bung-chim")

    elif command_name == 'khoan':
        await message.channel.send("https://cdn.discordapp.com/attachments/1050078382018265178/1454397083413909630/ezgif-395a166e2e34663d.gif")


# --- Điểm khởi chạy chính của chương trình (Đặt ở ngoài cùng, không nằm trong hàm on_message) ---
if __name__ == '__main__':
    # Chạy Web Server ngầm cho host (HidenCloud/Render)
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

    # Chạy bot Discord (Thay token của bạn vào đây hoặc dùng os.environ)
token = os.getenv('DISCORD_TOKEN')
client.run(token)
