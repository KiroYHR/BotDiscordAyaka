import aiosqlite
import json
import logging

logger = logging.getLogger("AyakaDatabase")
DB_PATH = "ayaka_data.db"

class AyakaDatabase:
    def __init__(self):
        self.db_path = DB_PATH

    async def init_db(self):
        """Khởi tạo database và các bảng nếu chưa có."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Bảng Users (Level, EXP)
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
                await db.commit()
            logger.info("Đã kết nối và khởi tạo Database thành công!")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Database: {e}")

    # --- Các hàm cho Chat History (AI Brain) ---
    async def save_chat_history(self, channel_id: str, history_list: list):
        """Lưu trữ lịch sử chat của một kênh vào DB (JSON)."""
        history_json = json.dumps(history_list, ensure_ascii=False)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO chat_history (channel_id, history_json)
                VALUES (?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET history_json=excluded.history_json
            ''', (str(channel_id), history_json))
            await db.commit()

    async def get_chat_history(self, channel_id: str) -> list:
        """Lấy lịch sử chat của kênh từ DB."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT history_json FROM chat_history WHERE channel_id = ?', (str(channel_id),)) as cursor:
                row = await cursor.fetchone()
                if row:
                    try:
                        return json.loads(row[0])
                    except:
                        return []
                return []

    async def clear_chat_history(self, channel_id: str):
        """Xóa trí nhớ của bot trong kênh."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM chat_history WHERE channel_id = ?', (str(channel_id),))
            await db.commit()

    # --- Các hàm cho Hệ thống Level (EXP) ---
    async def add_exp(self, user_id: str, amount: int) -> dict:
        """Cộng EXP cho user. Trả về dict chứa thông tin level up nếu có."""
        user_id = str(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            # Lấy thông tin hiện tại
            async with db.execute('SELECT exp, level FROM users WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                
            if row is None:
                exp = amount
                level = 1
                await db.execute('INSERT INTO users (user_id, exp, level) VALUES (?, ?, ?)', (user_id, exp, level))
            else:
                exp = row[0] + amount
                level = row[1]
                await db.execute('UPDATE users SET exp = ? WHERE user_id = ?', (exp, user_id))
            
            # Tính level mới (công thức đơn giản: level = (exp // 100) + 1)
            # Bạn có thể đổi công thức sau
            new_level = (exp // 100) + 1
            leveled_up = False
            
            if new_level > level:
                await db.execute('UPDATE users SET level = ? WHERE user_id = ?', (new_level, user_id))
                leveled_up = True
                
            await db.commit()
            
            return {
                "leveled_up": leveled_up,
                "new_level": new_level,
                "exp": exp
            }

    async def get_user_stats(self, user_id: str):
        """Lấy thông tin cấp độ của user."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT exp, level FROM users WHERE user_id = ?', (str(user_id),)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"exp": row[0], "level": row[1]}
                return {"exp": 0, "level": 1}

# Tạo một instance duy nhất (Singleton pattern) để dùng chung
db_manager = AyakaDatabase()
