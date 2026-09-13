import sys
import logging
import discord
from discord.ext import commands
import config
import ai_brain
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AyakaBot")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def setup_hook():
    # Khởi tạo database trước tiên
    from database import db_manager
    await db_manager.init_db()
    
    initial_extensions = [
        'music_cog',
        'sys_cog',
        'game_cog',
        'image_cog',
        'rag_cog',
        'level_cog' # Load hệ thống level
    ]
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f"Đã tải module {extension} thành công!")
        except Exception as e:
            logger.error(f"Lỗi khi tải module {extension}: {e}")

from web_dashboard import start_web_server

@bot.event
async def on_ready():
    """Kích hoạt khi bot kết nối thành công đến Discord."""
    logger.info("=" * 50)
    logger.info(f"🌸 Kamisato Ayaka đã thức giấc! Đăng nhập với tên: {bot.user} (ID: {bot.user.id})")
    logger.info(f"🌸 Đang có mặt tại {len(bot.guilds)} máy chủ:")
    for guild in bot.guilds:
        logger.info(f"   - {guild.name} (ID: {guild.id})")
    logger.info("=" * 50)

    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name="tiếng tuyết rơi & gió Inazuma 🌸❄️"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)
    
    # Khởi động Web Dashboard Server (Không block luồng chính)
    bot.loop.create_task(start_web_server(bot, port=928))

async def send_split_message(channel: discord.abc.Messageable, text: str, reference=None):
    """Gửi tin nhắn an toàn, tự động chia nhỏ nếu vượt quá 1900 ký tự của Discord."""
    max_len = 1900
    text = text.strip()
    if not text:
        return

    chunks = []
    current_chunk = ""

    for line in text.split("\n"):
        while len(line) > max_len:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            chunks.append(line[:max_len])
            line = line[max_len:]

        if len(current_chunk) + len(line) + 1 > max_len:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    first_sent = False
    for chunk in chunks:
        if not chunk:
            continue
        try:
            if not first_sent and reference:
                await channel.send(chunk, reference=reference)
                first_sent = True
            else:
                await channel.send(chunk)
        except Exception as e:
            logger.error(f"Lỗi khi gửi đoạn tin nhắn: {e}")

@bot.event
async def on_message(message: discord.Message):
    """Xử lý tin nhắn đến."""
    if message.author.bot:
        return

    await bot.process_commands(message)

    is_mentioned = bot.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_reply_to_ayaka = False

    if message.reference and message.reference.resolved:
        resolved_msg = message.reference.resolved
        if isinstance(resolved_msg, discord.Message) and resolved_msg.author.id == bot.user.id:
            is_reply_to_ayaka = True

    if is_mentioned or is_dm or is_reply_to_ayaka:
        if message.content.strip().startswith("!"):
            return

        clean_content = message.clean_content
        clean_content = clean_content.replace(f"@{bot.user.display_name}", "").strip()

        if not clean_content:
            await message.reply("Cậu gọi Ayaka có việc gì cần tớ tương trợ không? 🌸")
            return

        async with message.channel.typing():
            author_name = message.author.display_name
            reply_text = await ai_brain.ask_ayaka(
                channel_id=message.channel.id,
                user_name=author_name,
                message_text=clean_content
            )

        await send_split_message(message.channel, reply_text, reference=message)

@bot.command(name="ping")
async def ping(ctx: commands.Context):
    """Kiểm tra độ trễ của bot."""
    latency = round(bot.latency * 1000)
    await ctx.reply(f"🌸 Độ trễ tâm thức của Ayaka hiện tại là: **{latency}ms**.")

@bot.command(name="reset", aliases=["clear"])
async def reset_memory(ctx: commands.Context):
    """Xóa ký ức cuộc trò chuyện trong kênh này để bắt đầu chủ đề mới."""
    await ai_brain.clear_history(ctx.channel.id)
    await ctx.reply("❄️ Ayaka đã khép lại trang ký ức cũ trong cuộc đàm đạo này. Chúng ta hãy cùng bắt đầu một câu chuyện mới nhé cậu! 🍵")

@bot.command(name="help_ayaka")
async def help_command(ctx: commands.Context):
    """Hướng dẫn tương tác với Ayaka."""
    help_text = (
        "🌸 **Hướng Dẫn Trò Chuyện Cùng Kamisato Ayaka** 🌸\n\n"
        "• **Trò chuyện tự nhiên:** Chỉ cần `@Kamisato Ayaka <nội dung>` hoặc bấm *Reply* vào tin nhắn của tớ.\n"
        "• **Nhắn tin riêng (DM):** Nhắn trực tiếp cho Ayaka, tớ sẽ lắng nghe và đối đáp mọi lúc.\n"
        "• **`!reset` hoặc `!clear`:** Làm mới bộ nhớ hội thoại để đổi chủ đề.\n"
        "• **`!ping`:** Xem độ trễ kết nối.\n"
        "\n*Ayaka luôn sẵn lòng đồng hành cùng cậu trên mọi nẻo đường!* ❄️"
    )
    await ctx.reply(help_text)

if __name__ == "__main__":
    logger.info("Đang khởi động Kamisato Ayaka...")
    bot.run(config.DISCORD_BOT_TOKEN)
