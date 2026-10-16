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
    # Genshin Impact
    {"game": "Genshin Impact", "q": "Vị thần cai quản Inazuma là ai?", "opts": ["Raiden Shogun", "Venti", "Zhongli", "Nahida"]},
    {"game": "Genshin Impact", "q": "Anh trai của Kamisato Ayaka tên là gì?", "opts": ["Kamisato Ayato", "Thoma", "Kaedehara Kazuha", "Arataki Itto"]},
    {"game": "Genshin Impact", "q": "Danh xưng thần linh của Zhongli là gì?", "opts": ["Morax", "Barbatos", "Buer", "Focalors"]},
    {"game": "Genshin Impact", "q": "Venti là vị thần của quốc gia nào?", "opts": ["Mondstadt", "Liyue", "Sumeru", "Natlan"]},
    {"game": "Genshin Impact", "q": "Hu Tao sử dụng loại vũ khí nào?", "opts": ["Vũ khí cán dài", "Kiếm đơn", "Pháp khí", "Cung"]},
    {"game": "Genshin Impact", "q": "Nguyên tố của Kamisato Ayaka là gì?", "opts": ["Băng", "Thủy", "Phong", "Lôi"]},
    {"game": "Genshin Impact", "q": "Người bạn đồng hành bay lơ lửng bên cạnh Nhà Lữ Hành tên là gì?", "opts": ["Paimon", "Dainsleif", "Katheryne", "Timmie"]},
    {"game": "Genshin Impact", "q": "Đơn vị tiền tệ phổ biến ở Teyvat là gì?", "opts": ["Mora", "Credit", "Dennies", "Nguyên Thạch"]},
    {"game": "Genshin Impact", "q": "Các Quan Chấp Hành (Harbingers) thuộc tổ chức nào?", "opts": ["Fatui", "Đội Kỵ Sĩ Tây Phong", "Giáo Viện Sumeru", "Thiên Lĩnh Phụng Hành"]},
    {"game": "Genshin Impact", "q": "Diluc là chủ của tửu trang nào?", "opts": ["Tửu trang Dawn", "Tửu trang Angel's Share", "Tửu trang Goth", "Tửu trang Springvale"]},
    {"game": "Genshin Impact", "q": "Hu Tao là đường chủ đời thứ mấy của Vãng Sinh Đường?", "opts": ["77", "70", "68", "99"]},
    {"game": "Genshin Impact", "q": "Furina từng là Thủy Thần của quốc gia nào?", "opts": ["Fontaine", "Inazuma", "Snezhnaya", "Mondstadt"]},
    {"game": "Genshin Impact", "q": "Mẹ của Klee tên là gì?", "opts": ["Alice", "Rosaria", "Jean", "Barbara"]},
    {"game": "Genshin Impact", "q": "Thảo Thần trẻ tuổi của Sumeru còn được gọi là gì?", "opts": ["Kusanali", "Rukkhadevata", "Makoto", "Murata"]},
    {"game": "Genshin Impact", "q": "Thần Hỏa của Natlan có tên là gì?", "opts": ["Mavuika", "Xilonen", "Chasca", "Citlali"]},
    # Honkai: Star Rail
    {"game": "Honkai: Star Rail", "q": "Con tàu chở Đội Khai Phá đi khắp vũ trụ tên là gì?", "opts": ["Tàu Astral", "Tàu Xianzhou", "Tàu Herta", "Tàu Belobog"]},
    {"game": "Honkai: Star Rail", "q": "Hành tinh đầu tiên Đội Khai Phá ghé thăm sau Trạm Không Gian Herta là?", "opts": ["Jarilo-VI", "Penacony", "Xianzhou Luofu", "Amphoreus"]},
    {"game": "Honkai: Star Rail", "q": "Aeon của Con Đường Hủy Diệt là ai?", "opts": ["Nanook", "Qlipoth", "Lan", "Aha"]},
    {"game": "Honkai: Star Rail", "q": "Aeon của Con Đường Săn Bắn là ai?", "opts": ["Lan", "Nanook", "Xipe", "Nous"]},
    {"game": "Honkai: Star Rail", "q": "Kafka là thành viên của tổ chức nào?", "opts": ["Thợ Săn Stellaron", "Công Ty Hòa Bình Liên Hành Tinh (IPC)", "Hội Thiên Tài", "Kẻ Ngu Đeo Mặt Nạ"]},
    {"game": "Honkai: Star Rail", "q": "Ai là người trưởng tàu của tàu Astral?", "opts": ["Pom-Pom", "Himeko", "Welt", "Dan Heng"]},
    {"game": "Honkai: Star Rail", "q": "Tướng quân Thần Sách của Tiên Chu La Phù là ai?", "opts": ["Jing Yuan", "Fu Xuan", "Yanqing", "Blade"]},
    {"game": "Honkai: Star Rail", "q": "March 7th được Đội Khai Phá tìm thấy trong hoàn cảnh nào?", "opts": ["Bị đóng băng trong một khối băng vĩnh cửu", "Ngủ say trong khoang tàu", "Lạc trong giấc mơ Penacony", "Bị giam ở Belobog"]},
    {"game": "Honkai: Star Rail", "q": "Thành phố mộng Penacony do tổ chức nào quản lý?", "opts": ["Gia Tộc (The Family)", "IPC", "Hội Thiên Tài", "Đoàn Kịch Thiên Hà"]},
    # Zenless Zone Zero
    {"game": "Zenless Zone Zero", "q": "Bối cảnh chính của Zenless Zone Zero là thành phố nào?", "opts": ["New Eridu", "Belobog", "Fontaine", "Penacony"]},
    {"game": "Zenless Zone Zero", "q": "Tên của hai anh em Proxy nhân vật chính là gì?", "opts": ["Wise và Belle", "Caelus và Stelle", "Aether và Lumine", "Billy và Nicole"]},
    {"game": "Zenless Zone Zero", "q": "Hai anh em Proxy điều hành cửa hàng nào?", "opts": ["Tiệm băng đĩa Random Play", "Quán mì Waterfall Soup", "Tiệm 141", "Box Galaxy"]},
    {"game": "Zenless Zone Zero", "q": "Trợ lý AI siêu cấp của hai anh em Proxy tên là gì?", "opts": ["Fairy", "Eous", "Pom-Pom", "Paimon"]},
    {"game": "Zenless Zone Zero", "q": "Ellen Joe là thành viên của nhóm nào?", "opts": ["Victoria Housekeeping", "Cunning Hares", "Belobog Heavy Industries", "Section 6"]},
    {"game": "Zenless Zone Zero", "q": "Thủ lĩnh của nhóm Cunning Hares là ai?", "opts": ["Nicole Demara", "Anby Demara", "Grace Howard", "Koleda Belobog"]},
    {"game": "Zenless Zone Zero", "q": "Những sinh vật nhỏ hỗ trợ trong Hollow ở ZZZ được gọi là gì?", "opts": ["Bangboo", "Slime", "Seele", "Trotter"]},
    # Honkai Impact 3rd
    {"game": "Honkai Impact 3rd", "q": "Nữ chính của Honkai Impact 3rd là ai?", "opts": ["Kiana Kaslana", "Raiden Mei", "Bronya Zaychik", "Elysia"]},
]


async def setup(bot):
    await bot.add_cog(MinigameCog(bot))
