# Tầm Nhìn Trọn Vẹn: Kamisato Ayaka Siêu Việt (Master Plan)

Hoàn toàn hợp lý! Nếu mục tiêu là tạo ra một Ayaka tuyệt vời và hoàn hảo nhất, chúng ta sẽ làm **tất cả 4 lựa chọn**. Tuy nhiên, để đảm bảo code không bị lỗi và hệ thống chạy mượt mà, chúng ta phải đi theo một **trình tự logic** (như việc xây nhà phải xây móng trước).

Dưới đây là trình tự thực hiện Master Plan:

1. **Giai đoạn 3: Xây dựng Cơ Sở Dữ Liệu (Database)** - *(Làm móng)*: Chuyển trí nhớ từ RAM sang Ổ cứng bằng SQLite.
2. **Giai đoạn 4: Hoàn thiện Tính năng Nhạc & Lời Bài Hát** - *(Xây nội thất)*: Thêm API lời bài hát và các hiệu ứng.
3. **Giai đoạn 5: Phát triển Web Dashboard** - *(Sơn sửa mặt tiền)*: Tạo trang web quản lý bot.
4. **Giai đoạn 6: Khởi Chạy Đám Mây (Cloud/VPS)** - *(Chuyển nhà)*: Đóng gói tất cả vào Docker và đưa lên VPS.

Chúng ta sẽ bắt đầu ngay với **Giai đoạn 3: Xây dựng Cơ Sở Dữ Liệu**.

---

## User Review Required

> [!IMPORTANT]
> Tớ đề xuất sử dụng **SQLite** kết hợp thư viện `aiosqlite` (Bất đồng bộ) cho Giai đoạn 3. 
> - **Lý do**: SQLite lưu dữ liệu dưới dạng 1 file duy nhất (vd: `ayaka_data.db`). Rất dễ dàng di chuyển, backup và khi đưa lên Cloud/VPS (Giai đoạn 6) thì không cần tốn tiền thuê thêm server Database bên ngoài.
> Cậu có đồng ý sử dụng SQLite không, hay muốn dùng MongoDB/MySQL?

## Proposed Changes (Giai Đoạn 3: Database)

### 1. Khởi tạo Database Layer
- Cài đặt thư viện: `pip install aiosqlite`
- Tạo file `database.py` để quản lý kết nối và tạo các bảng (Tables):
  - `users`: Lưu cấp độ (Level), EXP, và cài đặt cá nhân của người dùng.
  - `chat_history`: Lưu lại ngữ cảnh trò chuyện của AI thay cho RAM.
  - `guild_config`: Lưu cấu hình cho từng server (kênh được phép chat, prefix).

#### [NEW] [database.py](file:///e:/DuAnCaNhan/AIDiscordBuild/database.py)
Tạo class `Database` với các hàm async như `init_db()`, `get_user()`, `add_exp()`, `save_chat()`.

### 2. Tích hợp Database vào AI Brain
- Sửa đổi `ai_brain.py` để lấy lịch sử chat từ `database.py` thay vì dùng biến `chat_history = {}` trên RAM.
- Giúp Ayaka vẫn nhớ cậu đã nói gì kể cả khi bot bị khởi động lại.

#### [MODIFY] [ai_brain.py](file:///e:/DuAnCaNhan/AIDiscordBuild/ai_brain.py)

### 3. Tích hợp Hệ thống Level & Kinh nghiệm
- Tạo sự kiện trong `bot.py` hoặc một Cog mới (`level_cog.py`) để cộng EXP mỗi khi người dùng chat.
- Khi đủ EXP, Ayaka sẽ gửi tin nhắn chúc mừng lên cấp.

#### [NEW] [level_cog.py](file:///e:/DuAnCaNhan/AIDiscordBuild/level_cog.py)
#### [MODIFY] [bot.py](file:///e:/DuAnCaNhan/AIDiscordBuild/bot.py)
Tích hợp hàm kết nối Database vào sự kiện `on_ready`.

## Verification Plan

### Manual Verification
- Tắt và bật lại Bot, chat với Ayaka để kiểm tra xem trí nhớ có được giữ nguyên không.
- Kiểm tra file `ayaka_data.db` có tự động được sinh ra trong thư mục dự án không.
- Chat liên tục để kiểm tra xem bot có tính điểm EXP và thông báo lên cấp độ không.
