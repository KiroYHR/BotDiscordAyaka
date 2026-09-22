import discord
from discord.ext import commands
import json
import random
import time
import os
import logging
from typing import Dict, List

logger = logging.getLogger("AyakaGacha")

class GachaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.characters = self.load_characters()
        
        # Flatten characters for easier rolling (excluding L rarity which shouldn't be pulled)
        self.pool = {
            'genshin': self.get_pool_by_game('genshin'),
            'hsr': self.get_pool_by_game('hsr'),
            'zzz': self.get_pool_by_game('zzz')
        }

    def load_characters(self) -> Dict:
        try:
            with open("data/characters.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Lỗi tải characters.json: {e}")
            return {"genshin": [], "hsr": [], "zzz": []}

    def get_pool_by_game(self, game: str) -> Dict[str, List[Dict]]:
        game_chars = self.characters.get(game, [])
        return {
            'SSR': [c for c in game_chars if c['rarity'] == 'SSR'],
            'SR': [c for c in game_chars if c['rarity'] == 'SR'],
            'R': [c for c in game_chars if c['rarity'] == 'R'],
        }

    async def init_user_pity(self, user_id: str):
        if not self.db.pool: return
        async with self.db.pool.acquire() as db:
            await db.execute('''
                INSERT INTO gacha_pity (user_id, pity_4star, pity_5star, total_pulls)
                VALUES ($1, 0, 0, 0)
                ON CONFLICT(user_id) DO NOTHING
            ''', str(user_id))

    async def get_user_primogems(self, user_id: str) -> int:
        if not self.db.pool: return 0
        async with self.db.pool.acquire() as db:
            row = await db.fetchrow("SELECT primogems FROM users WHERE user_id = $1", str(user_id))
            return row['primogems'] if row else 0

    async def add_primogems(self, user_id: str, amount: int):
        if not self.db.pool: return
        async with self.db.pool.acquire() as db:
            await db.execute('''
                INSERT INTO users (user_id, primogems)
                VALUES ($1, $2)
                ON CONFLICT(user_id) DO UPDATE SET primogems = users.primogems + $2
            ''', str(user_id), amount)

    @commands.command(name="daily")
    async def daily(self, ctx):
        user_id = str(ctx.author.id)
        now = time.time()
        
        if not self.db.pool:
            return await ctx.reply("❌ Không kết nối được Database!")
            
        async with self.db.pool.acquire() as db:
            row = await db.fetchrow("SELECT last_daily_claim FROM users WHERE user_id = $1", user_id)
            last_claim = row['last_daily_claim'] if row else 0
            
            # Reset at midnight or simple 24h (here simple 24h logic for now)
            if now - last_claim < 86400:
                hours_left = int(86400 - (now - last_claim)) // 3600
                await ctx.reply(f"⏳ Cậu đã nhận danh rùi! Hãy quay lại sau {hours_left} giờ nữa nhé.")
                return
                
            await db.execute('''
                INSERT INTO users (user_id, primogems, last_daily_claim)
                VALUES ($1, 160, $2)
                ON CONFLICT(user_id) DO UPDATE SET 
                    primogems = users.primogems + 160,
                    last_daily_claim = $2
            ''', user_id, now)
            
        await ctx.reply(f"✨ {ctx.author.mention} đã nhận được **160 Nguyên Thạch** từ quà đăng nhập hằng ngày! 💎")

    @commands.command(name="monthly")
    async def monthly(self, ctx):
        user_id = str(ctx.author.id)
        now = time.time()
        
        if not self.db.pool: return
            
        async with self.db.pool.acquire() as db:
            row = await db.fetchrow("SELECT last_monthly_claim FROM users WHERE user_id = $1", user_id)
            last_claim = row['last_monthly_claim'] if row and row.get('last_monthly_claim') else 0
            
            # Simple 30 days logic (2592000 seconds)
            if now - last_claim < 2592000:
                days_left = int(2592000 - (now - last_claim)) // 86400
                await ctx.reply(f"⏳ Cậu đã nhận quà tháng này rùi! Hãy quay lại sau {days_left} ngày nữa nhé.")
                return
                
            await db.execute('''
                INSERT INTO users (user_id, primogems, last_monthly_claim)
                VALUES ($1, 1600, $2)
                ON CONFLICT(user_id) DO UPDATE SET 
                    primogems = users.primogems + 1600,
                    last_monthly_claim = $2
            ''', user_id, now)
            
        await ctx.reply(f"🎁 {ctx.author.mention} đã nhận được **1600 Nguyên Thạch** từ phần quà ưu đãi hằng tháng! 💎 (Tương đương 10 lượt quay)")

    @commands.command(name="gacha", aliases=["quay", "roll"])
    async def gacha(self, ctx, game: str = "genshin", amount: int = 1):
        if amount not in [1, 10]:
            return await ctx.reply("❌ Cậu chỉ có thể gacha x1 hoặc x10 thôi nhé!")
            
        game = game.lower()
        if game not in ['genshin', 'hsr', 'zzz']:
            return await ctx.reply("❌ Game không hợp lệ! Vui lòng chọn: `genshin`, `hsr`, hoặc `zzz`.")
            
        user_id = str(ctx.author.id)
        cost = amount * 160
        
        primos = await self.get_user_primogems(user_id)
        if primos < cost:
            return await ctx.reply(f"❌ Cậu không đủ Nguyên Thạch! Cần {cost} 💎 nhưng cậu chỉ có {primos} 💎. Hãy dùng `!daily` hoặc chờ tháng sau nhé!")
            
        await self.init_user_pity(user_id)
        
        # Pull algorithm
        async with self.db.pool.acquire() as db:
            pity_row = await db.fetchrow("SELECT * FROM gacha_pity WHERE user_id = $1", user_id)
            pity_4star = pity_row['pity_4star']
            pity_5star = pity_row['pity_5star']
            
            results = []
            refund_primos = 0
            
            for _ in range(amount):
                pity_4star += 1
                pity_5star += 1
                
                roll = random.random() * 100 # 0.0 to 100.0
                rarity = 'R'
                
                # Check 5 star (0.6% or Hard Pity 100)
                if roll <= 0.6 or pity_5star >= 100:
                    rarity = 'SSR'
                    pity_5star = 0
                    pity_4star = 0 # reset 4 star pity as well on SSR
                # Check 4 star (5.1% or Soft Pity 10)
                elif roll <= 5.7 or pity_4star >= 10:
                    rarity = 'SR'
                    pity_4star = 0
                
                # Pick character from pool
                pool = self.pool[game].get(rarity, [])
                if not pool: # Fallback if no characters of this rarity exist in JSON
                    pool = self.pool[game].get('R', [])
                    
                if pool:
                    char = random.choice(pool)
                    
                    # Update inventory
                    inv_row = await db.fetchrow("SELECT copies FROM gacha_inventory WHERE user_id=$1 AND character_id=$2", user_id, char['id'])
                    copies = inv_row['copies'] if inv_row else 0
                    
                    if copies >= 7:
                        # Max copies reached, refund
                        if rarity == 'SSR': refund_primos += 1600
                        elif rarity == 'SR': refund_primos += 800
                        else: refund_primos += 160
                        
                        results.append(f"🔁 Đã quy đổi {char['name']} ({rarity}) thành Nguyên Thạch (Max 7).")
                    else:
                        await db.execute('''
                            INSERT INTO gacha_inventory (user_id, character_id, game, copies)
                            VALUES ($1, $2, $3, 1)
                            ON CONFLICT(user_id, character_id) DO UPDATE SET copies = gacha_inventory.copies + 1
                        ''', user_id, char['id'], game)
                        
                        if rarity == 'SSR':
                            results.append(f"🌈 **{char['name']}** (SSR) 🌟🌟🌟🌟🌟")
                        elif rarity == 'SR':
                            results.append(f"🟨 {char['name']} (SR) 🌟🌟🌟🌟")
                        else:
                            results.append(f"⬜ {char['name']} (R)")
            
            # Update pity and deduct cost + add refunds
            net_cost = cost - refund_primos
            await db.execute('''
                UPDATE gacha_pity SET pity_4star=$1, pity_5star=$2, total_pulls=total_pulls+$3 WHERE user_id=$4
            ''', pity_4star, pity_5star, amount, user_id)
            
            await db.execute('UPDATE users SET primogems = primogems - $1 WHERE user_id = $2', net_cost, user_id)
            
        # Send result
        msg = f"🌠 **{ctx.author.name}** đã cầu nguyện x{amount} lần tại banner `{game.upper()}`:\n\n"
        msg += "\n".join(results)
        if refund_primos > 0:
            msg += f"\n\n💎 Đã hoàn trả **{refund_primos} Nguyên Thạch** do nhận nhân vật trùng lặp vượt quá 7 lần!"
        
        await ctx.reply(msg)

async def setup(bot):
    await bot.add_cog(GachaCog(bot))
