import discord
from discord.ext import commands
import random
import asyncio
import logging

logger = logging.getLogger("AyakaMinigame")

class MinigameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    async def get_primos(self, user_id: str) -> int:
        if not self.db.pool: return 0
        async with self.db.pool.acquire() as db:
            row = await db.fetchrow("SELECT primogems FROM users WHERE user_id = $1", str(user_id))
            return row['primogems'] if row else 0

    async def update_primos(self, user_id: str, amount: int):
        if not self.db.pool: return
        async with self.db.pool.acquire() as db:
            await db.execute('''
                UPDATE users SET primogems = primogems + $1 WHERE user_id = $2
            ''', amount, str(user_id))

    @commands.command(name="coinflip", aliases=["cf", "tungdongxu"])
    async def coinflip(self, ctx, bet: int = 0):
        if bet <= 0:
            return await ctx.reply("❌ Cậu phải cược một số Nguyên Thạch lớn hơn 0 nhé!")
            
        user_id = str(ctx.author.id)
        primos = await self.get_primos(user_id)
        
        if primos < bet:
            return await ctx.reply(f"❌ Cậu không có đủ Nguyên Thạch! Cậu chỉ có {primos} 💎.")
            
        result = random.choice(["Sấp", "Ngửa"])
        win = random.choice([True, False])
        
        if win:
            await self.update_primos(user_id, bet)
            await ctx.reply(f"🪙 Đồng xu lật ra: **{result}**!\n🎉 Chúc mừng cậu đã đoán trúng và nhận được **{bet * 2}** Nguyên Thạch (Lãi {bet} 💎)!")
        else:
            await self.update_primos(user_id, -bet)
            await ctx.reply(f"🪙 Đồng xu lật ra: **{result}**!\n😢 Ôi không, cậu đoán sai rùi và mất đi **{bet}** Nguyên Thạch. Lần sau may mắn hơn nhé!")

    @commands.command(name="rps", aliases=["oantuti"])
    async def rps(self, ctx, bet: int = 0):
        if bet <= 0:
            return await ctx.reply("❌ Cậu phải cược một số Nguyên Thạch lớn hơn 0 nhé!")
            
        user_id = str(ctx.author.id)
        primos = await self.get_primos(user_id)
        
        if primos < bet:
            return await ctx.reply(f"❌ Cậu không có đủ Nguyên Thạch! Cậu chỉ có {primos} 💎.")
            
        view = RPSView(self, ctx.author, bet)
        await ctx.reply(f"✌️✊🖐️ Hãy chọn nước đi của cậu để đấu Oẳn Tù Tì với Ayaka! (Cược: {bet} 💎)", view=view)

    @commands.command(name="trivia", aliases=["dovui"])
    async def trivia(self, ctx):
        questions = [
            {"q": "Vị thần của Inazuma là ai?", "opts": ["Venti", "Zhongli", "Raiden Shogun", "Nahida"], "ans": 2},
            {"q": "Hành tinh mà đội tàu Astral dừng chân đầu tiên là?", "opts": ["Jarilo-VI", "Penacony", "Herta Space Station", "Xianzhou Luofu"], "ans": 0},
            {"q": "Tên của tổ chức quản lý Hollow ở New Eridu là?", "opts": ["H.A.N.D.", "Knights of Favonius", "Fatui", "IPC"], "ans": 0},
            {"q": "Anh trai của Kamisato Ayaka tên là gì?", "opts": ["Kamisato Ayato", "Thoma", "Kazuha", "Diluc"], "ans": 0},
        ]
        
        q = random.choice(questions)
        view = TriviaView(self, ctx.author, q['ans'])
        
        msg = f"🧠 **Đố vui HoYoverse!** (Thưởng 50 💎)\n\n**Câu hỏi:** {q['q']}\n"
        for i, opt in enumerate(q['opts']):
            msg += f"**{i+1}.** {opt}\n"
            
        await ctx.reply(msg, view=view)

class RPSView(discord.ui.View):
    def __init__(self, cog, user, bet):
        super().__init__(timeout=30)
        self.cog = cog
        self.user = user
        self.bet = bet

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Cậu không phải là người chơi ván này!", ephemeral=True)
            return False
        return True

    async def play_round(self, interaction: discord.Interaction, user_choice: str):
        ayaka_choice = random.choice(["Kéo", "Búa", "Bao"])
        
        rules = {
            "Kéo": {"Kéo": "Hòa", "Búa": "Thua", "Bao": "Thắng"},
            "Búa": {"Kéo": "Thắng", "Búa": "Hòa", "Bao": "Thua"},
            "Bao": {"Kéo": "Thua", "Búa": "Thắng", "Bao": "Hòa"}
        }
        
        result = rules[user_choice][ayaka_choice]
        
        if result == "Thắng":
            await self.cog.update_primos(str(self.user.id), self.bet)
            msg = f"✌️ Cậu ra **{user_choice}**, Ayaka ra **{ayaka_choice}**.\n🎉 Cậu đã **THẮNG** và nhận được {self.bet * 2} Nguyên Thạch!"
        elif result == "Thua":
            await self.cog.update_primos(str(self.user.id), -self.bet)
            msg = f"✌️ Cậu ra **{user_choice}**, Ayaka ra **{ayaka_choice}**.\n😢 Cậu đã **THUA** và mất {self.bet} Nguyên Thạch!"
        else:
            msg = f"✌️ Cậu ra **{user_choice}**, Ayaka ra **{ayaka_choice}**.\n🤝 **HÒA**! Không ai mất Nguyên Thạch cả."
            
        # Disable buttons
        for item in self.children:
            item.disabled = True
            
        await interaction.response.edit_message(content=msg, view=self)

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
    def __init__(self, cog, user, correct_index):
        super().__init__(timeout=15)
        self.cog = cog
        self.user = user
        self.correct_index = correct_index

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Câu hỏi này không dành cho cậu!", ephemeral=True)
            return False
        return True

    async def check_answer(self, interaction: discord.Interaction, choice: int):
        for item in self.children:
            item.disabled = True
            
        if choice == self.correct_index:
            await self.cog.update_primos(str(self.user.id), 50)
            await interaction.response.edit_message(content="🎉 Chính xác! Cậu nhận được 50 Nguyên Thạch!", view=self)
        else:
            await interaction.response.edit_message(content="😢 Sai rồi! Chúc cậu may mắn lần sau nhé.", view=self)

    @discord.ui.button(label="1", style=discord.ButtonStyle.secondary)
    async def btn_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 0)

    @discord.ui.button(label="2", style=discord.ButtonStyle.secondary)
    async def btn_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 1)
        
    @discord.ui.button(label="3", style=discord.ButtonStyle.secondary)
    async def btn_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 2)
        
    @discord.ui.button(label="4", style=discord.ButtonStyle.secondary)
    async def btn_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 3)

async def setup(bot):
    await bot.add_cog(MinigameCog(bot))
