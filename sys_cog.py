import discord
from discord.ext import commands, tasks
import psutil
import platform
import datetime
import logging
import asyncio
import aiohttp
import config
from database import db_manager

logger = logging.getLogger("SysCog")

class SysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_greeting.start()
        
    def cog_unload(self):
        self.daily_greeting.cancel()

    @tasks.loop(minutes=1)
    async def daily_greeting(self):
        try:
            # Lấy giờ hiện tại (Việt Nam UTC+7)
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
            current_time_str = now.strftime("%H:%M")
            current_date_str = now.strftime("%d/%m/%Y")
            
            # Lấy tất cả lịch trình
            schedules = await db_manager.get_schedules()
            
            for schedule in schedules:
                if schedule['time_str'] == current_time_str:
                    # Kích hoạt chạy nhắc nhở tùy chỉnh
                    asyncio.create_task(self._process_single_schedule(schedule))
                    
            # --- Báo thức Cố định 6h sáng (Ngày tháng & Thời tiết mặc định) ---
            if current_time_str == "06:00":
                asyncio.create_task(self._run_6am_greeting(current_date_str))
        except Exception as e:
            logger.error(f"Lỗi trong vòng lặp daily_greeting: {e}")
                
    async def _run_6am_greeting(self, date_str: str):
        from ai_brain import client
        if not client: return
        
        # Lấy thời tiết TP.HCM và các khu vực lân cận
        hcm_weather = await self.fetch_weather("Ho Chi Minh City,VN")
        q1_weather = await self.fetch_weather("District 1, Ho Chi Minh City, VN")
        thu_duc_weather = await self.fetch_weather("Thu Duc, Ho Chi Minh City, VN")
        q7_weather = await self.fetch_weather("District 7, Ho Chi Minh City, VN")
        
        weather_info = f"TP.HCM chung: {hcm_weather}\nQuận 1: {q1_weather}\nThủ Đức: {thu_duc_weather}\nQuận 7: {q7_weather}"
        
        full_prompt = (
            f"Hôm nay là ngày {date_str}, bây giờ là 06:00 sáng.\n"
            f"Dưới góc độ nhân vật Kamisato Ayaka (Genshin Impact), hãy viết một lời chào buổi sáng thật dễ thương, "
            f"kèm theo thông tin ngày tháng hiện tại để gửi đến các 'Nhà Lữ Hành' trong hiệp hội Yashiro.\n"
            f"Thông tin thời tiết tại khu vực TP.HCM hôm nay:\n{weather_info}\n"
            f"(Hãy khéo léo lồng ghép dự báo thời tiết của TP.HCM và một vài quận tiêu biểu vào lời chào. Giữ tin nhắn ngắn gọn tầm 4-5 câu)."
        )
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(model=config.GEMINI_MODEL_NAME, contents=full_prompt)
            )
            message_text = response.text
        except Exception as e:
            logger.error(f"Lỗi AI 6am greeting: {e}")
            message_text = f"🌸 Chào buổi sáng mọi người! Hôm nay là ngày {date_str}, chúc các Nhà Lữ Hành một ngày mới an lành và tràn đầy năng lượng nhé!\n\n**Dự báo thời tiết nhanh:**\n{weather_info}"
            
        # Tìm kênh bản-tin-hiệp-hội-yashiro ở tất cả các server
        for guild in self.bot.guilds:
            target_channel = discord.utils.get(guild.text_channels, name="bản-tin-hiệp-hội-yashiro")
            if target_channel:
                try:
                    await target_channel.send(message_text)
                except:
                    pass

    async def fetch_weather(self, location: str) -> str:
        if not location or not config.WEATHER_API_KEY:
            return ""
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={config.WEATHER_API_KEY}&units=metric&lang=vi"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        desc = data['weather'][0]['description']
                        temp = data['main']['temp']
                        humidity = data['main']['humidity']
                        city = data['name']
                        return f"(Thời tiết thực tế tại {city}: {desc}, Nhiệt độ {temp}°C, Độ ẩm {humidity}%)"
            return ""
        except Exception as e:
            logger.error(f"Lỗi fetch weather: {e}")
            return ""

    async def _process_single_schedule(self, schedule: dict):
        from ai_brain import client
        if not client:
            return
            
        guild_id = schedule['guild_id']
        channel_id = schedule['channel_id']
        user_prompt = schedule['prompt']
        location = schedule.get('weather_location', '')
        time_str = schedule['time_str']
        
        guild = self.bot.get_guild(int(guild_id))
        if not guild: return
        channel = guild.get_channel(int(channel_id))
        if not channel: return
        
        weather_info = await self.fetch_weather(location) if location else ""
        
        # Xây dựng prompt dành riêng cho nhắc nhở
        full_prompt = (
            f"Dưới góc độ nhân vật Kamisato Ayaka (Genshin Impact), hãy nhắc nhở Nhà Lữ Hành một cách dễ thương và tự nhiên nhất về việc sau:\n"
            f"Lời nhắc: {user_prompt}\n"
            f"{weather_info}\n"
            f"(Nếu có thông tin thời tiết, hãy khéo léo lồng ghép vào. Giữ tin nhắn nhắc nhở ngắn gọn tầm 3-4 câu)."
        )
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(model=config.GEMINI_MODEL_NAME, contents=full_prompt)
            )
            message_text = response.text
            await channel.send(message_text)
        except Exception as e:
            logger.error(f"Lỗi AI schedule: {e}")
            fallback_msg = f"⏰ **Ayaka xin thông báo:** Đã đến giờ hẹn `{time_str}` của cậu rồi nhé!\n*(Lời nhắc: {user_prompt})*\n\n*(Xin lỗi cậu, kết nối tâm thức với máy chủ AI đang bị gián đoạn nên tớ chỉ có thể nhắc nhở đơn giản thế này thôi 🌸)*"
            try:
                await channel.send(fallback_msg)
            except Exception as inner_e:
                logger.error(f"Lỗi gửi tin nhắn fallback: {inner_e}")

    @daily_greeting.before_loop
    async def before_daily_greeting(self):
        await self.bot.wait_until_ready()

    @commands.command(name="testgreeting")
    async def testgreeting(self, ctx):
        """Lệnh ẩn để test thử tính năng báo thức"""
        await ctx.send("⏳ Tính năng test thủ công đã được vô hiệu hóa. Báo thức giờ chạy bằng hệ thống Lập lịch qua Web Dashboard!")

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
class HelpSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Trợ Giúp Cơ Bản", description="Cách giao tiếp với Ayaka", emoji="🌸", value="basic"),
            discord.SelectOption(label="Âm Nhạc", description="Lệnh liên quan đến trình phát nhạc", emoji="🎵", value="music"),
            discord.SelectOption(label="Cấp Độ & Bảng Xếp Hạng", description="Tính năng kinh nghiệm (EXP)", emoji="🏆", value="level"),
            discord.SelectOption(label="Hệ Thống", description="Các lệnh về máy chủ và bot", emoji="⚙️", value="sys")
        ]
        super().__init__(placeholder="Chọn danh mục cần hướng dẫn...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(color=0xFFB6C1)
        
        if self.values[0] == "basic":
            embed.title = "🌸 Trợ Giúp Cơ Bản"
            embed.description = (
                "• **Trò chuyện:** Gõ `@Kamisato Ayaka <nội dung>` hoặc *Reply* tin nhắn của tớ.\n"
                "• **Tin nhắn riêng (DM):** Nhắn trực tiếp, tớ sẽ trả lời mọi lúc.\n"
                "• `!reset` hoặc `!clear`: Xóa trí nhớ cuộc hội thoại hiện tại.\n"
            )
        elif self.values[0] == "music":
            embed.title = "🎵 Trợ Giúp Âm Nhạc"
            embed.description = (
                "• `!play <tên bài>` hoặc `!p`: Tìm và phát nhạc.\n"
                "• `!skip` hoặc `!s`: Bỏ qua bài hiện tại.\n"
                "• `!stop` hoặc `!leave`: Dừng phát và rời kênh thoại.\n"
                "• `!lyrics` hoặc `!loibaihat`: Tìm lời bài hát đang phát.\n"
                "*(Cậu cũng có thể dùng trực tiếp các nút bấm trên giao diện Trình Phát Nhạc nhé!)*"
            )
        elif self.values[0] == "level":
            embed.title = "🏆 Hệ Thống Cấp Độ"
            embed.description = (
                "• Tương tác (nhắn tin) trong server sẽ giúp cậu nhận được EXP.\n"
                "• `!rank`, `!level` hoặc `!capdo`: Xem Thẻ Cấp Độ của cậu hoặc người khác.\n"
                "• **Bảng Xếp Hạng:** Xem danh sách Top server tại [ayaka-bot-0ywq.onrender.com/#leaderboard](https://ayaka-bot-0ywq.onrender.com/#leaderboard)"
            )
        elif self.values[0] == "sys":
            embed.title = "⚙️ Lệnh Hệ Thống"
            embed.description = (
                "• `!ping`: Xem độ trễ kết nối.\n"
                "• `!sysinfo`, `!hardware`: Trạng thái máy chủ Host.\n"
            )
            
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.add_item(HelpSelect(bot))

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["trogiup", "h"])
    async def help_command(self, ctx: commands.Context):
        """Bảng hướng dẫn tương tác toàn diện."""
        embed = discord.Embed(
            title="🌸 Sách Hướng Dẫn Hiệp Hội Yashiro",
            description="Xin chào, tớ là Kamisato Ayaka! Cậu cần tớ hướng dẫn về tính năng nào? Hãy chọn trong menu bên dưới nhé. 🍵",
            color=0xFFB6C1
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        await ctx.reply(embed=embed, view=HelpView(self.bot))

async def setup(bot):
    await bot.add_cog(SysCog(bot))
    await bot.add_cog(HelpCog(bot))
