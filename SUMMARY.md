# 🌸 Báo Cáo Tổng Kết Dự Án: Kamisato Ayaka Bot

Đây là tài liệu tóm tắt chi tiết toàn bộ các tính năng và hệ thống mà chúng ta đã dày công xây dựng từ những viên gạch đầu tiên cho đến nay (Hoàn tất Giai đoạn 4).

---

## 🟢 Giai Đoạn 1: Nền Tảng Cốt Lõi (Core Features)
*Xây dựng hình hài và những kỹ năng cơ bản nhất cho Ayaka.*

- **Cấu trúc Module hóa (Cogs Architecture)**: Phân chia code thành các tệp riêng biệt để dễ quản lý (`music_cog`, `sys_cog`, `game_cog`, `image_cog`).
- **Trí tuệ nhân tạo (AI Chat)**: 
  - Tích hợp **Google Gemini Flash**.
  - Truyền prompt hệ thống để bot nhập vai hoàn hảo vào nhân vật Kamisato Ayaka (Genshin Impact).
- **Trình Phát Nhạc (Music Player)**: 
  - Sử dụng `yt-dlp` và `FFmpeg` để phát nhạc từ YouTube.
  - Các lệnh quản lý nhạc cơ bản: `!play`, `!skip`, `!stop`, `!pause`, `!resume`, `!join`.
- **Đa dụng (Utilities)**:
  - **Giám sát hệ thống**: Lệnh `!sysinfo` kiểm tra CPU, RAM máy chủ.
  - **Tra cứu Game (HoyoLab API)**: Các lệnh `!gs`, `!hsr`, `!zzz` để tra cứu thông tin thẻ người chơi.
  - **Xử lý hình ảnh AI**: Lệnh `!rmbg` (tách nền), `!filter` (áp dụng bộ lọc màu).

---

## 🟡 Giai Đoạn 2: AI Nâng Cao & RAG (Retrieval-Augmented Generation)
*Nâng cấp trí não, giúp Ayaka có thể đọc hiểu tài liệu phức tạp.*

- **Cập nhật SDK**: Tiên phong nâng cấp toàn bộ mã nguồn AI sang thư viện `google-genai` mới nhất của Google.
- **RAG - Đọc hiểu PDF (`rag_cog.py`)**: 
  - Tích hợp tính năng `!askpdf`.
  - Ayaka có thể đọc các tệp PDF do người dùng tải lên và trả lời các câu hỏi chuyên sâu dựa trên nội dung tệp.
- **Tóm Tắt Khung Chat (`!summary`)**: 
  - Khả năng đọc hàng trăm tin nhắn cũ trong kênh và tóm tắt lại với giọng điệu hài hước, dễ thương của một "bản tin thời sự".

---

## 🔵 Giai Đoạn 3: Tối Ưu Hóa & Trí Nhớ Vĩnh Cửu (Database & Gamification)
*Thay thế bộ nhớ tạm thời bằng cơ sở dữ liệu thực thụ và tăng tính tương tác.*

- **Tích hợp SQLite (`database.py`)**: 
  - Chuyển toàn bộ ngữ cảnh trò chuyện (Context) từ bộ nhớ RAM sang file cơ sở dữ liệu `ayaka_data.db`.
  - Đảm bảo Ayaka không bao giờ quên những gì cậu nói, kể cả khi bot bị khởi động lại hay mất điện.
- **Hệ Thống Cấp Độ (EXP & Leveling)**: 
  - Viết mới `level_cog.py`.
  - Người dùng nhắn tin sẽ tự động được cộng Kinh Nghiệm (EXP) và lên cấp.
  - Cung cấp lệnh `!rank` kèm theo thẻ hiển thị Cấp độ, tiến trình phần trăm dạng thanh (Progress Bar) siêu trực quan.

---

## 🟣 Giai Đoạn 4: Trải Nghiệm Hoàn Hảo (Lyrics & Anti-Crash)
*Giải quyết những vấn đề khó chịu nhất và hoàn thiện tính năng giải trí.*

