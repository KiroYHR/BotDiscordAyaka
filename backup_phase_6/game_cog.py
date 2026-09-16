import discord
from discord.ext import commands
import genshin
import os
import logging

logger = logging.getLogger("GameTracker")

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        ltuid = os.getenv("HOYOLAB_LTUID")
        ltoken = os.getenv("HOYOLAB_LTOKEN")
        
        if ltuid and ltoken:
            self.client = genshin.Client({
                "ltuid_v2": ltuid, 
                "ltoken_v2": ltoken,
                "ltuid": ltuid,
                "ltoken": ltoken
            })
            # Thiết lập ngôn ngữ tiếng Việt cho dữ liệu game
            self.client.lang = "vi-vn"
        else:
            self.client = None
            logger.warning("Chưa thiết lập HOYOLAB_LTUID và HOYOLAB_LTOKEN trong .env!")

    @commands.command(name="gs", aliases=["genshin"])
    async def profile_genshin(self, ctx, uid: int = None):
        """Tra cứu thẻ thông tin Genshin Impact bằng UID"""
        if not self.client:
            await ctx.reply("❌ Cậu cần thiết lập `HOYOLAB_LTUID` và `HOYOLAB_LTOKEN` trong file `.env` trước nhé!")
            return
        if not uid:
            await ctx.reply("🌸 Cậu quên nhập UID rồi! Ví dụ: `!gs 808480599`")
            return
            
        async with ctx.typing():
            try:
                user = await self.client.get_genshin_user(uid)
                
                embed = discord.Embed(
                    title=f"🎐 Thẻ Khách Bộ Hành: **{user.info.nickname}**", 
                    description=f"✦ **UID:** `{uid}`  |  ✦ **Máy chủ:** `{user.info.server}`\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0x48C9B0
                )
                
                if user.characters:
                    embed.set_thumbnail(url=user.characters[0].icon)
                
                embed.add_field(name="🌟 Tiến Độ Chung", 
                                value=f"• Cấp Mạo Hiểm: **AR {user.info.level}**\n"
                                      f"• Thành Tựu: **{user.stats.achievements}** 🏆\n"
                                      f"• Nhân vật đã có: **{user.stats.characters}** 👤", 
                                inline=True)
                                
                embed.add_field(name="🗺️ Thâm Cảnh La Hoàn", 
                                value=f"• Tầng cao nhất: **{user.stats.spiral_abyss}** 👑\n"
                                      f"• Rương đã mở: **{user.stats.luxurious_chests + user.stats.precious_chests + user.stats.exquisite_chests + user.stats.common_chests}** 🎁", 
                                inline=True)
                
                # Top 4 nhân vật nổi bật
                if user.characters:
                    top_chars = "\n".join([f"✨ **{c.name}** - Lv.{c.level} (❤ {c.friendship})" for c in user.characters[:4]])
                    embed.add_field(name="💫 Đội Hình Nổi Bật", value=top_chars, inline=False)
                
                # Khu vực thám hiểm 100%
                maxed_areas = [exp.name for exp in user.explorations if exp.explored == 1000]
                if maxed_areas:
                    # Lấy tối đa 5 khu vực để tránh quá dài
                    areas_str = ", ".join(maxed_areas[:5]) + ("..." if len(maxed_areas) > 5 else "")
                    embed.add_field(name="🧭 Khu Vực Đã Khám Phá 100%", value=f"*{areas_str}*", inline=False)
                
                # Ảnh trang trí (Banner Genshin Impact cực đẹp)
                embed.set_image(url="https://i.pinimg.com/originals/c6/3e/21/c63e21a28a1ba5f22ca88d07019a16f2.gif")
                embed.set_footer(text="Hệ thống dữ liệu Cây Thế Giới (Irminsul)", icon_url="https://cdn.discordapp.com/emojis/1040523450978242590.webp")
                
                await ctx.send(embed=embed)
            except Exception as e:
                logger.error(f"Lỗi lấy dữ liệu Genshin UID {uid}: {e}")
                await ctx.reply("❌ Không tìm thấy thông tin! (Hoặc tài khoản này đang ẩn lịch sử công khai trên HoyoLab)")

    @commands.command(name="hsr", aliases=["starrail"])
    async def profile_hsr(self, ctx, uid: int = None):
        """Tra cứu thẻ thông tin Honkai: Star Rail bằng UID"""
        if not self.client:
            await ctx.reply("❌ Cậu cần thiết lập `HOYOLAB_LTUID` và `HOYOLAB_LTOKEN` trong file `.env` trước nhé!")
            return
        if not uid:
            await ctx.reply("🌸 Cậu quên nhập UID rồi! Ví dụ: `!hsr 800000000`")
            return
            
        async with ctx.typing():
            try:
                user = await self.client.get_starrail_user(uid)
                
                embed = discord.Embed(
                    title=f"🚂 Khách Vô Danh: **{user.info.nickname}**", 
                    description=f"✦ **UID:** `{uid}`  |  ✦ **Máy chủ:** `{user.info.server}`\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0x9B59B6
                )
                
                if user.characters:
                    embed.set_thumbnail(url=user.characters[0].icon)
                
                embed.add_field(name="🌟 Hành Trình Tàu Astral", 
                                value=f"• Cấp Khai Phá: **{user.info.level}**\n"
                                      f"• Thành Tựu: **{user.stats.achievements}** 🏆\n"
                                      f"• Nhân vật đồng hành: **{user.stats.characters}** 👤", 
                                inline=True)
                                
                embed.add_field(name="🌌 Vũ Trụ Mô Phỏng", 
                                value=f"• Sảnh Đường: **Sẵn sàng**\n"
                                      f"• Ký ức rực rỡ: Đang ghi chép", 
                                inline=True)
                
                # Top 4 nhân vật nổi bật
                if user.characters:
                    top_chars = "\n".join([f"✨ **{c.name}** - Lv.{c.level}" for c in user.characters[:4]])
                    embed.add_field(name="💫 Đội Hình Tiên Phong", value=top_chars, inline=False)
                
                embed.set_image(url="https://i.pinimg.com/originals/30/23/79/302379edbd6b9e3a6a12b9188d3e2305.gif")
                embed.set_footer(text="Dữ liệu truyền tải từ Tàu Astral", icon_url="https://cdn.discordapp.com/emojis/1101858564756242462.webp")
                
                await ctx.send(embed=embed)
            except Exception as e:
                logger.error(f"Lỗi lấy dữ liệu HSR UID {uid}: {e}")
                await ctx.reply("❌ Không tìm thấy thông tin HSR! (Hoặc tài khoản này đang ẩn lịch sử trên HoyoLab)")

    @commands.command(name="zzz", aliases=["zenless"])
    async def profile_zzz(self, ctx, uid: int = None):
        """Tra cứu thẻ thông tin Zenless Zone Zero bằng UID"""
        if not self.client:
            await ctx.reply("❌ Cậu cần thiết lập `HOYOLAB_LTUID` và `HOYOLAB_LTOKEN` trong file `.env` trước nhé!")
            return
        if not uid:
            await ctx.reply("🌸 Cậu quên nhập UID rồi! Ví dụ: `!zzz 130000000`")
            return
            
        async with ctx.typing():
            try:
                user = await self.client.get_zzz_user(uid)
                
                embed = discord.Embed(
                    title=f"📼 Người Kết Nối: **{user.info.nickname}**", 
                    description=f"✦ **UID:** `{uid}`  |  ✦ **Máy chủ:** `{user.info.server}`\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0xE67E22
                )
                
                embed.add_field(name="🌟 Hồ Sơ Pha Lê", 
                                value=f"• Cấp Mạng Node: **{user.info.level}**\n"
                                      f"• Người Đại Diện: **{user.stats.characters}** 👤", 
                                inline=True)
                
                # Top nhân vật
                if hasattr(user, 'characters') and user.characters:
                    top_chars = "\n".join([f"✨ **{c.name}** - Lv.{c.level}" for c in user.characters[:4]])
                    embed.add_field(name="💫 Biệt Đội Đánh Thuê", value=top_chars, inline=False)
                
                embed.set_image(url="https://i.pinimg.com/originals/74/6b/c8/746bc8a59530467edbbbb829f041ffce.gif")
                embed.set_footer(text="Dữ liệu nội bộ từ Pha Lê - New Eridu", icon_url="https://cdn.discordapp.com/emojis/1258622146951909386.webp")
                
                await ctx.send(embed=embed)
            except Exception as e:
                logger.error(f"Lỗi lấy dữ liệu ZZZ UID {uid}: {e}")
                await ctx.reply("❌ Không tìm thấy thông tin ZZZ! (Hoặc tài khoản này đang ẩn lịch sử trên HoyoLab)")

async def setup(bot):
    await bot.add_cog(GameCog(bot))
