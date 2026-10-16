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
        font_title = self._load_font(40)
        font_desc = self._load_font(30)

        # Text name
        draw.text((260, 100), f"Welcome to the Server!", fill=(255, 255, 255), font=font_title)
        draw.text((260, 160), str(member.name), fill=(45, 49, 118), font=font_desc)
        
        # Lưu ra byte array
        final_buffer = BytesIO()
        base.save(final_buffer, format="PNG")
        final_buffer.seek(0)
        
        return discord.File(fp=final_buffer, filename="welcome.png")

    def _load_font(self, size: int):
        """Render (Linux) không có arial.ttf, thử lần lượt các font phổ biến rồi tới font mặc định có scale."""
        for name in ("arial.ttf", "DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        try:
            return ImageFont.load_default(size=size)  # Pillow >= 10.1
        except TypeError:
            return ImageFont.load_default()

    def _find_welcome_channel(self, guild: discord.Guild):
        """Ưu tiên System Channel; nếu server chưa đặt thì tìm kênh có tên chào mừng/chung."""
        def can_send(ch):
            return ch is not None and ch.permissions_for(guild.me).send_messages

        if can_send(guild.system_channel):
            return guild.system_channel
        keywords = ("chào-mừng", "chao-mung", "welcome", "sảnh", "chung", "general")
        for kw in keywords:
            for ch in guild.text_channels:
                if kw in ch.name.lower() and can_send(ch):
                    return ch
        for ch in guild.text_channels:
            if can_send(ch):
                return ch
        return None

    async def send_welcome(self, member: discord.Member, channel=None):
        channel = channel or self._find_welcome_channel(member.guild)
        if not channel:
            logger.warning(f"Không tìm thấy kênh nào để gửi lời chào ở {member.guild.name}")
            return
        if not HAS_PIL:
            await channel.send(f"🌸 Chào mừng **{member.mention}** đã đến với **{member.guild.name}**! Chúc cậu có những giây phút vui vẻ nhé!")
            return
        try:
            card = await self.create_welcome_card(member)
            await channel.send(f"🌸 Chào mừng **{member.mention}** đã đến với **{member.guild.name}**! Hãy đọc luật và trò chuyện cùng mọi người nhé!", file=card)
        except Exception as e:
            logger.error(f"Lỗi gửi thiệp welcome: {e}")
            await channel.send(f"🌸 Chào mừng **{member.mention}** đã đến với **{member.guild.name}**!")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.info(f"Thành viên mới: {member.name} tham gia {member.guild.name}")
        await self.send_welcome(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = self._find_welcome_channel(member.guild)
        if channel:
            await channel.send(f"🍃 **{member.name}** đã rời khỏi máy chủ. Hẹn gặp lại nhé!")

    @commands.command(name="testwelcome")
    @commands.has_permissions(manage_guild=True)
    async def testwelcome(self, ctx):
        """(Admin) Xem trước thiệp chào mừng ngay tại kênh hiện tại."""
        await self.send_welcome(ctx.author, channel=ctx.channel)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
