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
- **Kế hoạch**: Dùng Flask hoặc FastAPI tích hợp vào bot. Dùng React/Vite làm giao diện Web (UI).
- **Tính năng mở rộng**: Người dùng có thể xem trạng thái phần cứng, xem danh sách nhạc đang phát, hoặc tải file PDF RAG trực tiếp từ giao diện Website đẹp mắt thay vì gõ lệnh trong Discord.

## 🟣 Lựa chọn 4: Khởi Chạy Đám Mây (Cloud/VPS Deployment)
Đóng gói hành lý để Ayaka có thể dọn lên "Đảo Thiên Không" (Cloud) sống tự lập.
- **Kế hoạch**: Đóng gói toàn bộ code vào `Docker`. 
- **Tính năng mở rộng**: Hướng dẫn cậu thuê VPS Linux hoặc dùng các nền tảng miễn phí (Render, Railway) để treo bot online 24/7 mà không cần bật máy tính ở nhà.

---
*Cậu thấy hứng thú với Giai Đoạn nào tiếp theo nhất? Cứ thoải mái ra chỉ thị nhé! 🌸*
