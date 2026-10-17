import discord
from discord.ext import commands
import logging
import time
import random
from data.database import db_manager
from core import config

logger = logging.getLogger("AyakaLevel")

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {} # {user_id: last_message_timestamp}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
            
        if message.content.startswith("!"):
            return

        user_id = str(message.author.id)
        now = time.time()
        
        # Cooldown 60s để chống spam
        if now - self.cooldowns.get(user_id, 0) < 60:
            return
            
        self.cooldowns[user_id] = now
        
        # Nhận cố định 5 EXP mỗi tin nhắn (Cooldown 1 phút)
        exp_to_add = 5
        
        try:
            result = await db_manager.add_exp(user_id, exp_to_add)
            if result.get("leveled_up"):
                new_level = result["new_level"]
                embed = discord.Embed(
                    title="🎉 Lên Cấp!", 
                    description=f"Chúc mừng {message.author.mention}! Cậu vừa đột phá lên **Cấp {new_level}**! 🌸",
                    color=discord.Color.gold()
                )
                await message.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Lỗi khi cộng EXP: {e}")

    @commands.command(name="reset_exp_all")
    @commands.has_permissions(administrator=True)
    async def reset_exp_all(self, ctx):
        """(Admin) Xóa toàn bộ điểm EXP của tất cả mọi người."""
        if not db_manager.pool:
            await ctx.reply("❌ Không thể kết nối đến cơ sở dữ liệu.")
            return
            
        try:
            async with db_manager.pool.acquire() as db:
                await db.execute('DELETE FROM users')
            await ctx.reply("✅ Đã reset toàn bộ điểm EXP của tất cả Nhà Lữ Hành về 0!")
        except Exception as e:
            logger.error(f"Lỗi khi reset EXP: {e}")
            await ctx.reply("❌ Đã xảy ra lỗi khi reset EXP.")

    @commands.command(name="daily", aliases=["diemdanh"])
    async def check_daily(self, ctx):
        """Điểm danh mỗi ngày để nhận điểm Hảo Cảm với Ayaka."""
        try:
            result = await db_manager.claim_daily(str(ctx.author.id))
            if result.get("success"):
                streak = result["streak"]
                affection = result["affection"]
                gained = result["affection_gained"]
                primos = result.get("primos_gained", 160)
                
                embed = discord.Embed(
                    title="💖 Điểm Danh Thành Công!",
                    description=f"Ayaka rất vui vì hôm nay lại được gặp {ctx.author.mention}! 🌸\nCậu vừa nhận được **{gained} Điểm Hảo Cảm** và **{primos} 💎 Nguyên Thạch**.",
                    color=discord.Color.brand_red()
                )
                embed.add_field(name="🔥 Chuỗi Điểm Danh", value=f"**{streak} ngày**", inline=True)
                embed.add_field(name="💖 Tổng Hảo Cảm", value=f"**{affection} trái tim**", inline=True)
                embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
                await ctx.reply(embed=embed)
            else:
                await ctx.reply(f"❌ {result.get('msg')}")
        except Exception as e:
            logger.error(f"Lỗi khi điểm danh: {e}")
            await ctx.reply("❌ Không thể điểm danh lúc này, có chút lỗi xảy ra cậu ạ.")

    @commands.command(name="monthly", aliases=["thang"])
    async def check_monthly(self, ctx):
        """Nhận quà ưu đãi hàng tháng (1600 Nguyên Thạch)."""
        try:
            result = await db_manager.claim_monthly(str(ctx.author.id))
            if result.get("success"):
                primos = result.get("primos_gained", 1600)
                await ctx.reply(f"🎁 {ctx.author.mention} đã nhận được **{primos} Nguyên Thạch** từ phần quà ưu đãi hằng tháng! 💎 (Tương đương 10 lượt quay)")
            else:
                await ctx.reply(f"❌ {result.get('msg')}")
        except Exception as e:
            logger.error(f"Lỗi khi nhận monthly: {e}")
            await ctx.reply("❌ Không thể nhận quà lúc này, có chút lỗi xảy ra cậu ạ.")

import os
import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT_DIR, "assets", "fonts")
ART_PATH = os.path.join(ROOT_DIR, "web", "dashboard", "assets", "emojis", "ayaka_model.png")
CARD_W, CARD_H = 1050, 360

def load_font(weight: str, size: int):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, f"BeVietnamPro-{weight}.ttf"), size)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

