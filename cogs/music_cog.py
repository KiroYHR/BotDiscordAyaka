import asyncio
import logging
import discord
from discord.ext import commands
import yt_dlp
import aiohttp
import urllib.parse
import random
import re

logger = logging.getLogger("AyakaMusic")

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
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

def format_duration(seconds):
    if not seconds: return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

class MusicPlayerView(discord.ui.View):
    def __init__(self, cog, guild_id, suggestions=None):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        
        # Thêm Menu thả xuống Gợi ý (Row 2)
        if suggestions and len(suggestions) > 0:
            options = []
            for i, s in enumerate(suggestions[:5]):
                desc = s.get('channel', 'YouTube')
                if not desc: desc = "YouTube"
                options.append(discord.SelectOption(
                    label=s['title'][:90], # Discord giới hạn 100 ký tự
                    value=s['url'],
                    description=desc[:90],
                    emoji="🎵"
                ))
            
            if options:
                select = discord.ui.Select(
                    placeholder="🎶 Chọn bài hát gợi ý tương tự...", 
                    options=options, 
                    row=2
                )
                select.callback = self.select_callback
                self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        # Khi người dùng chọn 1 bài từ danh sách gợi ý
        url = interaction.data['values'][0]
        await interaction.response.send_message(f"🔍 Ayaka đang chuẩn bị bài hát gợi ý...", ephemeral=True)
        
        try:
            song_info = await self.cog.extract_info(url, interaction.user.mention)
            queue = self.cog.get_queue(self.guild_id)
            queue.append(song_info)
            
            vc = interaction.guild.voice_client
            if not self.cog.is_playing.get(self.guild_id, False) and (not vc or not vc.is_playing()):
                self.cog.bot.loop.create_task(self.cog._async_play_next(self.guild_id))
            else:
                await self.cog.update_player_message(self.guild_id)
                
            await interaction.edit_original_response(content=f"✅ Đã thêm **{song_info['title']}** vào hàng đợi!")
        except Exception as e:
            logger.error(f"Lỗi gợi ý: {e}")
            await interaction.edit_original_response(content="❌ Có lỗi xảy ra khi tải bài hát này.")

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if vc:
            if vc.is_playing():
                vc.pause()
            elif vc.is_paused():
                vc.resume()
        await self.cog.update_player_message(self.guild_id)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
        else:
            await self.cog.update_player_message(self.guild_id)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if vc:
            self.cog.get_queue(self.guild_id).clear()
            self.cog.is_playing[self.guild_id] = False
            self.cog.current_song.pop(self.guild_id, None)
            await vc.disconnect()
        await self.cog.update_player_message(self.guild_id)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=0)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        queue = self.cog.get_queue(self.guild_id)
        if len(queue) > 1:
            random.shuffle(queue)
        await self.cog.update_player_message(self.guild_id)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=0)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        current_loop = self.cog.loop_mode.get(self.guild_id, 0)
        self.cog.loop_mode[self.guild_id] = (current_loop + 1) % 3
        # 0: Off, 1: Track, 2: Queue
        await self.cog.update_player_message(self.guild_id)

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, row=1)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if vc and vc.source and isinstance(vc.source, discord.PCMVolumeTransformer):
            # Giảm 20% âm lượng mỗi lần bấm cho rõ rệt
            vc.source.volume = max(0.1, round(vc.source.volume - 0.2, 1))
            self.cog.volumes[self.guild_id] = vc.source.volume
        await self.cog.update_player_message(self.guild_id)

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=1)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if vc and vc.source and isinstance(vc.source, discord.PCMVolumeTransformer):
            # Tăng 20% âm lượng mỗi lần bấm
            vc.source.volume = min(2.0, round(vc.source.volume + 0.2, 1))
            self.cog.volumes[self.guild_id] = vc.source.volume
        await self.cog.update_player_message(self.guild_id)
        
    @discord.ui.button(emoji="📜", label="Lyrics", style=discord.ButtonStyle.success, row=1)
    async def lyrics(self, interaction: discord.Interaction, button: discord.ui.Button):
        current = self.cog.current_song.get(self.guild_id)
        if not current:
            await interaction.response.send_message("Không có bài hát nào đang phát.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        lyrics_text = await self.cog.fetch_lyrics(current['title'])
        if not lyrics_text:
            await interaction.followup.send("Tớ không tìm thấy lời bài hát chuẩn cho bản remix/cover này! 😥", ephemeral=True)
            return
        
        if len(lyrics_text) > 3000:
            lyrics_text = lyrics_text[:3000] + "..."
            
        embed = discord.Embed(title=f"📜 {current['title']}", description=lyrics_text, color=discord.Color.blue())
        await interaction.followup.send(embed=embed, ephemeral=True)


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queues = {} 
        self.is_playing = {}  
        self.current_song = {} 
        self.loop_mode = {} 
        self.volumes = {} 
        self.player_messages = {} 
        self.current_suggestions = {} # Cache gợi ý cho từng guild
        self.last_text_channel = {}
        
    def get_queue(self, guild_id):
        if guild_id not in self.song_queues:
            self.song_queues[guild_id] = []
        return self.song_queues[guild_id]

    async def extract_info(self, url, requester):
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        except Exception as e:
            logger.warning(f"Lỗi YouTube: {e}. Thử SoundCloud...")
            fallback_opts = dict(YTDL_OPTIONS)
            fallback_opts['default_search'] = 'scsearch'
            fallback_ytdl = yt_dlp.YoutubeDL(fallback_opts)
            data = await loop.run_in_executor(None, lambda: fallback_ytdl.extract_info(url, download=False))
            
        if 'entries' in data:
            data = data['entries'][0]
            
        return {
            'url': data['url'],
            'title': data.get('title', 'Unknown Title'),
            'webpage_url': data.get('webpage_url', url),
            'duration': data.get('duration', 0),
            'thumbnail': data.get('thumbnail', ''),
            'requester': requester
        }

    async def get_suggestions(self, title):
        """Lấy danh sách bài hát gợi ý từ SoundCloud để tránh Rate Limit"""
        loop = asyncio.get_event_loop()
        search_opts = {'quiet': True, 'extract_flat': True}
        search_ytdl = yt_dlp.YoutubeDL(search_opts)
        try:
            clean_track = re.sub(r'\(.*?\) | \[.*?\]', '', title).strip()
            clean_track = clean_track.replace("Official", "").replace("MV", "").strip()
            
            query = f"scsearch5:{clean_track}"
            data = await loop.run_in_executor(None, lambda: search_ytdl.extract_info(query, download=False))
            
            suggestions = []
            if 'entries' in data:
                for e in data['entries']:
                    if e.get('title') and e.get('url') and e.get('title') != title:
                        suggestions.append({
                            'title': e['title'],
                            'url': e['url'],
                            'channel': e.get('uploader', 'SoundCloud')
                        })
            return suggestions
        except Exception as e:
            logger.error(f"Lỗi get suggestions: {e}")
            return []
        
    async def update_player_message(self, guild_id):
        channel = self.last_text_channel.get(guild_id)
        if not channel: return
        
        current = self.current_song.get(guild_id)
        queue = self.get_queue(guild_id)
        
        if not current and not queue:
            # Ngừng phát
            embed = discord.Embed(title="⏹️ Trình phát nhạc đã dừng", color=discord.Color.dark_grey())
            if guild_id in self.player_messages:
                try:
                    await self.player_messages[guild_id].edit(embed=embed, view=None)
                except:
                    pass
                del self.player_messages[guild_id]
            return

        loop_icons = ["", "🔂 (Bật: 1 Bài)", "🔁 (Bật: Hàng Đợi)"]
        loop_status = loop_icons[self.loop_mode.get(guild_id, 0)]
        vol = int(self.volumes.get(guild_id, 1.0) * 100)
        
        embed = discord.Embed(color=0x99ccff)
        suggestions = []
        
        if current:
            dur = format_duration(current["duration"])
            embed.set_author(name="Đang phát hiện tại", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            embed.title = current["title"]
            embed.url = current.get("webpage_url", "")
            
            desc = f"**Người gọi:** {current['requester']}\n"
            desc += f"**Thời lượng:** `{dur}` | **Âm lượng:** {vol}%\n"
            if loop_status:
                desc += f"**Lặp lại:** {loop_status}\n"
            embed.description = desc
            
            if current["thumbnail"]:
                embed.set_thumbnail(url=current["thumbnail"])
                
            # Lấy bài hát gợi ý từ cache thay vì block luồng
            suggestions = self.current_suggestions.get(guild_id, [])
        else:
            embed.title = "Đang tải nhạc..."

        # Danh sách chờ (Up Next)
        if queue:
            queue_str = ""
            for i, q in enumerate(queue[:10]):
                dur = format_duration(q['duration'])
                queue_str += f"**{i+1}.** {q['title']} `[{dur}]` - {q['requester']}\n"
            
            if len(queue) > 10:
                queue_str += f"\n*+ {len(queue) - 10} bài hát nữa trong hàng đợi...*"
                
            embed.add_field(name="Up Next:", value=queue_str, inline=False)
        else:
            embed.add_field(name="Up Next:", value="*Trống*", inline=False)

        view = MusicPlayerView(self, guild_id, suggestions=suggestions)
        
        # Cập nhật hoặc gửi tin nhắn mới
        old_msg = self.player_messages.get(guild_id)
        if old_msg:
            try:
                await old_msg.edit(embed=embed, view=view)
                return
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Lỗi edit player: {e}")
                
        # Nếu chưa có hoặc bị xóa, gửi mới
        new_msg = await channel.send(embed=embed, view=view)
        self.player_messages[guild_id] = new_msg

    def play_next(self, guild_id):
        self.bot.loop.create_task(self._async_play_next(guild_id))
        
    async def _async_play_next(self, guild_id):
        queue = self.get_queue(guild_id)
        current = self.current_song.get(guild_id)
        lmode = self.loop_mode.get(guild_id, 0)
        
        if current:
            if lmode == 1:
                queue.insert(0, current)
            elif lmode == 2:
                queue.append(current)
                
        guild = self.bot.get_guild(guild_id)
        if not guild or not guild.voice_client: return
        vc = guild.voice_client

        if len(queue) > 0:
            self.is_playing[guild_id] = True
            song = queue.pop(0)
            self.current_song[guild_id] = song
            
            try:
                source = discord.FFmpegPCMAudio(song['url'], executable="ffmpeg", **FFMPEG_OPTIONS)
                # Bọc Transformer với volume hiện tại
                source = discord.PCMVolumeTransformer(source, volume=self.volumes.get(guild_id, 1.0))
                vc.play(source, after=lambda e: self.play_next(guild_id))
            except Exception as e:
                logger.error(f"Lỗi phát nhạc: {e}")
                self.play_next(guild_id)
                return
                
            await self.update_player_message(guild_id)
            # Fetch gợi ý trong background sau khi cập nhật Player để tránh delay
            self.bot.loop.create_task(self._fetch_and_update_suggestions(guild_id, song['title']))
        else:
            self.is_playing[guild_id] = False
            self.current_song.pop(guild_id, None)
            self.current_suggestions.pop(guild_id, None)
            await self.update_player_message(guild_id)
            await asyncio.sleep(60)
            if not self.is_playing.get(guild_id) and guild.voice_client:
                await guild.voice_client.disconnect()

    async def _fetch_and_update_suggestions(self, guild_id, title):
        suggestions = await self.get_suggestions(title)
        self.current_suggestions[guild_id] = suggestions
        await self.update_player_message(guild_id)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str = None):
        if not ctx.guild:
            await ctx.reply("Tớ chỉ có thể phát nhạc ở trong Máy Chủ (Server) thôi. 🌸")
            return
            
        if not search:
            await ctx.reply("Cậu muốn tớ phát bài gì nào? Hãy gõ thêm tên bài hát nhé (VD: `!play Nhạc Lofi`) 🌸")
            return

        if not ctx.author.voice:
            await ctx.reply("Cậu phải vào một kênh thoại (Voice Channel) trước thì tớ mới biết phải hát ở đâu chứ! 🌸")
            return
            
        voice_channel = ctx.author.voice.channel
        vc = ctx.voice_client
        self.last_text_channel[ctx.guild.id] = ctx.channel
        
        if vc is None:
            await voice_channel.connect()
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)
            
        try: await ctx.message.delete(delay=2)
        except: pass
        
        status_msg = await ctx.send(f"🔍 Đang tìm kiếm: `{search}`...")
        
        try:
            song_info = await self.extract_info(search, ctx.author.mention)
            queue = self.get_queue(ctx.guild.id)
            queue.append(song_info)
            
            await status_msg.delete()
            
            if not self.is_playing.get(ctx.guild.id, False) and not ctx.voice_client.is_playing():
                self.bot.loop.create_task(self._async_play_next(ctx.guild.id))
            else:
                await self.update_player_message(ctx.guild.id)
                
        except Exception as e:
            logger.error(f"Lỗi tìm nhạc: {e}")
            await status_msg.edit(content=f"Tớ xin lỗi... Có lỗi hệ thống: `{str(e)[:100]}` ❄️")

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.stop()
            try: await ctx.message.delete()
            except: pass
        else:
            await ctx.reply("Hiện tại không có bản nhạc nào đang phát cả cậu ạ.")

    @commands.command(name="stop", aliases=["leave", "disconnect"])
    async def stop(self, ctx):
        vc = ctx.voice_client
        if vc:
            self.get_queue(ctx.guild.id).clear()
            self.is_playing[ctx.guild.id] = False
            self.current_song.pop(ctx.guild.id, None)
            await vc.disconnect()
            await self.update_player_message(ctx.guild.id)
            try: await ctx.message.delete()
            except: pass
        else:
            await ctx.reply("Tớ không ở trong kênh thoại nào cả.")

    async def fetch_lyrics(self, track_name: str) -> str:
        try:
            # Dọn dẹp tên bài hát tốt hơn: Xóa mọi thứ trong ngoặc đơn () hoặc ngoặc vuông []
            clean_track = re.sub(r'\(.*?\) | \[.*?\]', '', track_name).strip()
            # Xóa các từ khóa Official, MV, Remix nếu có
            clean_track = clean_track.replace("Official", "").replace("MV", "").replace("Music Video", "").strip()
            
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
        guild_id = ctx.guild.id
        if not self.is_playing.get(guild_id, False) or guild_id not in self.current_song:
            await ctx.reply("🎵 Hiện tại Ayaka không phát bài nhạc nào cả cậu ạ.")
            return
            
        current = self.current_song[guild_id]
        await ctx.reply(f"🔍 Đang tìm lời bài hát **{current['title']}**...")
        
        lyrics_text = await self.fetch_lyrics(current['title'])
        if not lyrics_text:
            await ctx.send("Tớ không tìm thấy lời bài hát chuẩn cho bản phối này! 😥")
            return
            
        if len(lyrics_text) > 3000:
            lyrics_text = lyrics_text[:3000] + "..."
            
        embed = discord.Embed(title=f"📜 {current['title']}", description=lyrics_text, color=discord.Color.blue())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
