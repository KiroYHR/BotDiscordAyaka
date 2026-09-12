import discord
from discord.ext import commands
import psutil
import platform

class SysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sysinfo", aliases=["hardware", "status"])
    async def sysinfo(self, ctx):
        """Báo cáo trạng thái phần cứng của máy chủ Host"""
        async with ctx.typing():
            # CPU
            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count(logical=True)
            
            # RAM
            ram = psutil.virtual_memory()
            ram_total = round(ram.total / (1024**3), 2)
            ram_used = round(ram.used / (1024**3), 2)
            ram_percent = ram.percent
            
            # Disk
            # Trên Windows, ổ C: thường là ổ chính. psutil.disk_usage('/') sẽ quét ổ đĩa root.
            disk = psutil.disk_usage('/')
            disk_total = round(disk.total / (1024**3), 2)
            disk_used = round(disk.used / (1024**3), 2)
            disk_percent = disk.percent
            
            # OS
            os_name = platform.system()
            os_release = platform.release()
            
            # Khắc phục lỗi Python nhận diện nhầm Windows 11 thành Windows 10
            if os_name == "Windows" and os_release == "10":
                import sys
                if hasattr(sys, 'getwindowsversion') and sys.getwindowsversion().build >= 22000:
                    os_release = "11"
                    
            os_info = f"{os_name} {os_release}"
            
            # Tạo Embed
            embed = discord.Embed(title="⚙️ Trạng Thái Máy Chủ (System Monitor)", color=discord.Color.blue())
            
            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)
            
            embed.add_field(name="💻 CPU", value=f"Sử dụng: **{cpu_usage}%**\nSố luồng: **{cpu_count} Threads**", inline=True)
            embed.add_field(name="🧠 RAM", value=f"Sử dụng: **{ram_used}GB / {ram_total}GB**\nTỉ lệ: **{ram_percent}%**", inline=True)
            embed.add_field(name="💽 Ổ Cứng", value=f"Sử dụng: **{disk_used}GB / {disk_total}GB**\nTỉ lệ: **{disk_percent}%**", inline=True)
            embed.add_field(name="🖥️ Hệ Điều Hành", value=f"**{os_info}**", inline=False)
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SysCog(bot))