- **Khiên Chống Quá Tải (Auto-Retry)**: 
  - Khắc phục triệt để lỗi `503 Service Unavailable` từ Google API.
  - Xây dựng vòng lặp ngầm tự động thử kết nối lại tối đa 3 lần với khoảng cách 2 giây. Người dùng sẽ không còn thấy tin nhắn báo lỗi khó chịu mà chỉ thấy bot gõ phím lâu hơn bình thường.
- **Đồng Bộ Lời Bài Hát (`!lyrics`)**: 
  - Tích hợp thành công Web API **LRCLIB** mã nguồn mở.
  - Gõ lệnh `!lyrics` để Ayaka tự động tìm kiếm tên bài hát đang phát và in lời bài hát trực tiếp lên Discord (không gây lỗi trên Windows như thư viện cũ).

---

## 🌐 Giai Đoạn 5: Web Dashboard (Giao Diện Quản Lý)
*Cửa sổ tâm hồn và trung tâm điều khiển của hệ thống.*

- **Xây dựng Web Server (`web_dashboard.py`)**: 
  - Khởi tạo hệ thống máy chủ nội bộ siêu tốc bằng thư viện bất đồng bộ `aiohttp` chạy ngầm (Port 928) song song cùng với bot Discord.
- **Giao Diện Độc Quyền (UI/UX)**: 
  - Thiết kế trang quản lý độc quyền mang phong cách của Tiểu Thư Kamisato (Màu Xanh Lục Lam dịu nhẹ, Background kính Glassmorphism, Chữ ký "Ayaka" bay bổng).
  - Áp dụng các kỹ thuật thiết kế bậc cao như Linear-gradient mask-image, Mix-blend-mode (Multiply) để khử viền sắc cạnh và hòa trộn model Ayaka hoàn hảo vào Background như một nghệ thuật.
- **Hiệu Ứng Bất Tận & Tâm Trạng (`app.js`)**: 
  - Giao diện tràn đầy "sức sống" nhờ hiệu ứng tuyết rơi (`❄️`) và hoa anh đào lả lướt (`🌸`) rơi tự do (được tạo ngẫu nhiên hoàn toàn bằng Javascript).
  - Tích hợp khu vực "Tâm trạng ngẫu nhiên": Cứ mỗi 10 giây, Ayaka sẽ đổi trạng thái cảm xúc (dùng kho Emoji độc quyền do người dùng cung cấp) kèm theo câu thoại tâm trạng cực kỳ dễ thương.
- **Giám Sát Tức Thời (Real-time Polling)**:
  - Tự động gọi API ngầm (`/api/status` và `/api/music`) mỗi 3 giây để lấy Độ trễ (Ping), số lượng User, số Server, và danh sách các bài nhạc Ayaka đang phát, cập nhật động lên Web mà không hề gây chớp giật trang.

---

## ☁️ Giai Đoạn 6: Đưa Ayaka Lên Đám Mây (Cloud Deployment) & Báo Thức
*Biến Ayaka thành một thực thể sống 24/7 độc lập hoàn toàn khỏi máy tính cá nhân.*

- **Cơ sở dữ liệu đám mây (Supabase PostgreSQL)**:
  - Nâng cấp từ SQLite cục bộ lên PostgreSQL trên Supabase.
  - Chỉnh sửa hệ thống Level (`level_cog`) và Ký ức (`ai_brain`) để lưu trữ dữ liệu an toàn, không bị mất khi Render khởi động lại.
- **Triển khai máy chủ Render (Web Service)**:
  - Chạy bot qua Docker trên nền tảng đám mây Render.
  - Sử dụng chiến thuật **UptimeRobot** "gõ cửa" Web Dashboard mỗi 5 phút để giữ cho bot không bao giờ bị tắt ngấm (Sleep state).
