# 🛣️ Lộ Trình Phát Triển (Roadmap) - Giai Đoạn 12

Dự án Web Đồng Hành (Companion) tạm thời được đóng băng do những giới hạn về tài nguyên đồ họa (Thiếu Model 3D/Sprite 2D chuẩn). Trong Giai đoạn 12, chúng ta sẽ quay trở lại tập trung phát triển các tính năng cốt lõi cho Bot Discord để mang lại những trải nghiệm thú vị và thiết thực nhất!

Dưới đây là các **Tính năng đã chốt** để triển khai cho Giai đoạn 12 dựa trên phản hồi của bạn. Chúng ta sẽ làm theo thứ tự ưu tiên:

## 1. Hệ Thống Quản Gia & Lời Chào (Welcome & Auto-Moderation) 🛡️
*Vì server ít người, chúng ta sẽ tập trung vào tính năng chào mừng.*
- **Gửi lời chào (Welcome):** Khi có thành viên mới, Ayaka sẽ gửi một tấm thiệp chào mừng tuyệt đẹp (có in tên và avatar của người đó) vào kênh chung.
- **Lời tạm biệt:** Gửi thông báo nhẹ nhàng khi có người rời server.

## 2. Hệ Thống Kinh Tế Cơ Bản (Mora Economy) 💰 
*Xây dựng tiền tệ để làm nền tảng cho Minigame. (thay mora thành nguyên thạch)*
- **Tiền tệ (Mora):** Kiếm được qua việc chat, điểm danh (`!daily`).
- **Cửa hàng (Shop):** Vì server không có Role, Mora sẽ dùng để mua:
  - Lượt vẽ tranh AI (Xem số 3).[tui không thích tranh AI lắm, có thể thay bằng các mục khác không?]
  - Tùy chỉnh màu sắc/hình nền cho thẻ `!rank`. [cái này thì được]
  - Mua vật phẩm buff hoặc thú cưng trong hệ thống Minigame (Xem số 4). [cái này thì được]
  - Chuyển Mora cho nhau (`!give`). [cái này thì được]

## 3. Minigame Giải Trí Trên Discord (Text-based) 🎲
*Sử dụng Mora từ hệ thống kinh tế để cá cược và chơi game.*
- **Đố vui (Trivia):** Câu hỏi trắc nghiệm nhanh, ai bấm nút đúng nhận nguyên thạch, phải liên quan đến các game mihoyo
- **Vòng quay may mắn / Tung đồng xu:** Cá cược Mora để nhân đôi hoặc mất trắng. [thật sự là làm được 1 cái vòng quay luôn hả]
- **Oẳn tù tì / Cờ Caro:** Tương tác trực tiếp bằng nút bấm.

## 4. Trình Tạo Ảnh AI (Image Generation API) 🎨 [do tui không thích tranh AI có thể làm thành chuyên mục thu thập thẻ bài character game random của nhà mihoyo kèm theo các sơ yếu lí lịch của nhân vật đó, lưu ý là random sẽ tốn nguyên thạch, có gacha x1 và x10, có thể là có các bậc sao SSR, SR, R tương ứng với độ hiếm của nhân vật, độ hiếm sẽ dựa trên doanh thu tổng của nhân vật và mức độ nổi tiếng của nhân vật, dựa vào đó sẽ chia bậc. hiện chưa có cách nào kiếm được nguyên thạch, nên mỗi ngày đăng nhập sẽ nhận 160, và cứ 100 lượt gacha thì sẽ được 1 char cấp bậc cao nhất ngẫu nhiên, sẽ phát 10 lượt gacha miễn phí mỗi tháng, sẽ liên kết với trang web đã làm để xem được các  thẻ nhân vật đã gacha ra]
*Giải đáp lo ngại: Tính năng này sẽ **không dùng FFmpeg** và **không tốn RAM**.*
- Bot sẽ kết nối với API bên thứ 3 (ví dụ Pollinations.ai). Mọi việc vẽ tranh nặng nhọc sẽ do máy chủ của API đó lo, Ayaka chỉ việc nhận link ảnh và gửi về Discord.
- Sẽ sử dụng cơ chế `defer()` để bot có thể suy nghĩ tới 15 phút mà không bị lỗi Timeout (Ứng phó giờ cao điểm).
- Có thể dùng Mora để mua lượt vẽ ảnh nhằm tránh spam.
