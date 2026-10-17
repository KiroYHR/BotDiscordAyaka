import discord
from discord.ext import commands
import json
import random
import os
import logging

logger = logging.getLogger("AyakaGacha")

class GachaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.unified_pool = self.load_unified_pool()

    def load_unified_pool(self):
        pool = {'L': [], 'SSR': [], 'SR': [], 'R': []}
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'characters.json')
        if not os.path.exists(path):
            logger.error("Không tìm thấy file data/characters.json!")
            return pool
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for game, chars in data.items():
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

    async def perform_pulls(self, user_id: str, amount: int) -> dict:
        """Hàm dùng chung để thực hiện gacha cho cả Discord command và Web API."""
        cost = amount * 160
        primos = await self.get_user_primogems(user_id)
        if primos < cost:
            return {
                "success": False,
                "msg": f"Cậu không đủ Nguyên Thạch! Cần {cost} 💎 nhưng hiện chỉ có {primos} 💎."
            }

        await self.init_user_pity(user_id)

        async with self.db.pool.acquire() as db:
            pity_row = await db.fetchrow("SELECT * FROM gacha_pity WHERE user_id = $1", user_id)
            pity_4star = pity_row['pity_4star']
            pity_5star = pity_row['pity_5star']

            results = []
            pulled_cards = []
            refund_primos = 0

            for _ in range(amount):
                pity_4star += 1
                pity_5star += 1

                roll = random.random() * 100 # 0.0 to 100.0
                rarity = 'R'

                # Check L (0.1%)
                if roll <= 0.1:
                    rarity = 'L'
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
                if not pool:
                    pool = self.unified_pool.get('R', [])
                    rarity = 'R'

                if pool:
                    char = random.choice(pool)
                    char_id = char['id']
                    game = char['game']

                    inv_row = await db.fetchrow("SELECT copies FROM gacha_inventory WHERE user_id=$1 AND character_id=$2", user_id, char_id)
                    copies = inv_row['copies'] if inv_row else 0

                    if copies >= 7:
                        # Hoàn trả khi đã max C6 (7 bản): R = 0, SR = 160, SSR = 480, L = 800
                        if rarity == 'L':
                            refund_primos += 800
                            results.append(f"🔁 **{char['name']}** (LIMITED) ➔ Max 7 bản! Quy đổi **5 lượt** (+800 💎)")
                        elif rarity == 'SSR':
                            refund_primos += 480
                            results.append(f"🔁 **{char['name']}** (SSR) ➔ Max 7 bản! Quy đổi **3 lượt** (+480 💎)")
                        elif rarity == 'SR':
                            refund_primos += 160
                            results.append(f"🔁 **{char['name']}** (SR) ➔ Max 7 bản! Quy đổi **1 lượt** (+160 💎)")
                        else:
                            results.append(f"🔁 {char['name']} (R) ➔ Max 7 bản! (Không tặng thêm 💎)")

                        pulled_cards.append({
                            "id": char_id,
                            "name": char['name'],
                            "rarity": rarity,
                            "game": game,
                            "image": char.get('image', ''),
                            "element": char.get('element') or char.get('path') or '',
                            "copies": copies,
                            "is_refund": True
                        })
                    else:
                        await db.execute('''
                            INSERT INTO gacha_inventory (user_id, character_id, game, copies)
                            VALUES ($1, $2, $3, 1)
                            ON CONFLICT(user_id, character_id) DO UPDATE SET copies = gacha_inventory.copies + 1
                        ''', user_id, char_id, game)

                        curr_copy = copies + 1
                        copy_str = f" [C{curr_copy-1}]" if curr_copy > 1 else " [Mới!]"

                        if rarity == 'L':
                            results.append(f"🔥 **{char['name']}** (LIMITED){copy_str} 💠💠💠💠💠💠")
                        elif rarity == 'SSR':
                            results.append(f"🌈 **{char['name']}** (SSR){copy_str} 🌟🌟🌟🌟🌟")
                        elif rarity == 'SR':
                            results.append(f"🟨 **{char['name']}** (SR){copy_str} 🌟🌟🌟🌟")
                        else:
                            results.append(f"⬜ {char['name']} (R){copy_str}")

                        pulled_cards.append({
                            "id": char_id,
                            "name": char['name'],
                            "rarity": rarity,
                            "game": game,
                            "image": char.get('image', ''),
                            "element": char.get('element') or char.get('path') or '',
                            "copies": curr_copy,
                            "is_refund": False
                        })

            net_cost = cost - refund_primos
            await db.execute('''
                UPDATE gacha_pity SET pity_4star=$1, pity_5star=$2, total_pulls=total_pulls+$3 WHERE user_id=$4
            ''', pity_4star, pity_5star, amount, user_id)

            await db.execute('UPDATE users SET primogems = primogems - $1 WHERE user_id = $2', net_cost, user_id)
            user_row = await db.fetchrow("SELECT primogems FROM users WHERE user_id = $1", user_id)
            remaining_primos = user_row['primogems'] if user_row else 0

        return {
            "success": True,
            "results": results,
            "pulled_cards": pulled_cards,
            "pity_4star": pity_4star,
            "pity_5star": pity_5star,
            "refund_primos": refund_primos,
            "remaining_primos": remaining_primos
        }

    @commands.command(name="gacha", aliases=["quay", "roll"])
    async def gacha(self, ctx, amount: int = 1):
        if amount not in [1, 10]:
            return await ctx.reply("❌ Cậu chỉ có thể gacha x1 hoặc x10 thôi nhé! (VD: `!gacha 1` hoặc `!gacha 10`)")

        user_id = str(ctx.author.id)
        res = await self.perform_pulls(user_id, amount)
        if not res["success"]:
            return await ctx.reply(f"❌ {res['msg']}")

        results = res["results"]
        pity_4star = res["pity_4star"]
        pity_5star = res["pity_5star"]
        refund_primos = res["refund_primos"]

        embed = discord.Embed(
            title=f"🌠 Cầu Nguyện x{amount} Đa Vũ Trụ",
            description="\n".join(results),
            color=0xF7BA2A if any("SSR" in r or "LIMITED" in r for r in results) else (0xB180FF if any("SR" in r for r in results) else 0x8ACBEB)
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Bảo hiểm: SR ({pity_4star}/10) • SSR ({pity_5star}/100)")

        if refund_primos > 0:
            embed.add_field(name="💎 Quy Đổi Hoàn Trả", value=f"Đã hoàn trả **{refund_primos:,} Nguyên Thạch** vào túi đồ!", inline=False)

        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(GachaCog(bot))
