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
        self.unified_pool = self.build_unified_pool()

    def load_characters(self) -> Dict:
        try:
            with open("data/characters.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Lỗi tải characters.json: {e}")
            return {"genshin": [], "hsr": [], "zzz": []}

    def build_unified_pool(self) -> Dict[str, List[Dict]]:
        pool = {'L': [], 'SSR': [], 'SR': [], 'R': []}
        for game, chars in self.characters.items():
            for c in chars:
                c['game'] = game  # Inject game key into the dict for database saving
                rarity = c.get('rarity', 'R')
                if rarity in pool:
                    pool[rarity].append(c)
        return pool

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

    @commands.command(name="gacha", aliases=["quay", "roll"])
    async def gacha(self, ctx, amount: int = 1):
        if amount not in [1, 10]:
            return await ctx.reply("❌ Cậu chỉ có thể gacha x1 hoặc x10 thôi nhé! (VD: `!gacha 10`)")
            
        user_id = str(ctx.author.id)
        cost = amount * 160
        
        primos = await self.get_user_primogems(user_id)
        if primos < cost:
            return await ctx.reply(f"❌ Cậu không đủ Nguyên Thạch! Cần {cost} 💎 nhưng cậu chỉ có {primos} 💎. Hãy dùng `!daily` hoặc chờ tháng sau nhé!")
            
        await self.init_user_pity(user_id)
        
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
                
                # Check L (0.1%)
                if roll <= 0.1:
                    rarity = 'L'
                    # L doesn't reset normal pity according to user
                # Check SSR (0.6% or Hard Pity 100)
                elif roll <= 0.7 or pity_5star >= 100:
                    rarity = 'SSR'
                    pity_5star = 0
                    pity_4star = 0
                # Check SR (5.1% or Soft Pity 10)
                elif roll <= 5.8 or pity_4star >= 10:
                    rarity = 'SR'
                    pity_4star = 0
                
                pool = self.unified_pool.get(rarity, [])
                if not pool: # Fallback
                    pool = self.unified_pool.get('R', [])
                    rarity = 'R'
                    
                if pool:
                    char = random.choice(pool)
                    char_id = char['id']
                    game = char['game']
                    
                    inv_row = await db.fetchrow("SELECT copies FROM gacha_inventory WHERE user_id=$1 AND character_id=$2", user_id, char_id)
                    copies = inv_row['copies'] if inv_row else 0
                    
                    if copies >= 7:
                        if rarity == 'L': refund_primos += 1600
                        elif rarity == 'SSR': refund_primos += 1600
                        elif rarity == 'SR': refund_primos += 800
                        else: refund_primos += 160
                        
                        results.append(f"🔁 Quy đổi: {char['name']} ({rarity}) ➔ Nguyên Thạch (Max 7).")
                    else:
                        await db.execute('''
                            INSERT INTO gacha_inventory (user_id, character_id, game, copies)
                            VALUES ($1, $2, $3, 1)
                            ON CONFLICT(user_id, character_id) DO UPDATE SET copies = gacha_inventory.copies + 1
                        ''', user_id, char_id, game)
                        
                        if rarity == 'L':
                            results.append(f"🔥 **{char['name']}** (LIMITED) 💠💠💠💠💠💠")
                        elif rarity == 'SSR':
                            results.append(f"🌈 **{char['name']}** (SSR) 🌟🌟🌟🌟🌟")
                        elif rarity == 'SR':
                            results.append(f"🟨 {char['name']} (SR) 🌟🌟🌟🌟")
                        else:
                            results.append(f"⬜ {char['name']} (R)")
            
            net_cost = cost - refund_primos
            await db.execute('''
                UPDATE gacha_pity SET pity_4star=$1, pity_5star=$2, total_pulls=total_pulls+$3 WHERE user_id=$4
            ''', pity_4star, pity_5star, amount, user_id)
            
            await db.execute('UPDATE users SET primogems = primogems - $1 WHERE user_id = $2', net_cost, user_id)
            
        msg = f"🌠 **{ctx.author.name}** đã cầu nguyện x{amount} lần vào Bể chứa Đa Vũ Trụ:\n\n"
        msg += "\n".join(results)
        if refund_primos > 0:
            msg += f"\n\n💎 Đã hoàn trả **{refund_primos} Nguyên Thạch** do nhận thẻ trùng lặp!"
        
        await ctx.reply(msg)

async def setup(bot):
    await bot.add_cog(GachaCog(bot))
