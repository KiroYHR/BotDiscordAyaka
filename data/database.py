# pyrefly: ignore [missing-import]
import asyncpg
import json
import logging
import math
import os

logger = logging.getLogger("AyakaDatabase")

class AyakaDatabase:
    def __init__(self):
        # Lấy DATABASE_URL từ biến môi trường (Lấy từ Supabase/Neon)
        self.db_url = os.getenv("DATABASE_URL")
        self.pool = None

    async def init_db(self):
        """Khởi tạo database và các bảng nếu chưa có."""
        if not self.db_url:
            logger.warning("Không tìm thấy DATABASE_URL trong .env. Bot sẽ chạy với trí nhớ rỗng (RAM)!")
            return

        try:
            # Tạo Connection Pool cho PostgreSQL
            self.pool = await asyncpg.create_pool(self.db_url)
            
            async with self.pool.acquire() as db:
                # Bảng Users (Level, EXP) - dùng DOUBLE PRECISION thay cho REAL nếu cần, nhưng PostgreSQL hỗ trợ REAL.
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        exp INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1,
                        last_message_time REAL DEFAULT 0
                    )
                ''')
                
                # Bảng lưu phiên đăng nhập Web Dashboard
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS web_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        discord_data TEXT,
                        created_at REAL
                    )
                ''')
                
                # Cập nhật schema cho bảng users
                try:
                    await db.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS affection INTEGER DEFAULT 0')
                    await db.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0')
                    await db.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_daily_claim REAL DEFAULT 0')
                    await db.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_monthly_claim REAL DEFAULT 0')
                    await db.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS primogems INTEGER DEFAULT 0')
                    await db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS selected_character TEXT DEFAULT 'airi'")
                except Exception as e:
                    logger.warning(f"Lỗi khi Alter Table users (có thể đã tồn tại): {e}")
                
                # Bảng Gacha Pity
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS gacha_pity (
                        user_id TEXT PRIMARY KEY,
                        pity_4star INTEGER DEFAULT 0,
                        pity_5star INTEGER DEFAULT 0,
                        total_pulls INTEGER DEFAULT 0
                    )
                ''')
                
                # Bảng Gacha Inventory
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS gacha_inventory (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT,
                        character_id TEXT,
                        game TEXT,
                        copies INTEGER DEFAULT 1,
                        UNIQUE(user_id, character_id)
                    )
                ''')
                
                # Bảng Chat History (Trí nhớ AI)
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        channel_id TEXT PRIMARY KEY,
                        history_json TEXT
                    )
                ''')
                
                # Bảng Guild Config (Cấu hình máy chủ)
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS guild_config (
                        guild_id TEXT PRIMARY KEY,
                        prefix TEXT DEFAULT '!',
                        ai_channel_id TEXT
                    )
                ''')
                
                # Bảng Lịch Trình (Scheduled Tasks)
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS scheduled_tasks (
                        id SERIAL PRIMARY KEY,
                        guild_id TEXT NOT NULL,
                        channel_id TEXT NOT NULL,
                        time_str TEXT NOT NULL,
                        prompt TEXT NOT NULL,
                        weather_location TEXT
                    )
                ''')
            logger.info("Đã kết nối và khởi tạo Database PostgreSQL thành công!")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Database PostgreSQL: {e}")

    # --- Các hàm cho Chat History (AI Brain) ---
    async def save_chat_history(self, channel_id: str, history_list: list):
        """Lưu trữ lịch sử chat của một kênh vào DB (JSON)."""
        if not self.pool: return
        history_json = json.dumps(history_list, ensure_ascii=False)
        async with self.pool.acquire() as db:
            await db.execute('''
                INSERT INTO chat_history (channel_id, history_json)
                VALUES ($1, $2)
                ON CONFLICT(channel_id) DO UPDATE SET history_json=EXCLUDED.history_json
            ''', str(channel_id), history_json)

    async def get_chat_history(self, channel_id: str) -> list:
        """Lấy lịch sử chat của kênh từ DB."""
        if not self.pool: return []
        async with self.pool.acquire() as db:
            row = await db.fetchrow('SELECT history_json FROM chat_history WHERE channel_id = $1', str(channel_id))
            if row:
                try:
                    return json.loads(row['history_json'])
                except:
                    return []
            return []

    async def clear_chat_history(self, channel_id: str):
        """Xóa trí nhớ của bot trong kênh."""
        if not self.pool: return
        async with self.pool.acquire() as db:
            await db.execute('DELETE FROM chat_history WHERE channel_id = $1', str(channel_id))

    # --- Các hàm cho Hệ thống Level (EXP) ---
    async def add_exp(self, user_id: str, amount: int) -> dict:
        """Cộng EXP cho user. Trả về dict chứa thông tin level up nếu có."""
        user_id = str(user_id)
        if not self.pool: return {"leveled_up": False, "new_level": 1, "exp": 0}
        
        async with self.pool.acquire() as db:
            # Lấy thông tin hiện tại
            row = await db.fetchrow('SELECT exp, level FROM users WHERE user_id = $1', user_id)
            
            if row is None:
                exp = amount
                level = 1
                await db.execute('INSERT INTO users (user_id, exp, level) VALUES ($1, $2, $3)', user_id, exp, level)
            else:
                exp = row['exp'] + amount
                level = row['level']
                await db.execute('UPDATE users SET exp = $1 WHERE user_id = $2', exp, user_id)
            
            # Tính level mới: mỗi cấp cộng thêm 50 EXP (1->2: 100, 2->3: 150, ...)
            new_level = math.floor((-1 + math.sqrt(9 + 0.16 * exp)) / 2)
            leveled_up = False
            
            if new_level > level:
                await db.execute('UPDATE users SET level = $1 WHERE user_id = $2', new_level, user_id)
                leveled_up = True
                
            return {
                "leveled_up": leveled_up,
                "new_level": new_level,
                "exp": exp
            }

    async def get_user_stats(self, user_id: str):
        """Lấy thông tin cấp độ của user."""
        if not self.pool: return {"exp": 0, "level": 1}
        async with self.pool.acquire() as db:
            row = await db.fetchrow('SELECT exp, level FROM users WHERE user_id = $1', str(user_id))
            if row:
                return {"exp": row['exp'], "level": row['level']}
            return {"exp": 0, "level": 1}

    async def get_user_profile(self, user_id: str) -> dict:
        """Lấy toàn bộ profile user cho Web Dashboard."""
        user_id = str(user_id)
        if not self.pool: return None
        async with self.pool.acquire() as db:
            row = await db.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
            if row:
                return dict(row)
            return None

    async def claim_daily(self, user_id: str) -> dict:
        """Thực hiện điểm danh hàng ngày tăng Hảo cảm."""
        import time
        from datetime import datetime, timedelta
        import pytz
        
        user_id = str(user_id)
        if not self.pool: return {"success": False, "msg": "Không thể kết nối DB."}
        
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_vn = datetime.now(vn_tz)
        now_ts = now_vn.timestamp()
        
        # Tính thời điểm 3h sáng gần nhất
        reset_today = vn_tz.localize(datetime.combine(now_vn.date(), datetime.strptime("03:00", "%H:%M").time()))
        
        if now_vn < reset_today:
            last_reset = reset_today - timedelta(days=1)
        else:
            last_reset = reset_today
            
        last_reset_ts = last_reset.timestamp()
        previous_reset_ts = (last_reset - timedelta(days=1)).timestamp()
        
        async with self.pool.acquire() as db:
            row = await db.fetchrow('SELECT affection, streak, last_daily_claim, primogems FROM users WHERE user_id = $1', user_id)
            if not row:
                await db.execute('INSERT INTO users (user_id, affection, streak, last_daily_claim, primogems) VALUES ($1, $2, $3, $4, $5)', user_id, 10, 1, now_ts, 160)
                return {"success": True, "streak": 1, "affection": 10, "affection_gained": 10, "primos_gained": 160}
            
            last_claim = row['last_daily_claim'] or 0
            streak = row['streak'] or 0
            affection = row['affection'] or 0
            
            # Thời gian chờ: Đã điểm danh trong chu kỳ hiện tại (từ 3h sáng gần nhất tới nay)
            if last_claim >= last_reset_ts:
                next_reset = last_reset + timedelta(days=1)
                hours_left = int((next_reset.timestamp() - now_ts) / 3600) + 1
                return {"success": False, "msg": f"Cậu đã điểm danh hôm nay rồi! Hãy quay lại sau khoảng {hours_left} giờ nữa nhé (từ 03:00 sáng)."}
            
            # Mất chuỗi nếu claim cũ hơn chu kỳ hôm qua (tức là bỏ lỡ 1 ngày nguyên vẹn)
            if last_claim < previous_reset_ts:
                streak = 1
            else:
                streak += 1
                
            affection_gained = min(10 + (streak * 2), 50)
            affection += affection_gained
            primos_gained = 160
            
            await db.execute('''
                UPDATE users 
                SET affection = $1, streak = $2, last_daily_claim = $3, primogems = primogems + $4
                WHERE user_id = $5
            ''', affection, streak, now_ts, primos_gained, user_id)
            
            return {"success": True, "streak": streak, "affection": affection, "affection_gained": affection_gained, "primos_gained": primos_gained}

    async def claim_monthly(self, user_id: str) -> dict:
        import time
        from datetime import datetime, timedelta
        import pytz
        
        user_id = str(user_id)
        if not self.pool: return {"success": False, "msg": "Không thể kết nối DB."}
        
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_vn = datetime.now(vn_tz)
        now_ts = now_vn.timestamp()
        
        # Reset vào ngày 1 hàng tháng lúc 03:00 Sáng
        reset_this_month = vn_tz.localize(datetime(now_vn.year, now_vn.month, 1, 3, 0))
        
        if now_vn < reset_this_month:
            # Nếu hiện tại < 3h sáng ngày 1, thì reset của tháng này vẫn là mùng 1 tháng trước
            prev_month = now_vn.month - 1 if now_vn.month > 1 else 12
            prev_year = now_vn.year if now_vn.month > 1 else now_vn.year - 1
            last_reset = vn_tz.localize(datetime(prev_year, prev_month, 1, 3, 0))
        else:
            last_reset = reset_this_month
            
        last_reset_ts = last_reset.timestamp()
        
        async with self.pool.acquire() as db:
            row = await db.fetchrow('SELECT last_monthly_claim FROM users WHERE user_id = $1', user_id)
            
            # Khởi tạo user nếu chưa có
            if not row:
                await db.execute('INSERT INTO users (user_id, last_monthly_claim, primogems) VALUES ($1, $2, $3)', user_id, now_ts, 1600)
                return {"success": True, "primos_gained": 1600}
                
            last_claim = row['last_monthly_claim'] or 0
            if last_claim >= last_reset_ts:
                # Tính tháng tiếp theo
                next_month = last_reset.month + 1 if last_reset.month < 12 else 1
                next_year = last_reset.year if last_reset.month < 12 else last_reset.year + 1
                next_reset = vn_tz.localize(datetime(next_year, next_month, 1, 3, 0))
                days_left = (next_reset - now_vn).days
                return {"success": False, "msg": f"Cậu đã nhận quà tháng này rồi! Hãy quay lại sau khoảng {days_left} ngày nữa nhé."}
                
            await db.execute('UPDATE users SET last_monthly_claim = $1, primogems = primogems + $2 WHERE user_id = $3', now_ts, 1600, user_id)
            return {"success": True, "primos_gained": 1600}

    async def get_top_users(self, limit: int = 50) -> list:
        """Lấy danh sách người dùng top EXP."""
        if not self.pool: return []
        async with self.pool.acquire() as db:
            rows = await db.fetch('SELECT user_id, exp, level FROM users ORDER BY exp DESC LIMIT $1', limit)
            return [dict(row) for row in rows]

    # --- Các hàm cho Lịch Trình (Scheduled Tasks) ---
    async def add_schedule(self, guild_id: str, channel_id: str, time_str: str, prompt: str, weather_location: str = None) -> tuple[bool, str]:
        """Thêm một lịch trình mới vào DB."""
        if not self.pool: return False, "Database không được khởi tạo (pool is None)."
        try:
            async with self.pool.acquire() as db:
                await db.execute('''
                    INSERT INTO scheduled_tasks (guild_id, channel_id, time_str, prompt, weather_location)
                    VALUES ($1, $2, $3, $4, $5)
                ''', str(guild_id), str(channel_id), time_str, prompt, weather_location)
            return True, "Thành công"
        except Exception as e:
            logger.error(f"Lỗi khi thêm lịch trình: {e}")
            return False, str(e)

    async def get_schedules(self, guild_id: str = None) -> list:
        """Lấy danh sách lịch trình. Nếu truyền guild_id thì lấy theo server."""
        if not self.pool: return []
        async with self.pool.acquire() as db:
            if guild_id:
                rows = await db.fetch('SELECT * FROM scheduled_tasks WHERE guild_id = $1', str(guild_id))
            else:
                rows = await db.fetch('SELECT * FROM scheduled_tasks')
            return [dict(row) for row in rows]

    async def delete_schedule(self, schedule_id: int) -> bool:
        """Xóa một lịch trình theo ID."""
        if not self.pool: return False
        try:
            async with self.pool.acquire() as db:
                result = await db.execute('DELETE FROM scheduled_tasks WHERE id = $1', schedule_id)
                return result != "DELETE 0"
        except Exception as e:
            logger.error(f"Lỗi khi xóa lịch trình: {e}")
            return False

# Tạo một instance duy nhất (Singleton pattern) để dùng chung
    async def save_session(self, session_id, user_id, discord_data):
        """Lưu phiên bản web dashboard session."""
        if not self.pool:
            return
        try:
            discord_data_str = json.dumps(discord_data)
            async with self.pool.acquire() as db:
                await db.execute('''
                    INSERT INTO web_sessions (session_id, user_id, discord_data, created_at)
                    VALUES ($1, $2, $3, EXTRACT(EPOCH FROM NOW()))
                    ON CONFLICT (session_id) 
                    DO UPDATE SET user_id = EXCLUDED.user_id, discord_data = EXCLUDED.discord_data
                ''', session_id, user_id, discord_data_str)
        except Exception as e:
            logger.error(f"Lỗi save_session: {e}")

    async def get_session(self, session_id):
        """Lấy thông tin session."""
        if not self.pool:
            return None
        try:
            async with self.pool.acquire() as db:
                row = await db.fetchrow('SELECT user_id, discord_data FROM web_sessions WHERE session_id = $1', session_id)
                if row:
                    return {
                        "user_id": row["user_id"],
                        "discord_data": json.loads(row["discord_data"])
                    }
        except Exception as e:
            logger.error(f"Lỗi get_session: {e}")
        return None

db_manager = AyakaDatabase()