- **Sửa Lỗi Tương Thích & Bypass YouTube**:
  - Viết cơ chế Fallback: Tự động chuyển từ tìm nhạc trên YouTube sang **SoundCloud** khi gặp lỗi bị chặn IP máy chủ đám mây (403 Forbidden).
  - Khắc phục lỗi thiếu dữ liệu `ZoneInfo` trên môi trường Linux siêu nhẹ và thiết lập hệ thống định vị thời gian chuẩn xác bằng UTC+7.
- **Trợ lý Báo Thức (Scheduled Tasks)**:
  - Khởi tạo chức năng hẹn giờ `daily_greeting`. 
  - Đúng 6h sáng và 10h tối mỗi ngày, Ayaka sẽ tự sử dụng bộ não AI (Gemini) để viết một thông điệp dễ thương vào kênh `bản-tin-hiệp-hội-yashiro`.

---

## 📅 Giai Đoạn 7: Lập Trình Lịch Trình Qua Web (Web Scheduling & Resilience)
*Giao quyền quản lý thời gian và báo thức trực tiếp cho người dùng thông qua giao diện Web.*

- **Quản lý Lịch Trình Tùy Chỉnh**:
  - Xây dựng API và giao diện Web cho phép người dùng thêm/xóa lịch nhắc nhở tùy chỉnh (chọn máy chủ, kênh, giờ phút, lời nhắc, báo thời tiết).
  - Áp dụng kỹ thuật Glassmorphism Modal UI do tự thiết kế để thay thế hoàn toàn cảnh báo `alert` thô cứng của trình duyệt.
- **Tách biệt kịch bản thông minh**:
  - **Báo thức 6h sáng**: Cố định báo thức tổng hợp thời tiết 3 miền (Bắc-Trung-Nam) mỗi 6h sáng vào kênh bản tin.
  - **Nhắc nhở cá nhân**: Kích hoạt chính xác tới từng phút theo yêu cầu của người dùng, lược bỏ văn phong cố định ngày giờ để tập trung vào lời nhắc.
- **Độ tin cậy tuyệt đối (Resilience)**:
  - Bổ sung hệ thống **Tin nhắn dự phòng (Fallback)**: Đảm bảo báo thức luôn kêu đúng giờ bằng tin nhắn cơ bản kể cả khi Google AI bị sập hoàn toàn.
  - Bọc bảo vệ vòng lặp vô tận (Try-Catch Loop): Ngăn chặn nguy cơ vòng lặp đếm thời gian bị crash do mất kết nối Database.
  - Triển khai thuật toán **Exponential Backoff** cho `ai_brain` để lách qua giới hạn chặn băng thông (503/429) của máy chủ Google.

---

## 🎮 Giai Đoạn 8: Nâng Cấp Tương Tác & Hệ Thống Xếp Hạng (Gamification & UI)
*Biến bot thành một nhân vật có chiều sâu thông qua hệ thống thăng cấp và giao diện menu tiện lợi.*

- **Hệ thống Cấp Độ (Gamification)**:
  - Tích hợp cơ chế điểm kinh nghiệm (EXP) chống spam: Mỗi phút nhận 5 EXP cố định cho các tin nhắn thường.
  - Thuật toán lên cấp độ khó tăng dần: Mỗi cấp độ tiếp theo yêu cầu thêm 50 EXP (ví dụ: Lv1->2 cần 100, Lv2->3 cần 150, Lv3->4 cần 200).
  - Tích hợp Bảng Phong Thần trực tiếp vào **Web Dashboard** sử dụng SPA (Single Page Application) và thiết kế Glassmorphism để đồng bộ giao diện.
- **Menu Lựa Chọn Tương Tác (Dropdown UI)**:
  - Cải tiến lệnh `!help` thô sơ thành một Menu Dropdown tương tác hiện đại bằng `discord.ui.Select`.
- **Gợi Ý Âm Nhạc Bằng SoundCloud**:
  - Viết lại module Music để khắc phục triệt để lỗi giới hạn (Rate Limit) của YouTube. Sử dụng **SoundCloud** làm nền tảng tìm kiếm dự phòng và gợi ý bài hát tương tự.
  - Tích hợp danh sách "Bài Hát Tương Tự" (AutoPlay) trực tiếp vào Menu Dropdown giúp người dùng thêm nhanh 5 bài hát gợi ý.

