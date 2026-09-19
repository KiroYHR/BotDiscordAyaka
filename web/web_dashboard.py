import os
import json
import logging
import uuid
from urllib.parse import urlencode
from aiohttp import web
import aiohttp
import discord
from core import config

logger = logging.getLogger("AyakaWeb")

# In-memory session store: {session_id: {"user_id": str, "access_token": str}}
SESSIONS = {}

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
        self.app.router.add_get('/api/leaderboard', self.api_leaderboard)
        
        # OAuth2 Routes
        self.app.router.add_get('/login', self.login)
        self.app.router.add_get('/callback', self.callback)
        self.app.router.add_get('/api/me', self.api_me)
        self.app.router.add_post('/api/daily', self.api_daily)
        
        # Static file routes
        self.app.router.add_get('/', self.serve_index)
        self.app.router.add_get('/leaderboard', self.serve_leaderboard)
        self.app.router.add_get('/style.css', self.serve_css)
        self.app.router.add_get('/app.js', self.serve_js)
        
        # Đường dẫn tuyệt đối để tránh lỗi không tìm thấy file
        assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web/dashboard', 'assets')
        self.app.router.add_static('/assets/', path=assets_path, name='assets')

    async def login(self, request):
        """Chuyển hướng đến Discord OAuth2."""
        if not config.DISCORD_CLIENT_ID:
            return web.Response(text="Thiếu DISCORD_CLIENT_ID", status=500)
            
        params = {
            'client_id': config.DISCORD_CLIENT_ID,
            'redirect_uri': config.DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify'
        }
        url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
        raise web.HTTPFound(url)

    async def callback(self, request):
        """Xử lý Discord callback và tạo session."""
        code = request.query.get('code')
        if not code:
            return web.Response(text="Lỗi: Không tìm thấy authorization code.", status=400)
            
        data = {
            'client_id': config.DISCORD_CLIENT_ID,
            'client_secret': config.DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': config.DISCORD_REDIRECT_URI
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://discord.com/api/oauth2/token', data=data, headers=headers) as resp:
                token_data = await resp.json()
                
                if 'access_token' not in token_data:
                    return web.Response(text=f"Lỗi khi xác thực: {token_data}", status=400)
                    
                access_token = token_data['access_token']
                
                # Fetch user data
                headers = {'Authorization': f'Bearer {access_token}'}
                async with session.get('https://discord.com/api/users/@me', headers=headers) as user_resp:
                    user_data = await user_resp.json()
                    
                    if 'id' not in user_data:
                        return web.Response(text="Không thể lấy thông tin user từ Discord.", status=400)
                        
                    session_id = str(uuid.uuid4())
                    SESSIONS[session_id] = {
                        "user_id": user_data['id'],
                        "discord_data": user_data
                    }
                    
                    response = web.HTTPFound('/')
                    response.set_cookie('session_token', session_id, max_age=86400 * 7) # 7 ngày
                    return response

    async def api_me(self, request):
        """Trả về thông tin user đã đăng nhập kèm DB profile."""
        session_id = request.cookies.get('session_token')
        if not session_id or session_id not in SESSIONS:
            return web.json_response({"authenticated": False})
            
        session_data = SESSIONS[session_id]
        discord_data = session_data["discord_data"]
        user_id = session_data["user_id"]
        
        # Get from DB
        from data.database import db_manager
        db_profile = await db_manager.get_user_profile(user_id)
        
        if not db_profile:
            db_profile = {"exp": 0, "level": 1, "affection": 0, "streak": 0, "selected_character": "airi"}
            
        avatar_hash = discord_data.get('avatar')
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png" if avatar_hash else "https://cdn.discordapp.com/embed/avatars/0.png"
        
        return web.json_response({
            "authenticated": True,
            "id": user_id,
            "username": discord_data.get('username'),
            "global_name": discord_data.get('global_name'),
            "avatar": avatar_url,
            "exp": db_profile.get('exp', 0),
            "level": db_profile.get('level', 1),
            "affection": db_profile.get('affection', 0),
            "streak": db_profile.get('streak', 0),
            "character": db_profile.get('selected_character', 'airi')
        })

    async def api_daily(self, request):
        """Endpoint điểm danh qua web."""
        session_id = request.cookies.get('session_token')
        if not session_id or session_id not in SESSIONS:
            return web.json_response({"success": False, "msg": "Vui lòng đăng nhập trước!"})
            
        user_id = SESSIONS[session_id]["user_id"]
        from data.database import db_manager
        result = await db_manager.claim_daily(user_id)
        return web.json_response(result)

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
            for guild_id, current_data in music_cog.current_song.items():
                guild = self.bot.get_guild(guild_id)
                guild_name = guild.name if guild else "Unknown Server"
                
                # Sửa lỗi [object Object]: Lấy đúng tên bài hát từ dictionary
                title = current_data.get("title", "Unknown Title") if isinstance(current_data, dict) else current_data
                
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
        from data.database import db_manager
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

            from data.database import db_manager
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
                
            from data.database import db_manager
            success = await db_manager.delete_schedule(int(schedule_id))
            return web.json_response({"success": success})
        except Exception as e:
            logger.error(f"Lỗi DELETE /api/schedules: {e}")
            return web.json_response({"success": False, "error": str(e)})

    async def api_leaderboard(self, request):
        """Trả về danh sách top 50 người dùng có EXP cao nhất."""
        from data.database import db_manager
        top_users = await db_manager.get_top_users(limit=50)
        
        result = []
        for i, u in enumerate(top_users):
            user = self.bot.get_user(int(u['user_id']))
            if user:
                result.append({
                    "rank": i + 1,
                    "id": str(user.id),
                    "username": str(user.name),
                    "display_name": user.display_name,
                    "avatar": user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png",
                    "exp": u['exp'],
                    "level": u['level']
                })
        return web.json_response(result)

    # Các hàm phục vụ file tĩnh (Frontend)
    async def serve_index(self, request):
        with open('web/dashboard/index.html', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')
            
    async def serve_leaderboard(self, request):
        raise web.HTTPFound('/')

    async def serve_css(self, request):
        with open('web/dashboard/style.css', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/css')

    async def serve_js(self, request):
        with open('web/dashboard/app.js', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='application/javascript')

async def start_web_server(bot, port=928):
    """Khởi động Web Server chạy ngầm trong bot."""
    web/dashboard = WebDashboard(bot)
    runner = web.AppRunner(web/dashboard.app)
    await runner.setup()
    
    # Chạy trên mọi IP (0.0.0.0) với cổng cấu hình
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🌐 Web Dashboard đang chạy tại: http://localhost:{port}")
