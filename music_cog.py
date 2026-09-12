import asyncio
import logging
import discord
from discord.ext import commands
import yt_dlp
import aiohttp
import urllib.parse

logger = logging.getLogger("AyakaMusic")

# Cấu hình yt-dlp để lấy định dạng audio tốt nhất (không giới hạn youtube premium)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # Để tránh các vấn đề IPv6
}

# Cấu hình FFmpeg để truyền stream ổn định
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn' # Bỏ qua video, chỉ lấy audio
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queues = {} # {guild_id: [(url, title, requester), ...]}
        self.is_playing = {}  # {guild_id: bool}
        self.current_song = {} # {guild_id: title}
        
    def get_queue(self, guild_id):
        if guild_id not in self.song_queues:
            self.song_queues[guild_id] = []
        return self.song_queues[guild_id]

    async def extract_info(self, url):
        """Lấy thông tin bài hát từ YouTube (bất đồng bộ)"""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        
        if 'entries' in data:
            # Nếu là kết quả tìm kiếm, lấy kết quả đầu tiên
            data = data['entries'][0]
            
        return {
            'url': data['url'],
            'title': data.get('title', 'Unknown Title'),
            'webpage_url': data.get('webpage_url', url)
        }
        
    def play_next(self, ctx):
        """Hàm đệ quy gọi lại khi một bài hát kết thúc để phát bài tiếp theo."""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        if len(queue) > 0:
            self.is_playing[guild_id] = True
            
            # Lấy bài hát tiếp theo
            song = queue.pop(0)
            url = song['url']
            title = song['title']
            self.current_song[guild_id] = title
            
            logger.info(f"Đang phát: {title}")
            
            vc = ctx.voice_client
            if vc and vc.is_connected():
                # Tạo audio source
                source = discord.FFmpegPCMAudio(url, executable="ffmpeg.exe", **FFMPEG_OPTIONS)
                # Khi phát xong tự động gọi lại play_next
                vc.play(source, after=lambda e: self.play_next(ctx))
                
                # Gửi thông báo
                coro = ctx.send(f"🎵 Ayaka bắt đầu gảy khúc hát: **{title}** 🌸")
                asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        else:
            # Hết hàng đợi
            self.is_playing[guild_id] = False
            if guild_id in self.current_song:
                del self.current_song[guild_id]
            logger.info("Đã phát hết danh sách nhạc.")

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str = None):
        """Yêu cầu Ayaka phát nhạc."""
        if not ctx.guild:
            await ctx.reply("Tớ chỉ có thể phát nhạc ở trong Máy Chủ (Server) thôi. Cậu hãy vào Server gọi tớ nhé! 🌸")
            return
            
        if not search:
            await ctx.reply("Cậu muốn tớ phát bài gì nào? Hãy gõ thêm tên bài hát nhé (VD: `!play Nhạc Lofi`) 🌸")
            return

        if not ctx.author.voice:
            await ctx.reply("Cậu phải vào một kênh thoại (Voice Channel) trước thì tớ mới biết phải hát ở đâu chứ! 🌸")
            return
            
        voice_channel = ctx.author.voice.channel
        vc = ctx.voice_client
        
        if vc is None:
            await voice_channel.connect()
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)
            
        async with ctx.typing():
            try:
                # Phân tích URL hoặc tìm kiếm
                song_info = await self.extract_info(search)
                queue = self.get_queue(ctx.guild.id)
                queue.append(song_info)
                
                if not self.is_playing.get(ctx.guild.id, False) and not ctx.voice_client.is_playing():
                    await ctx.reply(f"🌸 Tớ đã chuẩn bị xong: **{song_info['title']}**! Cùng thưởng thức nhé cậu.")
                    self.play_next(ctx)
                else:
                    await ctx.reply(f"✅ Tớ đã ghi nhớ yêu cầu: **{song_info['title']}** vào danh sách chờ rồi nhé!")
            except Exception as e:
                logger.error(f"Lỗi khi tìm bài hát: {e}")
                await ctx.reply("Tớ xin lỗi, có vẻ như bản nhạc này quá khó tìm hoặc đã bị phong ấn ở Inazuma... Cậu thử bài khác nhé! ❄️")

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        """Bỏ qua bài hát hiện tại."""
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.stop() # Hành động stop sẽ kích hoạt trigger `after` và gọi play_next tự động
            await ctx.reply("⏭️ Tớ sẽ chuyển sang khúc ca tiếp theo ngay đây!")
        else:
            await ctx.reply("Hiện tại không có bản nhạc nào đang phát cả cậu ạ.")

    @commands.command(name="stop", aliases=["leave", "disconnect"])
    async def stop(self, ctx):
        """Dừng phát nhạc và rời kênh."""
        vc = ctx.voice_client
        if vc:
            self.get_queue(ctx.guild.id).clear()
            self.is_playing[ctx.guild.id] = False
            await vc.disconnect()
            await ctx.reply("🌸 Tớ xin phép cất lại tiếng đàn. Hy vọng cậu đã có những giây phút thư giãn!")
        else:
            await ctx.reply("Tớ không ở trong kênh thoại nào cả.")

    @commands.command(name="join", aliases=["j"])
    async def join(self, ctx):
        """Yêu cầu Ayaka tham gia kênh thoại."""
        if not ctx.author.voice:
            await ctx.reply("Cậu phải vào một kênh thoại (Voice Channel) trước thì tớ mới biết đường vào chứ! 🌸")
            return
            
        voice_channel = ctx.author.voice.channel
        vc = ctx.voice_client
        
        if vc is None:
            await voice_channel.connect()
            await ctx.reply(f"🌸 Tớ đã có mặt tại kênh **{voice_channel.name}** rồi đây!")
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)
            await ctx.reply(f"🌸 Tớ đã chuyển sang kênh **{voice_channel.name}** theo lời gọi của cậu!")
        else:
            await ctx.reply("Tớ đang ở trong kênh này cùng cậu rồi mà! 🌸")

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Tạm dừng nhạc."""
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await ctx.reply("⏸️ Tớ đã tạm ngừng bản nhạc. Bao giờ muốn nghe tiếp cậu cứ gọi nhé!")

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Tiếp tục phát nhạc."""
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.reply("▶️ Cùng tiếp tục đắm chìm trong giai điệu nào!")

    async def fetch_lyrics(self, track_name: str) -> str:
        """Tìm kiếm lời bài hát qua LRCLIB API."""
        try:
            # Xóa bớt các từ khóa thừa như (Official Music Video), (Lyrics) để tìm chính xác hơn
            clean_track = track_name.lower().split(' (')[0].split(' |')[0].split(' - ')[0]
            track_encoded = urllib.parse.quote(clean_track)
            url = f"https://lrclib.net/api/search?track_name={track_encoded}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'User-Agent': 'AyakaBot/1.0'}) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            return data[0].get('plainLyrics')
        except Exception as e:
            logger.error(f"Lỗi khi tìm lyrics: {e}")
        return None

    @commands.command(name="lyrics", aliases=["loibaihat"])
    async def lyrics(self, ctx):
        """Hiển thị lời bài hát đang phát."""
        guild_id = ctx.guild.id
        if not self.is_playing.get(guild_id, False) or guild_id not in self.current_song:
            await ctx.reply("🎵 Hiện tại Ayaka không phát bài nhạc nào cả cậu ạ.")
            return
            
        current_title = self.current_song[guild_id]
        await ctx.reply(f"🔍 Tớ đang lục tìm lời bài hát **{current_title}** trong Tàng Thư Các... Cậu đợi chút nhé! 🌸")
        
        async with ctx.typing():
            lyrics_text = await self.fetch_lyrics(current_title)
            
            if not lyrics_text:
                await ctx.reply("Tớ xin lỗi... Tớ không thể tìm thấy lời của bài hát này! 😥")
                return
                
            # Cắt ngắn nếu lyrics quá dài (Discord giới hạn 4000 ký tự cho embed)
            if len(lyrics_text) > 3000:
                lyrics_text = lyrics_text[:3000] + "\n\n... (Lời bài hát quá dài, tớ xin phép cắt bớt nha) 🌸"
                
            embed = discord.Embed(title=f"📜 Lời Bài Hát: {current_title}", description=lyrics_text, color=discord.Color.blue())
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
