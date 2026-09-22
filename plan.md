# 📅 Chi Tiết Kế Hoạch - Giai Đoạn 11 (Minigame Pixel Art & Xây Dựng Bản Đồ)

## 1. Mục Tiêu Tổng Quan
- **Thích ứng cấu hình:** Chuyển từ đồ họa 3D/Live2D sang phong cách **Pixel Art** nhẹ nhàng, tối ưu trên Web.
- **Tương tác hóa:** Biến Web Dashboard không chỉ là nơi xem dữ liệu mà trở thành một thế giới nhỏ (Minigame), nơi cậu có thể điều khiển bé Ayaka đi dạo quanh bản đồ.
- **Phong cách nghệ thuật:** Lấy cảm hứng từ *Thị Trấn Thủy Triều (Coral Island) / Stardew Valley* với góc nhìn **Top-Down 3/4** (Góc nhìn chéo từ trên xuống nhưng vẫn thấy được chiều sâu mặt trước của nhân vật/cảnh vật).
- *(Lưu ý: Các dự án liên quan đến 3D, Blender đã được đóng gói và cất vào `IDEAS.md` để dành cho tương lai).*

## 2. Tiến Độ Các Bước Thực Hiện

### Bước 1: Chế Tạo Sprite & Hoạt Ảnh Nhân Vật (✅ Đã Xong)
- Tự vẽ và thiết kế Sprite Sheet khung cơ bản `32x48` px.
- Dùng Python (OpenCV) bóc tách lớp nền lưới, tạo ra chuỗi hoạt ảnh mượt mà: Idle (Chớp mắt) và Walk (Đi bộ).
- Tích hợp lên Web bằng CSS thuần (`steps()`), xử lý logic click chuột.

### Bước 2: Xây Dựng Bản Đồ (Map Building) bằng Tiled (🚧 Đang Tiến Hành)
- **Công cụ:** Vẽ Tile nền (đất, cỏ, nước) bằng Piskel, sau đó dùng **Tiled (Map Editor)** để lắp ráp.
- **Giao thức:** Sử dụng lưới `Orthogonal` (Lưới ô vuông thẳng góc) nhưng hình vẽ mang ảo giác góc nhìn 3/4.
- **Cấu trúc Layer:** Thiết lập tối thiểu 2-3 lớp:
  - `Ground`: Lớp đất nền.
  - `Collision / Obstacle`: Vật thể cản đường (đá, hàng rào).
  - `Foreground`: Tán cây che khuất đầu nhân vật.

### Bước 3: Lập Trình Tương Tác & Di Chuyển (JS Game Engine) (🔜 Sắp Tới)
- Trích xuất file `.tmx` hoặc JSON từ Tiled để nạp vào Web (có thể code tay hoặc dùng thư viện nhẹ như Phaser/Kaboom).
- Code cơ chế bắt phím `W A S D` để điều khiển Ayaka chạy quanh Map.
- Xử lý Va chạm (Collision): Không cho phép Ayaka đi xuyên qua gốc cây, hòn đá.
- Cơ chế Camera (Tùy chọn): Nếu Map lớn hơn màn hình, camera sẽ tự động trượt theo Ayaka.

## 3. Công Cụ Đề Xuất
1. **Piskel**: Vẽ từng viên gạch/tán cây (Tiles) ở kích thước chuẩn `32x32`.
2. **Tiled**: "Xây dựng" và thiết kế cả một thị trấn khổng lồ từ những viên gạch đó.
3. **VS Code**: Cập nhật logic Javascript điều khiển.
