import os
import json
import logging
from aiohttp import web
import discord

logger = logging.getLogger("AyakaWeb")

class WebDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        # API Routes
        self.app.router.add_get('/api/status', self.api_status)
        self.app.router.add_get('/api/music', self.api_music)
        self.app.router.add_get('/api/channels', self.api_channels)
        self.app.router.add_get('/api/schedules', self.api_get_schedules)
        self.app.router.add_post('/api/schedules', self.api_post_schedules)
        self.app.router.add_delete('/api/schedules', self.api_delete_schedules)
        
        # Static file routes
        self.app.router.add_get('/', self.serve_index)
        self.app.router.add_get('/style.css', self.serve_css)
        self.app.router.add_get('/app.js', self.serve_js)
        
        # Đường dẫn tuyệt đối để tránh lỗi không tìm thấy file
        assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard', 'assets')
        self.app.router.add_static('/assets/', path=assets_path, name='assets')

    async def api_status(self, request):
        """Trả về thông số trạng thái của bot."""
        latency = round(self.bot.latency * 1000) if self.bot.latency else 0
        guild_count = len(self.bot.guilds)
        
        # Đếm tổng số user trong tất cả server
        user_count = sum([guild.member_count for guild in self.bot.guilds if guild.member_count])
        
        return web.json_response({
            "status": "online",
            "bot_name": str(self.bot.user),
            "latency": latency,
            "guilds": guild_count,
            "users": user_count
        })

    async def api_music(self, request):
        """Trả về bài hát đang phát (nếu có)."""
        music_cog = self.bot.get_cog("MusicCog")
        playing_tracks = []
        
        if music_cog:
            for guild_id, title in music_cog.current_song.items():
                guild = self.bot.get_guild(guild_id)
                guild_name = guild.name if guild else "Unknown Server"
                playing_tracks.append({
                    "server": guild_name,
                    "title": title
                })
                
        return web.json_response({
            "playing": len(playing_tracks) > 0,
            "tracks": playing_tracks
        })

    async def api_channels(self, request):
        """Trả về danh sách các kênh văn bản bot có thể truy cập."""
        channels = []
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                # Bỏ qua kênh không có quyền gửi tin
                permissions = channel.permissions_for(guild.me)
                if permissions.send_messages:
                    channels.append({
                        "id": str(channel.id),
                        "name": f"#{channel.name} ({guild.name})",
                        "guild_id": str(guild.id)
                    })
        return web.json_response(channels)

    async def api_get_schedules(self, request):
        """Lấy danh sách báo thức."""
        from database import db_manager
        schedules = await db_manager.get_schedules()
        return web.json_response(schedules)

    async def api_post_schedules(self, request):
        """Thêm lịch báo thức mới."""
        try:
            data = await request.json()
            guild_id = data.get("guild_id")
            channel_id = data.get("channel_id")
            time_str = data.get("time_str")
            prompt = data.get("prompt")
            weather_location = data.get("weather_location", "")

            if not all([guild_id, channel_id, time_str, prompt]):
                return web.json_response({"success": False, "error": "Thiếu dữ liệu"})

            from database import db_manager
            success, err_msg = await db_manager.add_schedule(guild_id, channel_id, time_str, prompt, weather_location)
            if success:
                return web.json_response({"success": True})
            else:
                return web.json_response({"success": False, "error": err_msg})
        except Exception as e:
            logger.error(f"Lỗi POST /api/schedules: {e}")
            return web.json_response({"success": False, "error": str(e)})

    async def api_delete_schedules(self, request):
        """Xóa lịch báo thức."""
        try:
            schedule_id = request.query.get("id")
            if not schedule_id:
                return web.json_response({"success": False, "error": "Thiếu ID"})
                
            from database import db_manager
            success = await db_manager.delete_schedule(int(schedule_id))
            return web.json_response({"success": success})
        except Exception as e:
            logger.error(f"Lỗi DELETE /api/schedules: {e}")
            return web.json_response({"success": False, "error": str(e)})

    # Các hàm phục vụ file tĩnh (Frontend)
    async def serve_index(self, request):
        with open('dashboard/index.html', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')

    async def serve_css(self, request):
        with open('dashboard/style.css', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/css')

    async def serve_js(self, request):
        with open('dashboard/app.js', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='application/javascript')

async def start_web_server(bot, port=928):
    """Khởi động Web Server chạy ngầm trong bot."""
    dashboard = WebDashboard(bot)
    runner = web.AppRunner(dashboard.app)
    await runner.setup()
    
    # Chạy trên mọi IP (0.0.0.0) với cổng cấu hình
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 Web Dashboard đang chạy tại: http://localhost:{port}")
