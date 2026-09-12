import discord
from discord.ext import commands, tasks
import psutil
import platform
import datetime
import logging
import asyncio

logger = logging.getLogger("SysCog")

class SysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_greeting.start()
        
    def cog_unload(self):
        self.daily_greeting.cancel()

    @tasks.loop(time=[
        datetime.time(hour=6, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=7))),
        datetime.time(hour=22, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=7)))
    ])
    async def daily_greeting(self):
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        is_morning = now.hour == 6
        
        # 1. Sinh nội dung bằng AI
        from ai_brain import client
        import config
        if not client:
            logger.error("Gemini client chưa được khởi tạo. Bỏ qua daily_greeting.")
            return
            
        try:
            if is_morning:
                prompt = "Bây giờ là 6 giờ sáng. Dưới góc độ nhân vật Kamisato Ayaka (Genshin Impact), hãy viết một lời chào buổi sáng ngắn gọn (khoảng 2-3 câu), thật dễ thương, lịch sự đến các 'Nhà Lữ Hành' trong hiệp hội Yashiro. Nhớ nhắc họ chú ý thời tiết hoặc giữ gìn sức khỏe cho ngày mới nhé!"
            else:
                prompt = "Bây giờ là 10 giờ tối. Dưới góc độ nhân vật Kamisato Ayaka (Genshin Impact), hãy viết một lời chúc ngủ ngon ngắn gọn (khoảng 2-3 câu), thật dễ thương và ân cần đến các 'Nhà Lữ Hành' trong hiệp hội Yashiro. Nhắc họ đi ngủ sớm để giữ sức khỏe."
                
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(model=config.GEMINI_MODEL_NAME, contents=prompt)
            )
            message_text = response.text
        except Exception as e:
            logger.error(f"Lỗi khi tạo tin nhắn báo thức: {e}")
            message_text = "🌸 Chào buổi sáng mọi người! Chúc mọi người một ngày an lành." if is_morning else "❄️ Đã muộn rồi, mọi người nhớ nghỉ ngơi sớm nhé!"

        # 2. Tìm kênh và gửi
        for guild in self.bot.guilds:
            target_channel = discord.utils.get(guild.text_channels, name="bản-tin-hiệp-hội-yashiro")
            if target_channel:
                try:
                    await target_channel.send(message_text)
                except Exception as e:
                    logger.error(f"Không thể gửi tin nhắn cho server {guild.name}: {e}")

    @daily_greeting.before_loop
    async def before_daily_greeting(self):
        await self.bot.wait_until_ready()

    @commands.command(name="testgreeting")
    @commands.has_permissions(administrator=True)
    async def testgreeting(self, ctx):
        """Lệnh ẩn để test thử tính năng báo thức"""
        await ctx.send("Đang kích hoạt chạy thử kịch bản báo thức/chúc ngủ ngon...")
        await self.daily_greeting()
        await ctx.send("Đã chạy xong hàm daily_greeting.")

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
