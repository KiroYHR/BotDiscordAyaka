# 📅 Chi Tiết Kế Hoạch - Giai Đoạn 8 (Interactive Music Player phong cách Lunabot)

## 1. Mục tiêu
- Nâng cấp hoàn toàn trải nghiệm nghe nhạc của Ayaka bằng cách thay thế các tin nhắn văn bản khô khan bằng một **Giao diện Trình phát nhạc (Player Embed)** sống động, bền bỉ và có tính tương tác cao (giống Lunabot).
- Cung cấp các nút bấm (Buttons) và menu thả xuống (Select Menu) để điều khiển nhạc trực tiếp mà không cần gõ lệnh.

## 2. Kiến trúc & Chỉnh sửa

### 2.1. Cấu trúc Trình Phát (Player Embed & UI View)
- Chỉnh sửa `music_cog.py` để sử dụng `discord.ui.View`.
- **Hệ thống Nút Bấm (Buttons)** chia làm 3 hàng:
  - Hàng 1: ⏯️ (Play/Pause), ⏭️ (Skip), ⏹️ (Stop/Leave), 🔀 (Shuffle), 🔁 (Loop/Repeat).
  - Hàng 2: 🔉 (Giảm âm lượng), 🔊 (Tăng âm lượng), ❤️ (Yêu thích/Lưu bài hát).
  - Hàng 3: 📜 (Xem Lời Bài Hát).
- **Menu Gợi Ý (Select Menu)**:
  - Một dropdown list hiển thị 5-10 bài hát gợi ý (dựa trên bài đang phát) để người dùng chọn và tự động thêm vào hàng đợi.

### 2.2. Trình Quản Lý Hàng Đợi (Queue & State Management)
- **Hiển thị Hàng Đợi (Queue Display)**:
  - Embed sẽ luôn hiển thị bài hát đang phát ở trên cùng (kèm Thumbnail, thời lượng, người yêu cầu).
  - Phần thân Embed liệt kê danh sách tối đa 10 bài hát tiếp theo (`Up Next`).
- **Tin nhắn Bền Bỉ (Persistent Message)**:
  - Mỗi khi bài hát chuyển sang bài mới, thay vì gửi một tin nhắn mới làm trôi chat, Ayaka sẽ **chỉnh sửa (edit)** chính tin nhắn Player đó để cập nhật trạng thái bài hát.
  - Lưu trữ `player_message_id` cho từng server. Nếu tin nhắn bị trôi quá xa, bot sẽ xóa tin nhắn cũ và gửi Player mới xuống dưới cùng.

### 2.3. Cải tiến Kỹ Thuật Lõi
- **Điều khiển Âm lượng**: Để các nút tăng/giảm âm lượng hoạt động, cần bọc `discord.FFmpegPCMAudio` vào trong `discord.PCMVolumeTransformer`.
- **Chế độ Lặp (Loop Mode)**: Thêm biến trạng thái `loop_mode` (Off, Single, Queue) vào logic của `play_next()`.
- **Trích xuất Dữ liệu Mở rộng**: Cấu hình `yt_dlp` lấy thêm `duration` (thời lượng) và `thumbnail` (ảnh bìa) để làm đẹp Embed.

## 3. Câu Hỏi Mở (Cần Cậu Quyết Định)

> [!WARNING]
> **Về tính năng Âm Lượng (Volume):** Việc cho phép điều chỉnh âm lượng bằng `PCMVolumeTransformer` có thể tốn thêm một chút CPU trên máy chủ Render. Cậu có chắc chắn muốn bật tính năng này không? (Gợi ý: Render vẫn có thể gánh được).

> [!IMPORTANT]
> **Về Menu Gợi Ý:** Cậu muốn Menu thả xuống này hiển thị các bài hát liên quan (YouTube Related) hay hiển thị Lịch sử các bài hát cậu vừa nghe? (Gợi ý: YouTube Related sẽ mang lại trải nghiệm giống Lunabot nhất).

## 4. Kế hoạch Kiểm thử
- Test nhấn nút nhiều lần (Spam buttons) xem API Discord có bị giới hạn (Rate limit) không.
- Chạy thử việc chuyển bài liên tục và kiểm tra xem Embed có được cập nhật mượt mà không.
