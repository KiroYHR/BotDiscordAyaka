# 📅 Chi Tiết Kế Hoạch - Giai Đoạn 11 (Chế Tạo Mô Hình Ayaka Pixel Art)

## 1. Mục Tiêu Tổng Quan
- Do giới hạn về phần cứng (PC không gánh nổi Blender/3D render), dự án sẽ chuyển hướng sang phong cách **Pixel Art** nhẹ nhàng, tối ưu, lấy cảm hứng từ các tựa game nông trại như "Thị Trấn Thủy Triều" (Coral Island / Stardew Valley).
- Tự vẽ và thiết kế Sprite Sheet cho Ayaka với các cử động cơ bản cực kỳ đáng yêu (Thở, Chớp mắt, Vẫy tay).
- Tích hợp Sprite Sheet này vào Web Dashboard để tạo cảm giác Retro/Cozy mộc mạc nhưng cuốn hút.
- *(Lưu ý: Toàn bộ các dự định liên quan đến 3D, Blender và Live2D đã được đóng gói và cất vào `IDEAS.md` để dành cho tương lai khi có điều kiện nâng cấp máy).*

## 2. Các Bước Thực Hiện Chi Tiết

### Bước 1: Chuẩn Bị Công Cụ Vẽ Pixel Art
Để vẽ Pixel, chúng ta không cần siêu máy tính, chỉ cần một trong các công cụ siêu nhẹ sau:
- **Aseprite**: Phần mềm "quốc dân" đỉnh nhất, chuyên dụng cho Pixel Animation (Khuyên dùng).
- **Piskel** hoặc **LibreSprite**: Công cụ vẽ pixel miễn phí (Piskel có thể chạy thẳng trên trình duyệt Web).
- **Photoshop**: Chỉnh lưới Grid về 1x1 pixel và dùng công cụ Bút chì (Pencil Tool) nét cứng.

### Bước 2: Phác Thảo & Thiết Kế Nhân Vật (Character Design)
- **Kích thước**: Chọn kích thước khung vẽ (Canvas) cỡ nhỏ như `32x32` hoặc `64x64` pixel để dễ kiểm soát.
- **Tạo hình**: Vẽ Ayaka dưới dạng Chibi (đầu to, thân nhỏ). Giữ lại các đặc điểm nhận dạng cốt lõi: Mái tóc xám bạc cắt bằng, nơ đỏ, và họa tiết hoa tuyết trên váy.
- **Bảng màu (Color Palette)**: Lấy mẫu màu trực tiếp từ ảnh gốc của Ayaka nhưng thu gọn lại chỉ dùng khoảng 10-15 màu để nhìn chuẩn chất Pixel cổ điển.

### Bước 3: Tạo Hoạt Ảnh (Animation) & Xuất Sprite Sheet
- **Idle Animation (Đứng chờ)**: Vẽ khoảng 4 khung hình (Frames) mô phỏng nhịp thở lên xuống của Ayaka (phần thân nhấp nhô 1 pixel, chớp mắt).
- **Xuất file**: Thay vì xuất video, chúng ta sẽ xuất toàn bộ các khung hình xếp liền nhau thành một bức ảnh dài duy nhất gọi là **Sprite Sheet** (định dạng `.png` nền trong suốt).

### Bước 4: Tích Hợp Lên Web Dashboard
- Nhúng tệp ảnh Sprite Sheet `.png` vào thư mục `web/dashboard/assets/`.
- Sử dụng CSS thuần (thuộc tính `animation` kết hợp với hàm thời gian `steps()`) để làm cho ảnh chạy khung hình một cách ảo diệu trên giao diện Web mà không tốn đến 1% CPU của máy tính.

## 3. Công Cụ Đề Xuất
1. **Aseprite / Piskel**: Để vẽ nghệ thuật Pixel.
2. **VS Code**: Để code HTML/CSS hiển thị bé Ayaka lên Web.

---
*Lối đi Pixel Art không chỉ là giải pháp "chữa cháy" hoàn hảo cho máy tính yếu, mà nó còn mang lại một nét thẩm mỹ Indie vô cùng mộc mạc, đáng yêu và cực kỳ thịnh hành!*
