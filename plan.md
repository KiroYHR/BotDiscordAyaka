# 📅 Chi Tiết Kế Hoạch - Giai Đoạn 11 (Chế Tạo Mô Hình Ayaka Độc Quyền)

## 1. Mục Tiêu Tổng Quan
- Tự thiết kế, tùy biến và tạo hoạt ảnh (Animation) cho mô hình Kamisato Ayaka để phục vụ cho Web Dashboard, do các nguồn miễn phí trên mạng không đáp ứng đủ yêu cầu về thẩm mỹ và chất lượng.
- Tìm hiểu các công cụ đồ họa máy tính chuyên nghiệp như **Blender**, **Mixamo**, và **Live2D Cubism**.

## 2. Các Bước Thực Hiện Chi Tiết

### Bước 1: Chuẩn Bị Mô Hình Gốc (Base Model)
- **Nguồn tài nguyên chính (Khuyên dùng)**: 
  - **Aplaybox (模之屋 - aplaybox.com)**: Đây là trang web chính thức mà nhà phát hành MiHoYo (Genshin Impact) dùng để đăng tải các mô hình 3D (MMD) gốc của nhân vật cực kỳ chất lượng. Cậu có thể lên đây tìm từ khóa **神里绫华** (Kamisato Ayaka) để tải về tệp `.pmx`. (Lưu ý: Trang web này cần tạo tài khoản).
  - **DeviantArt**: Nếu không tạo được tài khoản Aplaybox, cậu có thể lên trang *DeviantArt.com* và tìm kiếm *"Genshin Impact Ayaka MMD official download"*. Cộng đồng quốc tế thường xuyên chia sẻ lại các tệp gốc từ Aplaybox lên đây qua link Google Drive hoặc Mega.
- **Lưu ý bản quyền**: Các mô hình này được MiHoYo cung cấp miễn phí nhưng đi kèm điều khoản nghiêm ngặt: Chỉ sử dụng cho mục đích cá nhân, học tập, phi thương mại. Tuyệt đối không bán lại.

### Bước 2: Nhập Mô Hình Vào Blender (Sử dụng MMD Tools)
- **Cài đặt Blender & Plugin**: 
  - Cài đặt phần mềm Blender phiên bản mới nhất (4.2+).
  - Do Blender mặc định không hỗ trợ tệp `.pmx`, chúng ta phải cài thêm Add-on **[mmd_tools](https://github.com/UuuNyaa/blender_mmd_tools/releases)** (Tải tệp `.zip`, vào Blender chọn *Biên Soạn > Tùy Chọn > Tiện ích > Cài đặt* và nạp tệp zip vào).
- **Import (Nhập)**: Sử dụng tính năng *Tập Tin > Nhập > MikuMikuDance Model (.pmx)* để đưa Ayaka nguyên bản (có đầy đủ xương và vật liệu) vào Blender.

### Bước 3: Tạo Hoạt Ảnh Thủ Công (Manual Animation)
Vì chúng ta quyết định giữ lại toàn bộ bộ xương MMD gốc siêu chi tiết (bao gồm cả xương tóc, xương váy và khuôn mặt) để giữ nguyên thần thái của Ayaka, chúng ta sẽ tự làm Animation ngay trong Blender:
1. **Chế độ Pose Mode (Tạo dáng)**: Chọn khung xương (`Kamisato Ayaka_arm`) và chuyển sang chế độ Pose Mode. Tại đây cậu có thể xoay các khớp xương tay, chân, đầu để tạo ra các tư thế khác nhau.
2. **Keyframe (Lưu chuyển động)**: Mở cửa sổ *Timeline* ở dưới cùng, tạo dáng xong thì ấn phím `I` để lưu (Insert Keyframe) vị trí và góc xoay của xương tại từng khung hình (Frame).
3. **Bake Physics (Nướng vật lý)**: Nhờ có MMD Tools, áo và tóc của Ayaka đã được cài sẵn vật lý (Rigidbodies). Sau khi tạo xong chuyển động của tay chân, chúng ta sẽ dùng tính năng *Bake Physics* để Blender tự động tính toán lực gió làm đung đưa tóc và váy, biến chúng thành Keyframe có thể xuất ra được.

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
