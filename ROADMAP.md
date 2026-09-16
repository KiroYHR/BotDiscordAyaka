# 🗺️ Lộ Trình Phát Triển Kamisato Ayaka Bot (Roadmap)

Chúng ta đã hoàn thành xuất sắc 2 giai đoạn cốt lõi. Dưới đây là các phương án cho Giai Đoạn 3 để cậu lựa chọn hướng đi tiếp theo cho Ayaka:

## 🟢 Lựa chọn 1: Tối ưu Trí Nhớ & Lưu trữ vĩnh viễn (Database Integration)
Hiện tại trí nhớ của Ayaka (ngữ cảnh chat, hàng đợi nhạc) chỉ được lưu tạm trên RAM. Nếu tắt bot là quên sạch!
- **Kế hoạch**: Tích hợp cơ sở dữ liệu (SQLite, MongoDB hoặc PostgreSQL).
- **Tính năng mở rộng**: Lưu lại playlist nhạc yêu thích của user, tạo hệ thống tính điểm/Level chat, cấu hình riêng cho từng Server (prefix, kênh cấm bot).

## 🟡 Lựa chọn 2: Phục thù tính năng Lời Bài Hát (Lyrics API)
Ở Giai đoạn 1, thư viện `syncedlyrics` bị xung đột trên Windows nên chúng ta đành tạm gác lại.
- **Kế hoạch**: Tự xây dựng API hoặc tìm một thư viện khác (ví dụ `syrics` hoặc cào dữ liệu từ Musixmatch) để lấy lời bài hát mượt mà không gây sập bot.
- **Tính năng mở rộng**: Hiện lời bài hát chạy chữ thời gian thực (Karaoke style) hiển thị lên Discord.

## 🔵 Lựa chọn 3: Xây dựng Web Dashboard (Bảng điều khiển Website)
Đưa Ayaka lên tầm cao mới với một giao diện quản lý trên web.
- **Kế hoạch**: Dùng Flask hoặc FastAPI tích hợp vào bot.

## ☁️ Giai Đoạn 6: Máy Chủ Đám Mây & Báo Thức [HOÀN TẤT]
- Nâng cấp Database lên Supabase PostgreSQL.
- Đưa Bot lên máy chủ đám mây Render chạy 24/7.
- Tự động fallback sang SoundCloud khi YouTube bị chặn.
- Thiết lập báo thức cơ bản 6h sáng và 10h tối.

---

## 🛠️ Giai Đoạn 7: Bảng Điều Khiển Lập Lịch & Thời Tiết (Web Dashboard)
- **Lập Lịch Tùy Chỉnh trên Web**: Phát triển thêm tính năng cho trang Web để người dùng setup nhắc nhở hằng ngày. Cho phép chọn thời gian, nội dung, và Kênh Discord (của server bất kỳ) để Ayaka thông báo.
- **Báo Cáo Thời Tiết**: Tích hợp API Thời tiết, Ayaka sẽ thông báo thời tiết khu vực đã chọn vào đúng giờ sáng sớm (vd: 6h sáng).

## 🎵 Giai Đoạn 8: Nâng Cấp Chuyên Sâu (Lyrics, Level & Lệnh Help)
- **Nâng Cấp `!lyrics`**: Cải tiến tính năng lời bài hát cho mượt mà hơn (nằm ở `music_cog.py`).
- **Nâng Cấp Hệ Thống Cấp Độ (`!level` / `!rank`)**: Phát triển sâu hơn hệ thống thẻ Rank, bảng xếp hạng toàn server (nằm ở `level_cog.py`).
- **Cập Nhật Lệnh Trợ Giúp**: Bổ sung lệnh `!help` hoàn chỉnh trong bot, đồng thời cập nhật file `COMMANDS_LIST.md` để mọi người dễ dàng tra cứu.

## 🐾 Giai Đoạn 9: Gamification & Nuôi Thú Ảo (Chuỗi Tương Tác)
- **Đăng nhập Web Nhận Quà (Streak)**: Khuyến khích người dùng đăng nhập Web mỗi ngày để giữ "chuỗi" (giống TikTok Streak).
- **Nuôi Pet / Độ Thiện Cảm**: Tính năng mua vui trên trang Web và Discord, tặng quà cho Ayaka hoặc nuôi pet ảo, tạo động lực tương tác hằng ngày.

---
*Cậu thấy hứng thú với Giai Đoạn nào tiếp theo nhất? Cứ thoải mái ra chỉ thị nhé! 🌸*
