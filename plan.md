# 📅 Chi Tiết Kế Hoạch - Giai Đoạn 11 (Chế Tạo Mô Hình Ayaka Độc Quyền)

## 1. Mục Tiêu Tổng Quan
- Tự thiết kế, tùy biến và tạo hoạt ảnh (Animation) cho mô hình Kamisato Ayaka để phục vụ cho Web Dashboard, do các nguồn miễn phí trên mạng không đáp ứng đủ yêu cầu về thẩm mỹ và chất lượng.
- Tìm hiểu các công cụ đồ họa máy tính chuyên nghiệp như **Blender**, **Mixamo**, và **Live2D Cubism**.

## 2. Các Bước Thực Hiện Chi Tiết

### Bước 1: Chuẩn Bị Mô Hình Gốc (Base Model)
- **Nguồn tài nguyên**: Tìm kiếm các mô hình MMD (MikuMikuDance) của Genshin Impact do Mihoyo cung cấp công khai trên Bilibili (hoặc các nguồn chia sẻ mô hình 3D thô có định dạng `.pmx`, `.fbx`, `.obj`).
- **Lưu ý bản quyền**: Chỉ sử dụng cho mục đích cá nhân và phi thương mại.

### Bước 2: Nhập Mô Hình Vào Blender & Chỉnh Sửa
- **Cài đặt Blender**: Tải và cài đặt phần mềm Blender phiên bản mới nhất.
- **Import (Nhập) & Clean up**: Nhập mô hình thô vào Blender. Chỉnh sửa lại hệ thống vật liệu (Materials) và lưới (Mesh) nếu bị lỗi kết cấu.
- **Tối ưu hóa Shader**: Tạo các node Shader đặc biệt (Cel Shading/Toon Shading) trong Blender để giữ nguyên phong cách Anime đặc trưng của Ayaka thay vì đổ bóng chân thực.

### Bước 3: Gắn Xương (Rigging) và Tạo Hoạt Ảnh (Animation)
- **Phương án 1: Dùng Mixamo (Tự động & Nhanh chóng)**
  - Xuất mô hình thô (.fbx) không kèm xương từ Blender.
  - Tải lên trang web Mixamo của Adobe để thuật toán tự động nhận diện và gắn xương (Auto-Rigger).
  - Chọn các hoạt ảnh ưng ý (Idle, Vẫy tay, Đi bộ) và tải về.
- **Phương án 2: Tự làm trong Blender (Nâng cao)**
  - Sử dụng khung xương (Armature) có sẵn hoặc tự tạo khung xương mới.
  - Áp dụng các kỹ thuật Weight Painting để xương di chuyển không làm biến dạng váy/tóc.
  - Mở Dope Sheet / Timeline để gán Keyframe tạo cử động nhịp nhàng (thở, chớp mắt).

### Bước 4: Xuất Tệp (Export) và Tích Hợp Web
- **Định dạng 3D (.glb)**:
  - Nếu làm mô hình 3D, xuất file cuối cùng dưới định dạng `.glb` (GLTF Binary) có bao gồm sẵn Texture và Animation.
  - Bỏ vào thư mục `web/dashboard/assets/` và dùng Three.js (AnimationMixer) để phát trên Web.
- **Định dạng Live2D (.moc3)**:
  - Nếu muốn làm Live2D 2D, chúng ta sẽ cần "chụp" (Render) tách lớp từng bộ phận (đầu, mắt, tóc, thân) từ Blender ra các tệp `.png` nền trong suốt.
  - Đưa tất cả vào phần mềm **Live2D Cubism Editor** để gắn mesh và tạo Parameter chuyển động 2D ảo diệu.

## 3. Công Cụ Cần Thiết Cài Đặt
1. **Blender 3D**: Phần mềm cốt lõi để xử lý mô hình.
2. **MMD Tools (Addon)**: Plugin cho Blender để nhập tệp `.pmx` của Genshin Impact dễ dàng.
3. **Mixamo (Web)**: Đóng vai trò thư viện hoạt ảnh tự động.
4. **Live2D Cubism Editor** *(Tùy chọn)*: Nếu quyết định làm mô hình 2D thay vì 3D.

---
*Đây là một chân trời hoàn toàn mới đòi hỏi nhiều kỹ năng đồ họa, nhưng kết quả thu được sẽ là một Ayaka 100% "chính chủ" không đụng hàng với bất kỳ ai!*