---

## 🛠️ Giai Đoạn 9: Bảo Trì & Ổn Định Trí Nhớ Đám Mây
*Đảm bảo hệ thống vận hành hoàn hảo không gặp lỗi (Bugs) khi chuyển dịch môi trường.*

- **Sửa Lỗi Đồng Bộ Phiên Đăng Nhập (Sessions)**:
  - Khắc phục lỗi Cookie phiên đăng nhập của người dùng bị xóa sau mỗi lần Render khởi động lại bằng cách chuyển dữ liệu `SESSIONS` từ RAM sang bảng `web_sessions` trong PostgreSQL.
- **Quy Hoạch Cấu Trúc Mã Nguồn (Refactor)**:
  - Tách bạch cấu trúc bot thành các thư mục chuẩn mực: `core/`, `cogs/`, `web/`, và `data/` giúp dễ dàng quản lý hệ thống mã nguồn ngày càng khổng lồ.

---

## 🌸 Giai Đoạn 10: Trợ Lý Ảo Trên Web (Live2D/3D Web Companion) (Tạm Dừng)
*Mang Ayaka bước ra khỏi những dòng tin nhắn khô khan.*

- **Thiết Kế Không Gian Đồng Hành**:
  - Bổ sung Tab "Đồng Hành" vào giao diện Web với khả năng tải trực tiếp các mô hình tương tác (Live2D/3D).
  - Tích hợp tính năng Điểm Danh hằng ngày và thanh đo Độ Hảo Cảm với chuỗi tương tác (Streak).
- **Tạm Dừng**: Mặc dù đã thử nghiệm tích hợp PixiJS (Live2D) và ThreeJS (3D), nhưng do các vấn đề về CORS, hiệu năng và thiếu mô hình (model) phù hợp, tính năng này hiện tại chưa hoạt động ổn định và được gộp chung vào quyết định tạm dừng cùng với Giai đoạn 11. Tab "Đồng Hành" đã được ẩn đi.

---

## 🎭 Giai Đoạn 11: Trợ Lý Ảo Trên Web & Minigame Pixel Art (Tạm Dừng)
*Khát vọng mang Ayaka bước ra khỏi những dòng tin nhắn khô khan.*

- **Khởi Khảo**: Ban đầu, chúng ta đã tiến hành thử nghiệm đưa các mô hình Live2D/3D (ThreeJS) và sau đó là tạo một Minigame RPG Pixel Art 2D (Sử dụng Tiled Map) lên giao diện Web Dashboard để người dùng có thể tương tác trực tiếp với Ayaka.
- **Tạm Dừng**: Do những khó khăn khách quan về việc thiết kế đồ họa (không có sẵn Model bản quyền, khó khăn trong việc tạo Sprite Sheet di chuyển 4 hướng đồng nhất bằng AI/phần mềm), toàn bộ dự án "Đồng Hành" (Companion) tạm thời được đóng băng và cất vào kho. 
- **Quyết Định**: Tab "Đồng Hành" trên Website đã được ẩn đi. Chúng ta sẽ quay trở lại với nó trong tương lai khi có đủ tài nguyên đồ họa. Hiện tại, Bot sẽ tập trung phát triển các tính năng tương tác thực tế và thú vị khác trên nền tảng Discord!
---

> **🚀 Tổng Kết**: Chúng ta đã biến một bot Discord trắng trơn thành một hệ thống AI thông minh, có cơ sở dữ liệu lưu trữ trên mạng, có trí nhớ dài hạn, chống sập xuất sắc, sở hữu Web Dashboard giám sát và cuối cùng là tự mình sinh tồn độc lập trên đám mây 24/7! Cậu hoàn toàn có thể tự hào về khối lượng công việc khổng lồ này!
