import discord
from discord.ext import commands
import logging
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import aiohttp
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger("AyakaWelcome")

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def create_welcome_card(self, member: discord.Member) -> discord.File:
        """Tạo thẻ chào mừng bằng PIL."""
        # Kích thước thẻ
        width, height = 800, 300
        
        # Nền (Tạo màu gradient hoặc màu tĩnh đơn giản)
        base = Image.new("RGBA", (width, height), (138, 203, 235, 255)) # Cyan nhạt
        
        draw = ImageDraw.Draw(base)
        
        # Viền
        draw.rectangle([10, 10, width-10, height-10], outline=(255, 255, 255, 255), width=3)
        
        # Tải avatar
        avatar_size = 180
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(avatar_url)) as resp:
                    if resp.status == 200:
                        avatar_data = await resp.read()
                        avatar_img = Image.open(BytesIO(avatar_data)).convert("RGBA")
                        avatar_img = avatar_img.resize((avatar_size, avatar_size))
                        
                        # Làm tròn avatar
                        mask = Image.new("L", (avatar_size, avatar_size), 0)
                        mask_draw = ImageDraw.Draw(mask)
                        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                        avatar_img.putalpha(mask)
                        
                        # Dán avatar vào nền
                        base.paste(avatar_img, (50, 60), avatar_img)
        except Exception as e:
            logger.error(f"Lỗi tải avatar welcome: {e}")
            
        # Thêm text
        try:
            # Nếu có font tùy chỉnh thì load, không thì dùng font mặc định
            font_title = ImageFont.truetype("arial.ttf", 40)
            font_desc = ImageFont.truetype("arial.ttf", 30)
        except:
            font_title = ImageFont.load_default()
            font_desc = ImageFont.load_default()

        # Text name
        draw.text((260, 100), f"Welcome to the Server!", fill=(255, 255, 255), font=font_title)
        draw.text((260, 160), str(member.name), fill=(45, 49, 118), font=font_desc)
        
        # Lưu ra byte array
        final_buffer = BytesIO()
        base.save(final_buffer, format="PNG")
        final_buffer.seek(0)
        
        return discord.File(fp=final_buffer, filename="welcome.png")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.info(f"Thành viên mới: {member.name} tham gia {member.guild.name}")
        
        if not HAS_PIL:
            logger.warning("Không có thư viện Pillow, bỏ qua việc tạo thiệp chào mừng.")
            # Gửi tin nhắn text bình thường nếu không có PIL
            channel = member.guild.system_channel
            if channel:
                await channel.send(f"🌸 Chào mừng **{member.name}** đã đến với {member.guild.name}! Chúc cậu có những giây phút vui vẻ nhé!")
            return
            
        channel = member.guild.system_channel
        if channel:
            try:
                card = await self.create_welcome_card(member)
                await channel.send(f"🌸 Chào mừng **{member.mention}** đã đến với **{member.guild.name}**! Hãy đọc luật và trò chuyện cùng mọi người nhé!", file=card)
            except Exception as e:
                logger.error(f"Lỗi gửi thiệp welcome: {e}")
                await channel.send(f"🌸 Chào mừng **{member.mention}** đã đến với **{member.guild.name}**!")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = member.guild.system_channel
        if channel:
            await channel.send(f"🍃 **{member.name}** đã rời khỏi máy chủ. Hẹn gặp lại nhé!")

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
