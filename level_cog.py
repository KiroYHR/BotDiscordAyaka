import discord
from discord.ext import commands
import logging
import time
import random
from database import db_manager

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
        
        # Nhận ngẫu nhiên 10 - 20 EXP mỗi phút
        exp_to_add = random.randint(10, 20)
        
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

    @commands.command(name="rank", aliases=["level", "capdo"])
    async def check_rank(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        
        try:
            stats = await db_manager.get_user_stats(str(target.id))
            level = stats["level"]
            exp = stats["exp"]
            
            # Lấy top users để tìm hạng (Rank)
            top_users = await db_manager.get_top_users(limit=1000)
            rank = "?"
            for i, u in enumerate(top_users):
                if u["user_id"] == str(target.id):
                    rank = f"#{i + 1}"
                    break
            
            # Tính toán EXP cần thiết cho cấp tiếp theo (level = exp//100 + 1)
            current_level_base_exp = (level - 1) * 100
            next_level_base_exp = level * 100
            
            exp_in_current_level = exp - current_level_base_exp
            exp_needed = 100 # Cố định 100 exp mỗi cấp
            
            embed = discord.Embed(title=f"🌸 Hồ Sơ Rèn Luyện: {target.display_name}", color=0xFFB6C1)
            
            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)
                
            embed.add_field(name="🏆 Thứ Hạng", value=f"**{rank}**", inline=True)
            embed.add_field(name="🔰 Cấp Độ", value=f"**Lv. {level}**", inline=True)
            embed.add_field(name="✨ Kinh Nghiệm", value=f"**{exp}**", inline=True)
            
            # Thanh tiến trình
            progress_percent = exp_in_current_level / exp_needed
            filled_blocks = int(progress_percent * 10)
            empty_blocks = 10 - filled_blocks
            
            # Sử dụng các ký tự đặc biệt để làm thanh tiến trình đẹp hơn
            progress_bar = "🟦" * filled_blocks + "⬜" * empty_blocks
            
            embed.add_field(name="Tiến Trình Đột Phá", value=f"{progress_bar} {int(progress_percent*100)}%\n(`{exp_in_current_level} / {exp_needed}` để lên cấp tiếp theo)", inline=False)
            
            # Nút Xem Leaderboard trên Web
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Xem Bảng Xếp Hạng Đầy Đủ", url="https://ayaka-bot-0ywq.onrender.com/leaderboard", emoji="🌐"))
            
            await ctx.reply(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Lỗi kiểm tra rank: {e}")
            await ctx.reply("❌ Không thể tra cứu thông tin cấp độ lúc này cậu ạ.")

async def setup(bot):
    await bot.add_cog(LevelCog(bot))
