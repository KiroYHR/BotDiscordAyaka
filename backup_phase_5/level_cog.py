import discord
from discord.ext import commands
import logging
from database import db_manager
import math

logger = logging.getLogger("AyakaLevel")

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Lắng nghe tin nhắn để cộng EXP cho người dùng."""
        if message.author.bot:
            return
            
        # Không cộng EXP cho các lệnh bot
        if message.content.startswith("!"):
            return

        # Tính toán lượng EXP dựa trên độ dài tin nhắn (tối đa 5 EXP mỗi tin)
        # Mỗi 10 ký tự = 1 EXP, tối thiểu 1 EXP, tối đa 5 EXP
        exp_to_add = max(1, min(5, len(message.content) // 10))
        
        try:
            result = await db_manager.add_exp(str(message.author.id), exp_to_add)
            if result.get("leveled_up"):
                new_level = result["new_level"]
                # Gửi thông báo chúc mừng lên cấp
                await message.channel.send(f"🎉 Chúc mừng {message.author.mention}! Sự rèn luyện của cậu đã đơm hoa kết trái. Cậu vừa đạt **Cấp độ {new_level}**! 🌸")
        except Exception as e:
            logger.error(f"Lỗi khi cộng EXP: {e}")

    @commands.command(name="rank", aliases=["level", "capdo"])
    async def check_rank(self, ctx, member: discord.Member = None):
        """Kiểm tra cấp độ hiện tại của cậu hoặc người khác."""
        target = member or ctx.author
        
        try:
            stats = await db_manager.get_user_stats(str(target.id))
            level = stats["level"]
            exp = stats["exp"]
            
            # Tính toán EXP cần thiết cho cấp tiếp theo
            # Theo công thức trong database: level = (exp // 100) + 1
            # => EXP cần để đạt level N là (N-1) * 100
            next_level_exp = level * 100
            
            embed = discord.Embed(title=f"🌸 Hồ Sơ Rèn Luyện: {target.display_name}", color=discord.Color.blue())
            
            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)
                
            embed.add_field(name="Cấp Độ Tinh Thông", value=f"**Lv. {level}**", inline=True)
            embed.add_field(name="Kinh Nghiệm", value=f"**{exp} / {next_level_exp} EXP**", inline=True)
            
            # Thanh tiến trình
            progress_percent = (exp % 100) / 100
            filled_blocks = int(progress_percent * 10)
            empty_blocks = 10 - filled_blocks
            progress_bar = "▓" * filled_blocks + "░" * empty_blocks
            
            embed.add_field(name="Tiến Trình Đột Phá", value=f"`{progress_bar}` {int(progress_percent*100)}%", inline=False)
            
            await ctx.reply(embed=embed)
        except Exception as e:
            logger.error(f"Lỗi kiểm tra rank: {e}")
            await ctx.reply("❌ Không thể tra cứu thông tin cấp độ lúc này cậu ạ.")

async def setup(bot):
    await bot.add_cog(LevelCog(bot))
