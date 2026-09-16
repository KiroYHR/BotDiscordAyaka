import asyncpg
import json
import logging
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
            
            # Tính level mới (công thức đơn giản: level = (exp // 100) + 1)
            new_level = (exp // 100) + 1
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
db_manager = AyakaDatabase()
