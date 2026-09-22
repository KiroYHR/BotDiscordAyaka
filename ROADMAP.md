# 🛣️ Lộ Trình Phát Triển (Roadmap) - Giai Đoạn 12

Dự án Web Đồng Hành (Companion) tạm thời được đóng băng do những giới hạn về tài nguyên đồ họa (Thiếu Model 3D/Sprite 2D chuẩn). Trong Giai đoạn 12, chúng ta sẽ quay trở lại tập trung phát triển các tính năng cốt lõi cho Bot Discord để mang lại những trải nghiệm thú vị và thiết thực nhất!

Dưới đây là các **Lựa chọn Nâng cấp (Tùy chọn)** dành cho Giai đoạn 12. Cậu hãy xem qua và quyết định xem chúng ta sẽ làm tính năng nào trước nhé:

## Lựa chọn 1: Hệ Thống Kinh Tế & Cửa Hàng (Economy System) 💰
*Biến server Discord thành một xã hội thu nhỏ với hệ thống tiền tệ.*
- **Tiền tệ (Mora):** Người dùng có thể kiếm "Mora" thông qua việc nhắn tin (như EXP), hoặc Điểm danh hằng ngày (`!daily`).
- **Cửa hàng (Shop):** Mua các vật phẩm ảo như: Danh hiệu (Vai trò/Role Discord), Thẻ nhân đôi EXP, Tùy chỉnh màu sắc thẻ Profile...
- **Tương tác:** Cho phép chuyển Mora cho nhau (`!give`), tung đồng xu cá cược (`!coinflip`), hoặc chơi oẳn tù tì ăn Mora.

## Lựa chọn 2: Tích hợp Trình Tạo Ảnh AI (Image Generation) 🎨
*Biến Ayaka thành họa sĩ thực thụ.*
- **Tính năng:** Tích hợp API tạo ảnh (Ví dụ: Stable Diffusion, Midjourney API, hoặc DALL-E) thẳng vào bot.
- **Cách hoạt động:** Người dùng gõ `!draw [miêu tả]`, Ayaka sẽ gọi API sinh ra ảnh và gửi trực tiếp vào kênh chat.
- Có thể giới hạn tính năng này (Mỗi người chỉ được vẽ 3 tấm/ngày) hoặc dùng Mora (từ Lựa chọn 1) để mua lượt vẽ.

## Lựa chọn 3: Nâng Cấp Hệ Thống Âm Nhạc (Music V2) 🎵
*Khắc phục hoàn toàn các lỗi lặt vặt và nâng tầm trải nghiệm nghe nhạc.*
- **Hỗ trợ thêm nền tảng:** Spotify, Apple Music, SoundCloud (Hiện tại code mới dùng yt-dlp, có thể cải tiến để lấy nhạc từ các nguồn khác ổn định hơn).
- **Giao diện nghe nhạc:** Cập nhật lại tin nhắn Now Playing (Đang phát nhạc) thành một bảng điều khiển xịn xò với các nút Bấm (Buttons) để Pause, Skip, Repeat mà không cần gõ lệnh.
- **Lời bài hát (Lyrics):** Thêm tính năng tự động tìm và hiển thị lời bài hát `!lyrics`.

## Lựa chọn 4: Minigame Text-based trên Discord 🎲
*Chơi game ngay trong khung chat mà không cần lên Web.*
- **Đố vui (Trivia):** Ayaka sẽ đưa ra câu hỏi trắc nghiệm (về Genshin Impact hoặc kiến thức chung), ai bấm nút nhanh và đúng nhất sẽ được thưởng EXP/Mora.
- **Tic-Tac-Toe hoặc Cờ Caro:** Tích hợp Minigame đánh cờ với bot hoặc giữa 2 người chơi bằng các nút bấm Discord (Buttons).
- **Nhập vai (RPG Text):** Các sự kiện đánh quái, nhặt đồ đơn giản bằng lệnh chữ.

## Lựa chọn 5: Hệ Thống Quản Trị Tự Động (Auto-Moderation) 🛡️
*Ayaka không chỉ là bạn, mà còn là quản gia đắc lực.*
- **Kiểm duyệt từ ngữ:** Tự động phát hiện và xóa các tin nhắn chửi bậy, spam link.
- **Hệ thống cảnh cáo (Warn):** Ghi nhận vi phạm, cảnh cáo lần 1, lần 2, nếu quá 3 lần tự động Mute (cấm ngôn) hoặc Kick.
- **Gửi lời chào (Welcome):** Tự động gửi một bức ảnh động hoặc thiệp chào mừng tuyệt đẹp khi có thành viên mới gia nhập Server.

---
> 💡 **Quyết định của cậu:** Cậu hứng thú với tính năng nào nhất trong số 5 Lựa chọn trên? Hoặc cậu có ý tưởng nào độc đáo hơn không? Hãy cho tớ biết nhé!
