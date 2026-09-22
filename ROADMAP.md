# 🛣️ Lộ Trình Phát Triển (Roadmap) - Giai Đoạn 12

Dự án Web Đồng Hành (Companion) tạm thời được đóng băng do những giới hạn về tài nguyên đồ họa (Thiếu Model 3D/Sprite 2D chuẩn). Trong Giai đoạn 12, chúng ta sẽ quay trở lại tập trung phát triển các tính năng cốt lõi cho Bot Discord để mang lại những trải nghiệm thú vị và thiết thực nhất!

Dưới đây là các **Tính năng đã chốt** để triển khai cho Giai đoạn 12 dựa trên phản hồi của bạn. Chúng ta sẽ làm theo thứ tự ưu tiên:

## 1. Hệ Thống Quản Gia & Lời Chào (Welcome & Auto-Moderation) 🛡️
*Vì server ít người, chúng ta sẽ tập trung vào tính năng chào mừng.*
- **Gửi lời chào (Welcome):** Khi có thành viên mới, Ayaka sẽ gửi một tấm thiệp chào mừng tuyệt đẹp (có in tên và avatar của người đó) vào kênh chung.
- **Lời tạm biệt:** Gửi thông báo nhẹ nhàng khi có người rời server.

## 2. Hệ Thống Kinh Tế Cơ Bản (Mora Economy) 💰
*Xây dựng tiền tệ để làm nền tảng cho Minigame.*
- **Tiền tệ (Mora):** Kiếm được qua việc chat, điểm danh (`!daily`).
- **Cửa hàng (Shop):** Vì server không có Role, Mora sẽ dùng để mua:
  - Lượt vẽ tranh AI (Xem số 3).
  - Tùy chỉnh màu sắc/hình nền cho thẻ `!rank`.
  - Mua vật phẩm buff hoặc thú cưng trong hệ thống Minigame (Xem số 4).
  - Chuyển Mora cho nhau (`!give`).

## 3. Minigame Giải Trí Trên Discord (Text-based) 🎲
*Sử dụng Mora từ hệ thống kinh tế để cá cược và chơi game.*
- **Đố vui (Trivia):** Câu hỏi trắc nghiệm nhanh, ai bấm nút đúng nhận Mora.
- **Vòng quay may mắn / Tung đồng xu:** Cá cược Mora để nhân đôi hoặc mất trắng.
- **Oẳn tù tì / Cờ Caro:** Tương tác trực tiếp bằng nút bấm.

## 4. Trình Tạo Ảnh AI (Image Generation API) 🎨
*Giải đáp lo ngại: Tính năng này sẽ **không dùng FFmpeg** và **không tốn RAM**.*
- Bot sẽ kết nối với API bên thứ 3 (ví dụ Pollinations.ai). Mọi việc vẽ tranh nặng nhọc sẽ do máy chủ của API đó lo, Ayaka chỉ việc nhận link ảnh và gửi về Discord.
- Sẽ sử dụng cơ chế `defer()` để bot có thể suy nghĩ tới 15 phút mà không bị lỗi Timeout (Ứng phó giờ cao điểm).
- Có thể dùng Mora để mua lượt vẽ ảnh nhằm tránh spam.
