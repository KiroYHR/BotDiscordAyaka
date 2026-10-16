import discord
from discord.ext import commands
import asyncio
import logging
import os
import random
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import aiohttp
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger("AyakaWelcome")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT_DIR, "assets", "fonts")
ART_PATH = os.path.join(ROOT_DIR, "web", "dashboard", "assets", "emojis", "ayaka_model.png")
CARD_W, CARD_H = 1100, 400


def load_font(weight: str, size: int):
    """Font Be Vietnam Pro đi kèm repo (hỗ trợ đầy đủ tiếng Việt, không phụ thuộc font hệ thống)."""
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, f"BeVietnamPro-{weight}.ttf"), size)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


def _fit_text(draw, text, weight, max_size, min_size, max_width):
    """Thu nhỏ cỡ chữ cho vừa khung, nếu vẫn dài thì cắt kèm dấu …"""
    for size in range(max_size, min_size - 1, -2):
        font = load_font(weight, size)
        if draw.textlength(text, font=font) <= max_width:
            return text, font
    font = load_font(weight, min_size)
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1]
    return text + "…", font


def render_welcome_card(avatar_bytes, display_name: str, username: str, guild_name: str, member_count: int) -> bytes:
    W, H = CARD_W, CARD_H
    rnd = random.Random(username)  # tuyết rơi cố định theo user cho ổn định

    # 1) Nền gradient đêm Inazuma (xanh đậm -> tím lam -> xanh băng)
    grad = Image.new("RGB", (W, 1))
    stops = [(0.0, (18, 22, 58)), (0.55, (52, 60, 128)), (1.0, (140, 196, 232))]
    for x in range(W):
        t = x / (W - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                grad.putpixel((x, 0), tuple(int(c0[i] + (c1[i] - c0[i]) * k) for i in range(3)))
                break
    card = grad.resize((W, H)).convert("RGBA")

    # 2) Ảnh Ayaka bên phải, mờ dần sang trái
    try:
        art = Image.open(ART_PATH).convert("RGBA")
        scale = (H * 1.55) / art.height
        art = art.resize((int(art.width * scale), int(art.height * scale)), Image.LANCZOS)
        art = art.crop((0, int(art.height * 0.08), art.width, int(art.height * 0.08) + H))
        fade = Image.new("L", art.size, 0)
        fd = ImageDraw.Draw(fade)
        for x in range(art.width):
            fd.line([(x, 0), (x, H)], fill=int(235 * min(1, (x / (art.width * 0.55)) ** 1.6)))
        art.putalpha(Image.composite(art.getchannel("A"), Image.new("L", art.size, 0), fade))
        card.alpha_composite(art, (W - art.width + 30, 0))
    except Exception as e:
        logger.warning(f"Không tải được ảnh Ayaka cho thiệp: {e}")

    # 3) Tuyết rơi lấp lánh
    snow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(snow)
    for _ in range(70):
        x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([1, 1, 2, 2, 3])
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rnd.randint(90, 200)))
    card.alpha_composite(snow.filter(ImageFilter.GaussianBlur(0.8)))

    # 4) Tấm kính mờ (glass panel)
    panel_box = (30, 30, 770, H - 30)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle(panel_box, radius=28, fill=(255, 255, 255, 26), outline=(255, 255, 255, 70), width=2)
    card.alpha_composite(panel)

    # 5) Avatar tròn + vòng gradient phát sáng
    AV, cx, cy = 210, 70 + 105, H // 2
    ring = AV + 16
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((cx - ring // 2 - 14, cy - ring // 2 - 14, cx + ring // 2 + 14, cy + ring // 2 + 14),
                                 fill=(150, 210, 255, 150))
    card.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))

    ring_img = Image.new("RGBA", (ring, ring), (0, 0, 0, 0))
    rg = Image.linear_gradient("L").rotate(45).resize((ring, ring))
    ring_color = Image.composite(Image.new("RGBA", (ring, ring), (255, 182, 213, 255)),
                                 Image.new("RGBA", (ring, ring), (140, 210, 255, 255)), rg)
    ring_mask = Image.new("L", (ring, ring), 0)
    ImageDraw.Draw(ring_mask).ellipse((0, 0, ring - 1, ring - 1), fill=255)
    ring_img.paste(ring_color, (0, 0), ring_mask)
    card.alpha_composite(ring_img, (cx - ring // 2, cy - ring // 2))

    try:
        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA") if avatar_bytes else None
    except Exception:
        avatar = None
    if avatar is None:
        avatar = Image.new("RGBA", (AV, AV), (88, 101, 242, 255))
    avatar = avatar.resize((AV * 2, AV * 2), Image.LANCZOS)  # vẽ 2x rồi thu nhỏ cho viền mượt
    m = Image.new("L", (AV * 2, AV * 2), 0)
    ImageDraw.Draw(m).ellipse((0, 0, AV * 2 - 1, AV * 2 - 1), fill=255)
    avatar.putalpha(m)
    avatar = avatar.resize((AV, AV), Image.LANCZOS)
    card.alpha_composite(avatar, (cx - AV // 2, cy - AV // 2))

    # 6) Chữ (vẽ trên lớp trong suốt rồi ghép để độ mờ hòa trộn đúng)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    tx, text_w = 320, 430
    d.text((tx, 92), "C H À O   M Ừ N G", font=load_font("Bold", 22), fill=(170, 220, 255, 255))
    name, name_font = _fit_text(d, display_name, "ExtraBold", 58, 30, text_w)
    d.text((tx + 2, 165 + 3), name, font=name_font, fill=(10, 12, 40, 140), anchor="lm")
    d.text((tx, 165), name, font=name_font, fill=(255, 255, 255, 255), anchor="lm")
    sub, sub_font = _fit_text(d, f"đã đến với {guild_name}", "Medium", 26, 18, text_w)
    d.text((tx, 208), sub, font=sub_font, fill=(225, 232, 255, 255))

    badge_font = load_font("Bold", 20)
    badge = f"Thành viên thứ #{member_count}"
    bw = int(d.textlength(badge, font=badge_font)) + 40
    d.rounded_rectangle((tx, 262, tx + bw, 302), radius=20, fill=(255, 182, 213, 55), outline=(255, 182, 213, 200), width=2)
    d.text((tx + bw // 2, 282), badge, font=badge_font, fill=(255, 225, 238, 255), anchor="mm")

    d.text((tx, H - 62), f"@{username}", font=load_font("Medium", 18), fill=(190, 200, 235, 255))
    card.alpha_composite(overlay)

    out = BytesIO()
    card.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()


class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def create_welcome_card(self, member: discord.Member) -> discord.File:
        """Tải avatar rồi vẽ thiệp trong thread riêng để không chặn bot."""
        avatar_bytes = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(member.display_avatar.replace(size=512, format="png").url),
                                       timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        avatar_bytes = await resp.read()
        except Exception as e:
            logger.error(f"Lỗi tải avatar welcome: {e}")

        png = await asyncio.get_running_loop().run_in_executor(
            None, render_welcome_card, avatar_bytes, member.display_name, member.name,
            member.guild.name, member.guild.member_count or len(member.guild.members))
        return discord.File(fp=BytesIO(png), filename="welcome.png")

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
