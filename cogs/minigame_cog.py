import discord
from discord.ext import commands
import random
import asyncio
import logging

logger = logging.getLogger("AyakaMinigame")

PRIMO = "💎"
COLOR_WIN = 0x7ED6A8
COLOR_LOSE = 0xE57A8C
COLOR_DRAW = 0xF2D27A
COLOR_INFO = 0x8ACBEB

WIN_LINES = [
    "Ồ, vận may hôm nay đứng về phía cậu rồi đó! ✨",
    "Quả là có duyên với thần may mắn của Inazuma nhỉ~ 🌸",
    "Tớ phải học hỏi cậu bí quyết này mới được! ❄️",
    "Hihi, Ayaka xin chúc mừng cậu nhé! 🎐",
]
LOSE_LINES = [
    "Đừng buồn nhé, ván sau chắc chắn sẽ may mắn hơn mà! ❄️",
    "Ưm... hôm nay vận may hơi bướng bỉnh một chút thôi~",
    "Tớ tin là cậu sẽ gỡ lại được ngay thôi! 🌸",
    "Thắng thua là chuyện thường tình của kiếm sĩ, cậu đừng nản nhé! 🍵",
]
DRAW_LINES = [
    "Ồ, tâm ý tương thông rồi! Chúng ta hòa nhau nhé~ 🌸",
    "Cùng một suy nghĩ luôn này, thú vị thật đó! ❄️",
]


class MinigameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_primos(self, user_id: str) -> int:
        if not self.db.pool: return 0
        async with self.db.pool.acquire() as db:
            row = await db.fetchrow("SELECT primogems FROM users WHERE user_id = $1", str(user_id))
            return row['primogems'] if row else 0

    async def update_primos(self, user_id: str, amount: int) -> int:
        """Cộng/trừ Nguyên Thạch, tạo user nếu chưa có. Trả về số dư mới."""
        if not self.db.pool: return 0
        async with self.db.pool.acquire() as db:
            row = await db.fetchrow('''
                INSERT INTO users (user_id, primogems) VALUES ($2, GREATEST($1, 0))
                ON CONFLICT (user_id) DO UPDATE SET primogems = GREATEST(users.primogems + $1, 0)
                RETURNING primogems
            ''', amount, str(user_id))
            return row['primogems'] if row else 0

    async def validate_bet(self, ctx, bet: int, usage: str) -> bool:
        if bet <= 0:
            await ctx.reply(embed=discord.Embed(
                description=f"🌸 Cậu muốn cược bao nhiêu Nguyên Thạch nè?\nCách dùng: `{usage}`",
                color=COLOR_INFO))
            return False
        primos = await self.get_primos(str(ctx.author.id))
        if primos < bet:
            await ctx.reply(embed=discord.Embed(
                description=f"💧 Túi của cậu chỉ còn **{primos:,}** {PRIMO}, chưa đủ để cược **{bet:,}** {PRIMO} đâu.\n"
                            f"Dùng `!daily` để nhận thêm Nguyên Thạch nhé!",
                color=COLOR_LOSE))
            return False
        return True

    # ------------------------------------------------------------------ COINFLIP
    @commands.command(name="coinflip", aliases=["cf", "tungdongxu"])
    async def coinflip(self, ctx, bet: int = 0, side: str = None):
        """!coinflip <cược> [sấp/ngửa]"""
        if not await self.validate_bet(ctx, bet, "!coinflip 10 [sấp/ngửa]"):
            return
        view = CoinflipView(self, ctx.author, bet)
        chosen = CoinflipView.parse_side(side)
        if chosen:
            msg = await ctx.reply(embed=CoinflipView.spinning_embed(ctx.author, bet, chosen, 0))
            view.message = msg
            await view.flip(chosen, msg=msg)
        else:
            embed = discord.Embed(
                title="🪙 Tung Đồng Xu",
                description=f"Ayaka đã cầm sẵn đồng xu rồi nè~\nCậu đoán mặt nào sẽ ngửa lên? (Cược **{bet:,}** {PRIMO})",
                color=COLOR_INFO)
            embed.set_footer(text="Cậu có 30 giây để chọn")
            view.message = await ctx.reply(embed=embed, view=view)

    # ------------------------------------------------------------------ RPS
    @commands.command(name="rps", aliases=["oantuti"])
    async def rps(self, ctx, bet: int = 0):
        """!rps <cược>"""
        if not await self.validate_bet(ctx, bet, "!rps 10"):
            return
        view = RPSView(self, ctx.author, bet)
        view.message = await ctx.reply(embed=RPSView.intro_embed(bet), view=view)

    # ------------------------------------------------------------------ TRIVIA
    @commands.command(name="trivia", aliases=["dovui"])
    async def trivia(self, ctx):
        q = random.choice(TRIVIA_QUESTIONS)
        opts = list(q["opts"])
        correct_text = opts[0]  # đáp án đúng luôn đặt ở vị trí đầu trong ngân hàng câu hỏi
        random.shuffle(opts)
        correct_index = opts.index(correct_text)

        view = TriviaView(self, opts, correct_index, reward=TRIVIA_REWARD)
        view.question = q
        view.message = await ctx.reply(embed=view.build_embed(q), view=view)