def _fit_text(draw, text, weight, max_size, min_size, max_width):
    for size in range(max_size, min_size - 1, -2):
        font = load_font(weight, size)
        if draw.textlength(text, font=font) <= max_width:
            return text, font
    font = load_font(weight, min_size)
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1]
    return text + "…", font

def render_rank_card(avatar_bytes, display_name: str, username: str, rank_str: str, level: int, exp: int, exp_in_level: int, exp_needed: int, primogems: int) -> bytes:
    W, H = CARD_W, CARD_H
    rnd = random.Random(username)

    # 1) Nền gradient đêm Inazuma
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
        if os.path.exists(ART_PATH):
            art = Image.open(ART_PATH).convert("RGBA")
            scale = (H * 1.5) / art.height
            art = art.resize((int(art.width * scale), int(art.height * scale)), Image.LANCZOS)
            art = art.crop((0, int(art.height * 0.08), art.width, int(art.height * 0.08) + H))
            fade = Image.new("L", art.size, 0)
            fd = ImageDraw.Draw(fade)
            for x in range(art.width):
                fd.line([(x, 0), (x, H)], fill=int(220 * min(1, (x / (art.width * 0.6)) ** 1.6)))
            art.putalpha(Image.composite(art.getchannel("A"), Image.new("L", art.size, 0), fade))
            card.alpha_composite(art, (W - art.width + 30, 0))
    except Exception as e:
        logger.warning(f"Lỗi load art cho rank: {e}")

    # 3) Tuyết rơi lấp lánh
    snow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(snow)
    for _ in range(60):
        x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([1, 1, 2, 2])
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rnd.randint(80, 190)))
    card.alpha_composite(snow.filter(ImageFilter.GaussianBlur(0.8)))

    # 4) Tấm kính mờ (glass panel)
    panel_box = (25, 25, 760, H - 25)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle(panel_box, radius=24, fill=(255, 255, 255, 24), outline=(255, 255, 255, 65), width=2)
    card.alpha_composite(panel)

    # 5) Avatar tròn + vòng phát sáng
    AV, cx, cy = 170, 55 + 85, H // 2 - 15
    ring = AV + 14
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((cx - ring//2 - 12, cy - ring//2 - 12, cx + ring//2 + 12, cy + ring//2 + 12), fill=(140, 205, 255, 140))
    card.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))

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
    avatar = avatar.resize((AV * 2, AV * 2), Image.LANCZOS)
    m = Image.new("L", (AV * 2, AV * 2), 0)
    ImageDraw.Draw(m).ellipse((0, 0, AV * 2 - 1, AV * 2 - 1), fill=255)
    avatar.putalpha(m)
    avatar = avatar.resize((AV, AV), Image.LANCZOS)
    card.alpha_composite(avatar, (cx - AV // 2, cy - AV // 2))

    # Badge Level dưới Avatar
    lvl_badge = f"Lv. {level}"
    bf = load_font("Bold", 18)
    bw = int(ImageDraw.Draw(card).textlength(lvl_badge, font=bf)) + 30
    bx = cx - bw // 2
    by = cy + AV // 2 - 10
    lvl_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lvl_img)
    ld.rounded_rectangle((bx, by, bx + bw, by + 30), radius=15, fill=(45, 55, 130, 240), outline=(255, 182, 213, 220), width=2)
    ld.text((cx, by + 15), lvl_badge, font=bf, fill=(255, 235, 245), anchor="mm")
    card.alpha_composite(lvl_img)

    # 6) Chữ & Thông số
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    tx = 265

    # Header
    d.text((tx, 45), "H Ồ   S Ơ   R È N   L U Y Ệ N", font=load_font("Bold", 18), fill=(170, 220, 255, 255))
    
    # Tên & Username
    name, name_font = _fit_text(d, display_name, "ExtraBold", 42, 26, 310)
    d.text((tx + 2, 92 + 2), name, font=name_font, fill=(10, 12, 40, 140), anchor="lm")
    d.text((tx, 92), name, font=name_font, fill=(255, 255, 255, 255), anchor="lm")
    
    # Thứ hạng badge bên cạnh tên
    rank_badge = f"Thứ Hạng {rank_str}"
    rf = load_font("Bold", 18)
    rw = int(d.textlength(rank_badge, font=rf)) + 24
    rx = 740 - rw
    d.rounded_rectangle((rx, 75, 740, 107), radius=16, fill=(255, 215, 0, 45), outline=(255, 215, 0, 180), width=2)
    d.text((rx + rw // 2, 91), rank_badge, font=rf, fill=(255, 235, 140, 255), anchor="mm")

    d.text((tx, 125), f"@{username}", font=load_font("Medium", 16), fill=(190, 200, 235, 255))

    # Hàng chỉ số (Kinh Nghiệm & Nguyên Thạch)
    stat_box_y = 155
    d.text((tx, stat_box_y), "Kinh Nghiệm:", font=load_font("Medium", 16), fill=(210, 220, 245, 255))
    d.text((tx + 120, stat_box_y), f"{exp:,} EXP", font=load_font("Bold", 18), fill=(255, 255, 255, 255))

    d.text((tx + 260, stat_box_y), "Nguyên Thạch:", font=load_font("Medium", 16), fill=(210, 220, 245, 255))
    d.text((tx + 390, stat_box_y), f"{primogems:,} 💎", font=load_font("Bold", 18), fill=(100, 240, 255, 255))

    # Thanh tiến trình EXP
    bar_x, bar_y, bar_w, bar_h = tx, 205, 475, 24
    # Nền thanh
    d.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=12, fill=(10, 15, 40, 180), outline=(255, 255, 255, 60), width=1)
    
    pct = max(0.0, min(1.0, exp_in_level / exp_needed if exp_needed > 0 else 1.0))
    fill_w = int(bar_w * pct)
    if fill_w > 8:
        bar_fill = Image.new("RGBA", (fill_w, bar_h), (0, 0, 0, 0))
        bf_draw = ImageDraw.Draw(bar_fill)
        bf_draw.rounded_rectangle((0, 0, fill_w, bar_h), radius=12, fill=(140, 210, 255, 255))
        overlay.alpha_composite(bar_fill, (bar_x, bar_y))

    # Text % và EXP trong/dưới thanh
    pct_text = f"{int(pct * 100)}%"
    d.text((bar_x + bar_w - 5, bar_y + 12), pct_text, font=load_font("Bold", 14), fill=(255, 255, 255, 255), anchor="rm")
    
    sub_exp = f"{exp_in_level:,} / {exp_needed:,} EXP để đột phá cấp tiếp theo"
    d.text((bar_x, bar_y + 36), sub_exp, font=load_font("Medium", 15), fill=(200, 215, 245, 230))

    card.alpha_composite(overlay)

    out = BytesIO()
    card.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()

    @commands.command(name="rank", aliases=["level", "capdo"])
    async def check_rank(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        
        try:
            profile = await db_manager.get_user_profile(str(target.id))
            level = profile.get("level", 1) if profile else 1
            exp = profile.get("exp", 0) if profile else 0
            primogems = profile.get("primogems", 0) if profile else 0
            
            # Lấy top users để tìm thứ hạng (Rank)
            top_users = await db_manager.get_top_users(limit=1000)
            rank = "?"
            for i, u in enumerate(top_users):
                if u["user_id"] == str(target.id):
                    rank = f"#{i + 1}"
                    break
            
            if rank == "?":
                rank = f"#{len(top_users) + 1}"
            
            # Tính toán EXP cần thiết cho cấp tiếp theo
            current_level_base_exp = int(25 * (level - 1) * (level + 2))
            next_level_base_exp = int(25 * level * (level + 3))
            
            exp_in_current_level = max(0, exp - current_level_base_exp)
            exp_needed = max(1, next_level_base_exp - current_level_base_exp)
            
            # Tải avatar
            avatar_bytes = None
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(target.display_avatar.replace(size=512, format="png").url),
                                           timeout=aiohttp.ClientTimeout(total=8)) as resp:
                        if resp.status == 200:
                            avatar_bytes = await resp.read()
            except Exception as e:
                logger.warning(f"Lỗi tải avatar cho rank card: {e}")
                
            png_bytes = await asyncio.get_running_loop().run_in_executor(
                None, render_rank_card, avatar_bytes, target.display_name, target.name,
                rank, level, exp, exp_in_current_level, exp_needed, primogems
            )
            
            rank_file = discord.File(fp=BytesIO(png_bytes), filename="rank.png")
            
            # Nút Xem Leaderboard trên Web
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Xem Bảng Xếp Hạng Đầy Đủ", url=f"{config.WEB_BASE_URL}/#leaderboard", emoji="🌐"))
            
            await ctx.reply(file=rank_file, view=view)
        except Exception as e:
            logger.error(f"Lỗi kiểm tra rank: {e}")
            await ctx.reply("❌ Không thể tra cứu thông tin cấp độ lúc này cậu ạ.")

async def setup(bot):
    await bot.add_cog(LevelCog(bot))
