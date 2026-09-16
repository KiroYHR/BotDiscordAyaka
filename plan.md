# 📅 Chi Tiết Kế Hoạch - Giai Đoạn 7 (Web Dashboard Lập Lịch & Thời Tiết)

## 1. Mục tiêu
- Biến Web Dashboard thành trung tâm điều khiển thực thụ, người dùng có thể hẹn giờ Ayaka nhắn tin tự động (nhắc ngủ sớm, chúc buổi sáng, báo thời tiết) vào bất cứ khung giờ nào và bất cứ kênh nào.

## 2. Kiến trúc & Chỉnh sửa

### 2.1. Cơ sở dữ liệu (`database.py`)
- Cần tạo thêm một bảng `scheduled_tasks` trong PostgreSQL:
  - `task_id` (Primary Key)
  - `guild_id` (Server Discord)
  - `channel_id` (Kênh sẽ nhận tin nhắn)
  - `time_str` (Giờ thông báo - HH:MM)
  - `prompt_text` (Nội dung chỉ đạo cho AI)
  - `weather_location` (Tên thành phố, vd: "Hanoi")

### 2.2. Giao diện Web (`dashboard/index.html` & `app.js`)
- **Giao diện**: Thêm một Panel mới tên là "🕒 Lịch Trình Ayaka".
- **Biểu mẫu (Form)**:
  - Chọn Giờ (Timepicker).
  - Chọn Kênh (lấy danh sách kênh qua API).
  - Khung nhập nội dung (Prompt).
  - Khung nhập Địa điểm lấy Thời tiết (Không bắt buộc).
- **Logic**: Gửi lệnh (POST request) về Web Server nội bộ.

### 2.3. Server API (`web_dashboard.py`)
- Thêm Endpoint `/api/channels` để Web lấy danh sách kênh.
- Thêm Endpoint `/api/schedules` để Web Ghi/Đọc lịch trình từ Database.

### 2.4. Trí thông minh & Vòng lặp (`sys_cog.py`)
- Thay đổi `@tasks.loop(time=[...])` thành `@tasks.loop(minutes=1)`.
- Mỗi phút, vòng lặp ngầm sẽ:
  - Đọc giờ hiện tại.
  - Quét Database xem có lịch nào trùng giờ hiện tại không.
  - Nếu có: Lấy thông tin thời tiết (nếu có địa điểm) từ API `OpenWeatherMap`.
  - Nạp thông tin đó vào lời nhắc (Prompt) và gọi Gemini AI.
  - Gửi tin nhắn kết quả vào kênh được chỉ định.

## 3. Yêu cầu ngoại vi (External Requirements)
- Cần đăng ký một API Key miễn phí từ **OpenWeatherMap** (hoặc WeatherAPI) để có quyền truy cập dữ liệu thời tiết thực tế.
- Khóa này sẽ được nạp vào file `.env` hoặc cấu hình trên Render.