# ====================================================================== VIEWS
class BaseGameView(discord.ui.View):
    def __init__(self, cog, user, bet, timeout=30):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.user = user
        self.bet = bet
        self.message = None
        self.finished = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("🌸 Ván này là của người khác rồi, cậu tự mở ván mới nhé!", ephemeral=True)
            return False
        return True

    def disable_all(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        if self.finished or not self.message:
            return
        self.disable_all()
        try:
            embed = self.message.embeds[0] if self.message.embeds else discord.Embed()
            embed.set_footer(text="⌛ Hết giờ rồi, ván này bị hủy và không mất Nguyên Thạch nào cả.")
            await self.message.edit(embed=embed, view=self)
        except Exception:
            pass


class PlayAgainView(discord.ui.View):
    def __init__(self, cog, user, bet, game: str):
        super().__init__(timeout=60)
        self.cog, self.user, self.bet, self.game = cog, user, bet, game

    @discord.ui.button(label="Chơi lại", emoji="🔁", style=discord.ButtonStyle.secondary)
    async def again(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("🌸 Cậu gõ lệnh để mở ván riêng nhé!", ephemeral=True)
        primos = await self.cog.get_primos(str(self.user.id))
        if primos < self.bet:
            return await interaction.response.send_message(
                f"💧 Cậu chỉ còn **{primos:,}** {PRIMO}, không đủ cược **{self.bet:,}** {PRIMO} nữa rồi.", ephemeral=True)
        button.disabled = True
        await interaction.response.edit_message(view=self)
        if self.game == "rps":
            view = RPSView(self.cog, self.user, self.bet)
            view.message = await interaction.followup.send(embed=RPSView.intro_embed(self.bet), view=view, wait=True)
        else:
            view = CoinflipView(self.cog, self.user, self.bet)
            embed = discord.Embed(title="🪙 Tung Đồng Xu",
                                  description=f"Ván mới nè! Cậu đoán mặt nào? (Cược **{self.bet:,}** {PRIMO})",
                                  color=COLOR_INFO)
            view.message = await interaction.followup.send(embed=embed, view=view, wait=True)


class CoinflipView(BaseGameView):
    SIDES = {"Sấp": "🌑", "Ngửa": "🌕"}

    @staticmethod
    def parse_side(side):
        if not side: return None
        s = side.lower()
        if s in ("sấp", "sap", "s", "tails", "t"): return "Sấp"
        if s in ("ngửa", "ngua", "n", "heads", "h"): return "Ngửa"
        return None

    @staticmethod
    def spinning_embed(user, bet, chosen, frame):
        frames = ["🪙 ⤴️  Đồng xu bay vút lên không trung...", "🪙 🔄  Đang xoay tít...", "🪙 ⤵️  Sắp rơi xuống rồi..."]
        embed = discord.Embed(title="🪙 Tung Đồng Xu", description=frames[frame % len(frames)], color=COLOR_INFO)
        embed.add_field(name="Cậu chọn", value=f"{CoinflipView.SIDES[chosen]} **{chosen}**")
        embed.add_field(name="Tiền cược", value=f"**{bet:,}** {PRIMO}")
        return embed

    async def flip(self, chosen: str, interaction: discord.Interaction = None, msg: discord.Message = None):
        self.finished = True
        self.disable_all()
        self.stop()

        async def edit(**kw):
            if interaction:
                await interaction.edit_original_response(**kw)
            else:
                await msg.edit(**kw)

        for frame in range(3):
            await edit(embed=self.spinning_embed(self.user, self.bet, chosen, frame), view=None)
            await asyncio.sleep(0.8)

        # Kiểm tra lại số dư lúc chốt kết quả (tránh cược vượt số dư khi mở nhiều ván)
        if await self.cog.get_primos(str(self.user.id)) < self.bet:
            return await edit(embed=discord.Embed(description="💧 Số dư không còn đủ để cược nữa, ván này bị hủy nhé.", color=COLOR_LOSE))

        result = random.choice(list(self.SIDES))
        win = result == chosen
        balance = await self.cog.update_primos(str(self.user.id), self.bet if win else -self.bet)

        embed = discord.Embed(
            title="🎉 Đoán trúng rồi!" if win else "💧 Tiếc quá, trật mất rồi...",
            description=random.choice(WIN_LINES if win else LOSE_LINES),
            color=COLOR_WIN if win else COLOR_LOSE)
        embed.add_field(name="Cậu chọn", value=f"{self.SIDES[chosen]} **{chosen}**")
        embed.add_field(name="Kết quả", value=f"{self.SIDES[result]} **{result}**")
        embed.add_field(name="Nguyên Thạch", value=f"**{'+' if win else '-'}{self.bet:,}** {PRIMO}")
        embed.set_footer(text=f"Số dư hiện tại: {balance:,} Nguyên Thạch")
        await edit(embed=embed, view=PlayAgainView(self.cog, self.user, self.bet, "coinflip"))

    @discord.ui.button(label="Sấp", emoji="🌑", style=discord.ButtonStyle.primary)
    async def btn_tails(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.flip("Sấp", interaction=interaction)

    @discord.ui.button(label="Ngửa", emoji="🌕", style=discord.ButtonStyle.primary)
    async def btn_heads(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.flip("Ngửa", interaction=interaction)


class RPSView(BaseGameView):
    EMOJI = {"Kéo": "✌️", "Búa": "✊", "Bao": "🖐️"}
    BEATS = {"Kéo": "Bao", "Búa": "Kéo", "Bao": "Búa"}

    @staticmethod
    def intro_embed(bet):
        embed = discord.Embed(
            title="✌️ Oẳn Tù Tì cùng Ayaka",
            description=f"Ayaka đã sẵn sàng rồi đó~ Cậu ra gì nào?\nCược: **{bet:,}** {PRIMO}",
            color=COLOR_INFO)
        embed.set_footer(text="Cậu có 30 giây để chọn")
        return embed

    async def play_round(self, interaction: discord.Interaction, user_choice: str):
        self.finished = True
        self.disable_all()
        self.stop()
        await interaction.response.defer()

        if await self.cog.get_primos(str(self.user.id)) < self.bet:
            return await interaction.edit_original_response(
                embed=discord.Embed(description="💧 Số dư không còn đủ để cược nữa, ván này bị hủy nhé.", color=COLOR_LOSE), view=None)

        ayaka_choice = random.choice(list(self.EMOJI))
        if user_choice == ayaka_choice:
            title, line, color, delta = "🤝 Hòa nhau!", random.choice(DRAW_LINES), COLOR_DRAW, 0
        elif self.BEATS[user_choice] == ayaka_choice:
            title, line, color, delta = "🎉 Cậu thắng rồi!", random.choice(WIN_LINES), COLOR_WIN, self.bet
        else:
            title, line, color, delta = "💧 Ayaka thắng mất rồi~", random.choice(LOSE_LINES), COLOR_LOSE, -self.bet

        balance = await self.cog.update_primos(str(self.user.id), delta) if delta else await self.cog.get_primos(str(self.user.id))

        embed = discord.Embed(title=title, description=line, color=color)
        embed.add_field(name="Cậu", value=f"{self.EMOJI[user_choice]} **{user_choice}**")
        embed.add_field(name="⚔️", value="\u200b")
        embed.add_field(name="Ayaka", value=f"{self.EMOJI[ayaka_choice]} **{ayaka_choice}**")
        change = "không đổi" if delta == 0 else f"{'+' if delta > 0 else '-'}{self.bet:,} {PRIMO}"
        embed.add_field(name="Nguyên Thạch", value=f"**{change}**", inline=False)
        embed.set_footer(text=f"Số dư hiện tại: {balance:,} Nguyên Thạch")
        await interaction.edit_original_response(embed=embed, view=PlayAgainView(self.cog, self.user, self.bet, "rps"))

    @discord.ui.button(label="Kéo", style=discord.ButtonStyle.primary, emoji="✌️")
    async def btn_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_round(interaction, "Kéo")

    @discord.ui.button(label="Búa", style=discord.ButtonStyle.primary, emoji="✊")
    async def btn_rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_round(interaction, "Búa")

    @discord.ui.button(label="Bao", style=discord.ButtonStyle.primary, emoji="🖐️")
    async def btn_paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_round(interaction, "Bao")


class TriviaView(discord.ui.View):
    """Ai trong kênh cũng trả lời được, mỗi người 1 lần, người đúng đầu tiên nhận thưởng."""
    LABELS = ["A", "B", "C", "D"]

    def __init__(self, cog, options, correct_index, reward):
        super().__init__(timeout=TRIVIA_TIMEOUT)
        self.cog = cog
        self.options = options
        self.correct_index = correct_index
        self.reward = reward
        self.answered_users = set()
        self.wrong_users = []
        self.winner = None
        self.message = None
        self.question = None
        for i, _ in enumerate(options):
            btn = discord.ui.Button(label=self.LABELS[i], style=discord.ButtonStyle.secondary)
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def build_embed(self, q, footer=None, color=COLOR_INFO):
        game_icon = {"Genshin Impact": "🌍", "Honkai: Star Rail": "🚂", "Zenless Zone Zero": "📼", "Honkai Impact 3rd": "⚔️"}
        embed = discord.Embed(
            title="🧠 Đố Vui HoYoverse",
            description=f"{game_icon.get(q['game'], '🎮')} *{q['game']}*\n\n**{q['q']}**\n\n" +
                        "\n".join(f"**{self.LABELS[i]}.** {opt}" for i, opt in enumerate(self.options)),
            color=color)
        embed.set_footer(text=footer or f"Ai trả lời đúng đầu tiên nhận {self.reward} Nguyên Thạch • Mỗi người 1 lượt • {TRIVIA_TIMEOUT} giây")
        return embed

    def reveal(self):
        for i, item in enumerate(self.children):
            item.disabled = True
            if i == self.correct_index:
                item.style = discord.ButtonStyle.success

    def make_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if self.winner:
                return await interaction.response.send_message("⌛ Câu này đã có người trả lời đúng rồi!", ephemeral=True)
            if interaction.user.id in self.answered_users:
                return await interaction.response.send_message("🌸 Mỗi người chỉ được trả lời một lần thôi nha~", ephemeral=True)
            self.answered_users.add(interaction.user.id)

            if index != self.correct_index:
                self.wrong_users.append(interaction.user.display_name)
                return await interaction.response.send_message(
                    f"💧 Đáp án **{self.LABELS[index]}** chưa đúng rồi, tiếc quá!", ephemeral=True)

            self.winner = interaction.user
            self.reveal()
            self.stop()
            answer = f"{self.LABELS[self.correct_index]}. {self.options[self.correct_index]}"
            embed = self.build_embed(
                self.question,
                footer=f"Đáp án: {answer}",
                color=COLOR_WIN)
            embed.add_field(name="🎉 Người chiến thắng",
                            value=f"{interaction.user.mention} trả lời chính xác và nhận **{self.reward}** {PRIMO}!")
            await interaction.response.edit_message(embed=embed, view=self)
            try:
                await self.cog.update_primos(str(interaction.user.id), self.reward)
            except Exception as e:
                logger.error(f"Lỗi cộng thưởng trivia: {e}")
        return callback

    async def on_timeout(self):
        if self.winner or not self.message:
            return
        self.reveal()
        answer = f"{self.LABELS[self.correct_index]}. {self.options[self.correct_index]}"
        embed = self.build_embed(self.question, footer=f"⌛ Hết giờ! Đáp án đúng là: {answer}", color=COLOR_LOSE)
        if self.wrong_users:
            embed.add_field(name="Đã thử sức", value=", ".join(self.wrong_users[:10]))
        try:
            await self.message.edit(embed=embed, view=self)
        except Exception:
            pass


# ====================================================================== DATA
TRIVIA_REWARD = 50
TRIVIA_TIMEOUT = 30

# Đáp án đúng luôn đặt ĐẦU TIÊN trong "opts" (sẽ được xáo trộn khi hiển thị)
TRIVIA_QUESTIONS = [
    {"game": "Genshin Impact", "q": "Vị thần cai quản quốc gia Inazuma là ai?", "opts": ["Raiden Shogun", "Venti", "Zhongli", "Nahida"]},
    {"game": "Genshin Impact", "q": "Anh trai của Kamisato Ayaka tên là gì?", "opts": ["Kamisato Ayato", "Thoma", "Kaedehara Kazuha", "Arataki Itto"]},
    {"game": "Genshin Impact", "q": "Danh xưng thần linh (Ma Thần) của Nham Thần Zhongli là gì?", "opts": ["Morax", "Barbatos", "Buer", "Focalors"]},
    {"game": "Genshin Impact", "q": "Venti là phong thần cai quản vùng đất nào?", "opts": ["Mondstadt", "Liyue", "Sumeru", "Fontaine"]},
    {"game": "Genshin Impact", "q": "Hu Tao sử dụng loại vũ khí nào trong chiến đấu?", "opts": ["Vũ khí cán dài", "Kiếm đơn", "Pháp khí", "Trọng kiếm"]},
    {"game": "Genshin Impact", "q": "Nguyên tố Vision của Kamisato Ayaka là gì?", "opts": ["Băng", "Thủy", "Phong", "Lôi"]},
    {"game": "Genshin Impact", "q": "Người bạn đồng hành bay lơ lửng luôn đi cùng Nhà Lữ Hành tên là gì?", "opts": ["Paimon", "Dainsleif", "Katheryne", "Timmie"]},
    {"game": "Genshin Impact", "q": "Đơn vị tiền tệ lưu hành phổ biến nhất khắp đại lục Teyvat là gì?", "opts": ["Mora", "Credit", "Dennies", "Coin"]},
    {"game": "Genshin Impact", "q": "Các Quan Chấp Hành (Harbingers) phục vụ dưới trướng tổ chức nào?", "opts": ["Fatui", "Đội Kỵ Sĩ Tây Phong", "Giáo Viện Sumeru", "Thất Tinh Liyue"]},
    {"game": "Genshin Impact", "q": "Diluc là chủ nhân của trang trại rượu nổi tiếng nào?", "opts": ["Tửu trang Dawn", "Quán Quà Của Thiên Sứ", "Quán Đuôi Mèo", "Trang trại Springvale"]},
    {"game": "Genshin Impact", "q": "Hu Tao là đường chủ đời thứ mấy của Vãng Sinh Đường?", "opts": ["Đời thứ 77", "Đời thứ 70", "Đời thứ 68", "Đời thứ 72"]},
    {"game": "Genshin Impact", "q": "Furina từng đóng vai trò là Thủy Thần của quốc gia nào?", "opts": ["Fontaine", "Inazuma", "Snezhnaya", "Natlan"]},
    {"game": "Genshin Impact", "q": "Mẹ ruột của cô bé Klee là ai?", "opts": ["Alice", "Rhinedottir", "Gold", "Nicole"]},
    {"game": "Genshin Impact", "q": "Thảo Thần hiện tại của vùng đất Sumeru có tôn hiệu là gì?", "opts": ["Kusanali", "Rukkhadevata", "Makoto", "Focalors"]},
    {"game": "Genshin Impact", "q": "Hỏa Thần của quốc gia chiến tranh Natlan có tên là gì?", "opts": ["Mavuika", "Xilonen", "Chasca", "Citlali"]},
    {"game": "Genshin Impact", "q": "Thẩm Phán Tối Cao của Tòa Án Fontaine là ai?", "opts": ["Neuvillette", "Wriothesley", "Clorinde", "Navia"]},
    {"game": "Genshin Impact", "q": "Pháo đài ngầm Meropide ở Fontaine do ai quản lý?", "opts": ["Wriothesley", "Neuvillette", "Sigewinne", "Lyney"]},
    {"game": "Genshin Impact", "q": "Hội Trưởng Đội Kỵ Sĩ Tây Phong hiện tại (đang đi viễn chinh) là ai?", "opts": ["Varka", "Jean", "Kaeya", "Albedo"]},
    {"game": "Genshin Impact", "q": "Tên quán trà bí mật do Hiệp Hội Yashiro quản lý tại Inazuma là gì?", "opts": ["Phòng Trà Komore", "Phòng Trà Yanshang", "Quán Trà Uyuu", "Quán Trà Kim Ngân"]},
    {"game": "Genshin Impact", "q": "Chú chó Shiba làm ông chủ quản lý tại Phòng Trà Komore tên là gì?", "opts": ["Taroumaru", "Kagari", "Komore", "Inu"]},
    {"game": "Genshin Impact", "q": "Ai là người sáng lập kiêm thủ lĩnh của Băng Đảng Arataki?", "opts": ["Arataki Itto", "Kuki Shinobu", "Heizou", "Thoma"]},
    {"game": "Genshin Impact", "q": "Đền Narukami tại Inazuma do ai làm Đại Pháp Chủ (Guuji)?", "opts": ["Yae Miko", "Raiden Ei", "Kujou Sara", "Kokomi"]},
    {"game": "Genshin Impact", "q": "Cố vấn quân sự kiêm Thánh Pháp Chủ của Đảo Watatsumi là ai?", "opts": ["Sangonomiya Kokomi", "Gorou", "Kazuha", "Beidou"]},
    {"game": "Genshin Impact", "q": "Con tàu chiến soái hạm của Thuyền Đội Nam Thập Tự tên là gì?", "opts": ["Tàu Alcor", "Tàu Pearl", "Tàu Waverider", "Tàu Liyue"]},
    {"game": "Genshin Impact", "q": "Người đứng đầu Thất Tinh Liyue giữ vị trí Thiên Quyền Tinh là ai?", "opts": ["Ningguang", "Keqing", "Ganyu", "Yelan"]},
    {"game": "Genshin Impact", "q": "Thư ký tổng vụ mẫn cán nghìn năm của Thất Tinh Liyue là ai?", "opts": ["Ganyu", "Yanfei", "Shenhe", "Xiangling"]},
    {"game": "Genshin Impact", "q": "Thủ hộ Dạ Xoa cuối cùng còn sót lại ở Liyue là ai?", "opts": ["Xiao", "Bosacius", "Menogias", "Indarias"]},
    {"game": "Genshin Impact", "q": "Bảo vật gia truyền mà Kaedehara Kazuha luôn mang theo khi rời Inazuma là gì?", "opts": ["Thanh kiếm Isshin và Vision trống", "Cây quạt tuyết", "Chiếc trâm cài tóc", "Sáo trúc"]},
    {"game": "Genshin Impact", "q": "Ai là Quan Chấp Hành Fatui đứng thứ 11 với mật danh 'Childe'?", "opts": ["Tartaglia", "Scaramouche", "Signora", "Dottore"]},
    {"game": "Genshin Impact", "q": "Cổ quốc đã sụp đổ 500 năm trước vì thảm họa vực sâu tên là gì?", "opts": ["Khaenri'ah", "Sal Vindagnyr", "Remuria", "Enkanomiya"]},
    {"game": "Genshin Impact", "q": "Danh xưng mà người dân Sumeru dùng để gọi Học Phái Kshahrewar là gì?", "opts": ["Diệu Luận Phái", "Tri Luận Phái", "Minh Luận Phái", "Tố Luận Phái"]},
    {"game": "Genshin Impact", "q": "Thần Thú đồng hành cùng đầu bếp Xiangling có tên là gì?", "opts": ["Guoba", "Ushi", "Yuegui", "Oz"]},
    {"game": "Genshin Impact", "q": "Tổ chức ngầm bảo vệ Mondstadt trong bóng tối của Diluc được gọi là gì?", "opts": ["Anh hùng bóng đêm", "Hiệp sĩ bóng đêm", "Thợ săn bóng đêm", "Hắc điệp"]},
    {"game": "Genshin Impact", "q": "Băng Thần của Snezhnaya có tôn hiệu ma thần là gì?", "opts": ["Tsaritsa", "Murata", "Focalors", "Rukkhadevata"]},
    {"game": "Genshin Impact", "q": "Con Rồng Gió Đông từng bị tha hóa tại Mondstadt tên là gì?", "opts": ["Dvalin", "Azhdaha", "Apep", "Durin"]},
    {"game": "Honkai: Star Rail", "q": "Con tàu chở Đội Khai Phá du hành xuyên qua các vì sao tên là gì?", "opts": ["Tàu Astral", "Tàu Xianzhou", "Tàu Belobog", "Tàu Hyperion"]},
    {"game": "Honkai: Star Rail", "q": "Trưởng tàu đáng yêu hình chú thỏ trên tàu Astral tên là gì?", "opts": ["Pom-Pom", "Paimon", "Bangboo", "Herta"]},
    {"game": "Honkai: Star Rail", "q": "Hành tinh đầu tiên Đội Khai Phá ghé thăm sau Trạm Không Gian Herta là?", "opts": ["Jarilo-VI", "Penacony", "Xianzhou Luofu", "Amphoreus"]},
    {"game": "Honkai: Star Rail", "q": "Aeon của Vận Mệnh Hủy Diệt là ai?", "opts": ["Nanook", "Qlipoth", "Lan", "Aha"]},
    {"game": "Honkai: Star Rail", "q": "Aeon của Vận Mệnh Săn Bắn là ai?", "opts": ["Lan", "Nanook", "Yaoshi", "Xipe"]},
    {"game": "Honkai: Star Rail", "q": "Aeon của Vận Mệnh Bảo Hộ đại diện cho việc xây dựng bức tường thiên hà là ai?", "opts": ["Qlipoth", "Fuli", "Nous", "Ena"]},
    {"game": "Honkai: Star Rail", "q": "Aeon của Vận Mệnh Vui Vẻ luôn tìm kiếm tiếng cười vũ trụ là ai?", "opts": ["Aha", "IX", "Tayzzyronth", "Terminus"]},
    {"game": "Honkai: Star Rail", "q": "Kafka là thành viên cốt cán của tổ chức ngầm nào?", "opts": ["Thợ Săn Stellaron", "Công Ty Hành Tinh Hòa Bình (IPC)", "Hội Thiên Tài", "Gia Tộc Penacony"]},
    {"game": "Honkai: Star Rail", "q": "Thủ lĩnh bí ẩn đứng sau điều phối Thợ Săn Stellaron có tên là gì?", "opts": ["Elio", "Blade", "Sam", "Silver Wolf"]},
    {"game": "Honkai: Star Rail", "q": "Chiến giáp Sam rực lửa của Thợ Săn Stellaron thực chất do ai điều khiển?", "opts": ["Firefly", "Kafka", "Silver Wolf", "Ruan Mei"]},
    {"game": "Honkai: Star Rail", "q": "Tướng quân Thần Sách trấn giữ Tiên Chu La Phù (Xianzhou Luofu) là ai?", "opts": ["Jing Yuan", "Fu Xuan", "Yanqing", "Feixiao"]},
    {"game": "Honkai: Star Rail", "q": "Thái Bốc Trưởng của Sở Thái Bốc Tiên Chu La Phù là ai?", "opts": ["Fu Xuan", "Qingque", "Yukong", "Hanya"]},
    {"game": "Honkai: Star Rail", "q": "Ẩm Nguyệt Quân của Tộc Vidyadhara tiền kiếp là hiện thân của ai?", "opts": ["Dan Heng", "Blade", "Jingliu", "Luocha"]},
    {"game": "Honkai: Star Rail", "q": "Kiếm thủ bất tử mang vết thương Ma Âm Nhập Thân của Thợ Săn Stellaron là ai?", "opts": ["Blade", "Jing Yuan", "Luka", "Boothill"]},
    {"game": "Honkai: Star Rail", "q": "Thành phố mộng Penacony được mệnh danh là gì?", "opts": ["Hành Tinh Lễ Hội", "Hành Tinh Băng Giá", "Thành Phố Ngầm", "Trạm Không Gian"]},
    {"game": "Honkai: Star Rail", "q": "Ca sĩ thần tượng nổi tiếng toàn dải ngân hà đến từ Penacony là ai?", "opts": ["Robin", "Sunday", "Sparkle", "Black Swan"]},
    {"game": "Honkai: Star Rail", "q": "Anh trai của ca sĩ Robin, người từng lãnh đạo Gia Tộc Oak ở Penacony là ai?", "opts": ["Sunday", "Gallagher", "Aventurine", "Dr. Ratio"]},
    {"game": "Honkai: Star Rail", "q": "Aventurine là thành viên cấp cao thuộc bộ phận nào của IPC?", "opts": ["Bộ Phận Đầu Tư Chiến Lược (10 Người Có Trái Tim Đá)", "Bộ Phận Tiếp Thị", "Bộ Phận Vật Tư", "Bộ Phận Tài Chính"]},
    {"game": "Honkai: Star Rail", "q": "Viên đá nền tảng đại diện cho Aventurine trong IPC là loại đá nào?", "opts": ["Đá Khổng Tước (Aventurine)", "Đá Topaz", "Đá Ngọc Bích (Jade)", "Đá Hổ Phách"]},
    {"game": "Honkai: Star Rail", "q": "Nghệ danh thật của nhân viên thu hồi nợ Topaz trong IPC là gì?", "opts": ["Jelena", "Numby", "Aventurine", "Clara"]},
    {"game": "Honkai: Star Rail", "q": "Sinh vật nhỏ bé đáng yêu luôn đi cùng Topaz để dò tìm kho báu tên là gì?", "opts": ["Numby", "Diting", "Peppy", "Pom-Pom"]},
    {"game": "Honkai: Star Rail", "q": "Thành viên số 81 của Hội Thiên Tài chuyên nghiên cứu sinh mệnh là ai?", "opts": ["Ruan Mei", "Herta", "Screwllum", "Stephen Lloyd"]},
    {"game": "Honkai: Star Rail", "q": "Chủ nhân thực sự của Trạm Không Gian Herta là ai?", "opts": ["Herta (Đại Herta)", "Asta", "Arlan", "Screwllum"]},
    {"game": "Honkai: Star Rail", "q": "Trưởng trạm quyền lực điều hành hàng ngày tại Trạm Không Gian Herta là ai?", "opts": ["Asta", "Herta", "Ruan Mei", "Yukong"]},
    {"game": "Honkai: Star Rail", "q": "Bác sĩ mang hộp cứu thương kỳ bí du hành đến La Phù là ai?", "opts": ["Luocha", "Gallagher", "Baizhu", "Sampo"]},
    {"game": "Honkai: Star Rail", "q": "Thợ Săn Tiên Chu kiêm Sư Tôn của Jing Yuan từng mang danh kiếm thủ số 1 là ai?", "opts": ["Jingliu", "Feixiao", "Yukong", "Hanya"]},
    {"game": "Honkai: Star Rail", "q": "Thiên Sách Tướng Quân của Tiên Chu Diệu Thanh (Yaoqing) là ai?", "opts": ["Feixiao", "Jing Yuan", "Huohuo", "Lingsha"]},
    {"game": "Honkai: Star Rail", "q": "Cảnh Binh Thiên Hà hệ cơ giới mang phong cách cao bồi viễn tây tên là gì?", "opts": ["Boothill", "Argenti", "Luka", "Sunday"]},
    {"game": "Honkai: Star Rail", "q": "Kỵ Sĩ Thuần Khiết của Đội Kỵ Sĩ Đẹp luôn ca tụng Nữ Thần Idrila là ai?", "opts": ["Argenti", "Boothill", "Welt", "Gepard"]},
    {"game": "Honkai: Star Rail", "q": "Vũ khí chính mà Nhà Khai Phá sử dụng khi thức tỉnh Vận Mệnh Hủy Diệt là gì?", "opts": ["Gậy bóng chày", "Ngọn giáo rực lửa", "Mũ phớt hòa hợp", "Kiếm ánh sáng"]},
    {"game": "Honkai: Star Rail", "q": "Tên thành phố duy nhất còn người sinh sống trên hành tinh băng tuyết Jarilo-VI là gì?", "opts": ["Belobog", "New Eridu", "Luofu", "Khaenri'ah"]},
    {"game": "Honkai: Star Rail", "q": "Thủ lĩnh Đấng Bảo Vệ Tối Cao đời thứ 19 của thành Belobog là ai?", "opts": ["Bronya Rand", "Cocolia Rand", "Serval Landau", "Natasha"]},
    {"game": "Honkai: Star Rail", "q": "Người bảo hộ của cô bé mồ côi Clara dưới lòng đất Belobog là ai?", "opts": ["Robot Svarog", "Oleg", "Sampo", "Luka"]},
    {"game": "Honkai: Star Rail", "q": "Thành viên Kẻ Ngu Đeo Mặt Nạ có tài biến hóa khôn lường tại Penacony là ai?", "opts": ["Sparkle", "Sampo", "Giovanni", "Black Swan"]},
    {"game": "Honkai: Star Rail", "q": "Ký Ức Chi Đình cử nhà chiêm tinh nào đến Penacony thu thập ký ức?", "opts": ["Black Swan", "Acheron", "Robin", "Cipher"]},
    {"game": "Zenless Zone Zero", "q": "Bối cảnh nền văn minh đô thị cuối cùng trong Zenless Zone Zero là thành phố nào?", "opts": ["New Eridu", "Belobog", "Mondstadt", "Penacony"]},
    {"game": "Zenless Zone Zero", "q": "Cặp anh em Proxy nhân vật chính huyền thoại có tên là gì?", "opts": ["Wise và Belle", "Aether và Lumine", "Caelus và Stelle", "Billy và Nicole"]},
    {"game": "Zenless Zone Zero", "q": "Tiệm cho thuê băng đĩa phim mà hai anh em Proxy vận hành tên là gì?", "opts": ["Random Play", "Box Galaxy", "Waterfall Soup", "Tiệm 141"]},
    {"game": "Zenless Zone Zero", "q": "Trợ lý trí tuệ nhân tạo siêu cấp đồng hành cùng hai anh em Proxy là ai?", "opts": ["Fairy", "Paimon", "Pom-Pom", "Eous"]},
    {"game": "Zenless Zone Zero", "q": "Những sinh vật cơ khí nhỏ bé hỗ trợ đắc lực trong Lỗ Hổng (Hollow) được gọi là gì?", "opts": ["Bangboo", "Slime", "Trotter", "Seele"]},
    {"game": "Zenless Zone Zero", "q": "Chú Bangboo mang mã hiệu 'Eous' thuộc quyền sở hữu của ai?", "opts": ["Wise và Belle (Phaethon)", "Nicole Demara", "Anby Demara", "Koleda"]},
    {"game": "Zenless Zone Zero", "q": "Nhóm thợ săn tiền thưởng do Nicole Demara thành lập và lãnh đạo có tên là gì?", "opts": ["Cunning Hares (Nhà Thỏ Xảo Quyệt)", "Victoria Housekeeping", "Section 6", "Belobog Heavy Industries"]},
    {"game": "Zenless Zone Zero", "q": "Thành viên người máy hài hước hâm mộ cuồng nhiệt phim 'Kỵ Sĩ Ánh Sao' trong Cunning Hares là ai?", "opts": ["Billy Kid", "Anton Ivanov", "Ben Bigger", "Seth Lowell"]},
    {"game": "Zenless Zone Zero", "q": "Cô gái điềm tĩnh mê ăn bánh burger của nhóm Cunning Hares tên là gì?", "opts": ["Anby Demara", "Nicole Demara", "Nekomata", "Corin"]},
    {"game": "Zenless Zone Zero", "q": "Cô nàng người mèo nghịch ngợm nhanh nhẹn trong Cunning Hares tên là gì?", "opts": ["Nekomiya Mana (Nekomata)", "Ellen Joe", "Piper Wheel", "Lucy"]},
    {"game": "Zenless Zone Zero", "q": "Công ty xây dựng công nghiệp nặng Belobog do nữ chủ tịch trẻ tuổi nào đứng đầu?", "opts": ["Koleda Belobog", "Grace Howard", "Piper Wheel", "Lucy"]},
    {"game": "Zenless Zone Zero", "q": "Chuyên viên cơ khí cuồng máy móc và coi máy móc như con trong Belobog Heavy Industries là ai?", "opts": ["Grace Howard", "Koleda Belobog", "Corin Wickes", "Rina"]},
    {"game": "Zenless Zone Zero", "q": "Chú gấu khổng lồ làm giám đốc tài chính mẫn cán của Công Nghiệp Nặng Belobog tên là gì?", "opts": ["Ben Bigger", "Billy Kid", "Anton Ivanov", "Von Lycaon"]},
    {"game": "Zenless Zone Zero", "q": "Tổ chức dịch vụ quản gia và người hầu cao cấp đầy bí ẩn tại New Eridu tên là gì?", "opts": ["Victoria Housekeeping", "Cunning Hares", "Section 6", "Sons of Calydon"]},
    {"game": "Zenless Zone Zero", "q": "Quản gia người sói lịch thiệp, thanh lịch của Victoria Housekeeping tên là gì?", "opts": ["Von Lycaon", "Hugo Vlad", "Seth Lowell", "Lighter"]},
    {"game": "Zenless Zone Zero", "q": "Nữ sinh hầu gái cá mập lạnh lùng mê kẹo mút trong Victoria Housekeeping tên là gì?", "opts": ["Ellen Joe", "Corin Wickes", "Alexandrina", "Lucy"]},
    {"game": "Zenless Zone Zero", "q": "Cô bé hầu gái nhút nhát sử dụng chiếc cưa máy khổng lồ trong Victoria Housekeeping là ai?", "opts": ["Corin Wickes", "Ellen Joe", "Rina", "Anby Demara"]},
    {"game": "Zenless Zone Zero", "q": "Băng đảng mô-tô xe máy thống trị vùng ngoại ô Outer Ring tên là gì?", "opts": ["Sons of Calydon (Những Đứa Con Của Calydon)", "Cunning Hares", "Obol Squad", "Section 6"]},
    {"game": "Zenless Zone Zero", "q": "Thủ lĩnh kiêm 'Đại Ca' cưỡi mô-tô dũng mãnh của Sons of Calydon là ai?", "opts": ["Caesar King", "Burnice White", "Piper Wheel", "Lucy"]},
    {"game": "Zenless Zone Zero", "q": "Cô nàng bartender chuyên pha chế đồ uống bằng súng phun lửa rực cháy của Calydon là ai?", "opts": ["Burnice White", "Caesar King", "Lucy", "Piper Wheel"]},
    {"game": "Zenless Zone Zero", "q": "Đội trưởng tài ba của Biệt Đội Ứng Phó Lỗ Hổng Số 6 (Section 6) là ai?", "opts": ["Hoshimi Miyabi", "Tsukishiro Yanagi", "Asaba Harumasa", "Soukaku"]},
    {"game": "Zenless Zone Zero", "q": "Phó đội trưởng thông minh kiêm quân sư của Section 6 là ai?", "opts": ["Tsukishiro Yanagi", "Hoshimi Miyabi", "Soukaku", "Astra Yao"]},
    {"game": "Zenless Zone Zero", "q": "Quỷ lùn màu xanh luôn thèm ăn cầm cây quạt gió trong Section 6 tên là gì?", "opts": ["Soukaku", "Billy", "Eous", "Corin"]},
    {"game": "Zenless Zone Zero", "q": "Tổ chức chấp pháp trị an chuyên duy trì luật lệ tại New Eridu là gì?", "opts": ["Đội Đặc Nhiệm Hình Sự (N.E.P.S)", "Cunning Hares", "Obol Squad", "Hội Tri Thức"]},
    {"game": "Zenless Zone Zero", "q": "Đội trưởng Đội Hình Sự trực thuộc Ty Trị An New Eridu là ai?", "opts": ["Zhu Yuan", "Qingyi", "Jane Doe", "Seth Lowell"]},
    {"game": "Honkai Impact 3rd", "q": "Nữ chiến binh Valkyrie nhân vật chính mang dòng máu Kaslana là ai?", "opts": ["Kiana Kaslana", "Raiden Mei", "Bronya Zaychik", "Fu Hua"]},
    {"game": "Honkai Impact 3rd", "q": "Người bạn thân thiết của Kiana sau này thức tỉnh thành Herrscher of Thunder là ai?", "opts": ["Raiden Mei", "Bronya Zaychik", "Theresa Apocalypse", "Himeko"]},
    {"game": "Honkai Impact 3rd", "q": "Nữ phi công lái robot Project Bunny xuất thân từ trại trẻ mồ côi Cocolia là ai?", "opts": ["Bronya Zaychik", "Seele Vollerei", "Sin Mal", "Liliya"]},
    {"game": "Honkai Impact 3rd", "q": "Hiệu trưởng trường đào tạo nữ chiến binh Thánh Freya (St. Freya) là ai?", "opts": ["Theresa Apocalypse", "Murata Himeko", "Otto Apocalypse", "Einstein"]},
    {"game": "Honkai Impact 3rd", "q": "Đại giáo chủ trị vì tổ chức Schicksal hơn 500 năm để hồi sinh người yêu là ai?", "opts": ["Otto Apocalypse", "Kevin Kaslana", "Welt Yang", "Siegfried Kaslana"]},
    {"game": "Honkai Impact 3rd", "q": "Người yêu sâu đậm thời thơ ấu mà Otto Apocalypse luôn tìm cách hồi sinh là ai?", "opts": ["Kallen Kaslana", "Yae Sakura", "Cecilia Schariac", "Theresa"]},
    {"game": "Honkai Impact 3rd", "q": "Thủ lĩnh tối cao của tổ chức Anti-Entropy kế thừa Danh Xưng Herrscher of Reason là ai?", "opts": ["Welt Yang", "Einstein", "Tesla", "Siegfried"]},
    {"game": "Honkai Impact 3rd", "q": "Giáo viên chủ nhiệm quả cảm của Kiana đã hy sinh trong trận chiến 'Bài Học Cuối Cùng' là ai?", "opts": ["Murata Himeko", "Theresa Apocalypse", "Fu Hua", "Rita Rossweisse"]},
    {"game": "Honkai Impact 3rd", "q": "Chiến binh bảo vệ Thần Châu hàng nghìn năm còn được gọi là Xích Tinh Tiên Nhân là ai?", "opts": ["Fu Hua", "Yae Sakura", "Sushang", "Kiana"]},
    {"game": "Honkai Impact 3rd", "q": "Valkyrie cấp S cầm lưỡi hái trung thành của tổ chức Schicksal là ai?", "opts": ["Rita Rossweisse", "Durandal", "Kiana", "Theresa"]},
    {"game": "Honkai Impact 3rd", "q": "Nữ chiến binh Valkyrie mạnh nhất Schicksal mang tên Bianka Ataegina được biết đến với biệt hiệu gì?", "opts": ["Durandal", "Rita", "Cecilia", "Himeko"]},
    {"game": "Honkai Impact 3rd", "q": "Thủ lĩnh dẫn dắt 13 Anh Kiệt Tiền Văn Minh (Flame-Chasers) chống lại Honkai là ai?", "opts": ["Kevin Kaslana", "Elysia", "Kalpas", "Su"]},
    {"game": "Honkai Impact 3rd", "q": "Anh Kiệt số 2 mang danh nghĩa 'Chân Ngã' với mái tóc hồng rực rỡ và nụ cười ấm áp là ai?", "opts": ["Elysia", "Eden", "Mobius", "Vill-V"]},
    {"game": "Honkai Impact 3rd", "q": "Thanh thần kiếm God Key thứ 7 rực lửa của Murata Himeko tên là gì?", "opts": ["Judgement of Shamash", "Key of Reason", "Oath of Judah", "Abyss Flower"]},
    {"game": "Honkai Impact 3rd", "q": "Trực thăng chiến hạm nổi tiếng của Thánh Freya đưa các Valkyrie vào chiến trường tên là gì?", "opts": ["Hyperion", "Astral", "Helios", "Selene"]},
]


async def setup(bot):
    await bot.add_cog(MinigameCog(bot))
