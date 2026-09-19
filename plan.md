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

### Bước 3: Tạo Hoạt Ảnh Bằng Dữ Liệu VMD (Nhàn hạ & Đẹp nhất)
Nhìn bảng xương chằng chịt tiếng Nhật kia ai cũng phải choáng ngợp! Rất may, vì chúng ta đang dùng mô hình chuẩn MMD, nên chúng ta **hoàn toàn không cần làm hoạt ảnh bằng tay** hay nhờ AI ngoài nào cả! Chúng ta sẽ sử dụng các tệp chuyển động có sẵn gọi là **VMD (Vocaloid Motion Data)** do cộng đồng chia sẻ.
1. **Tìm & Tải VMD**: Tìm kiếm trên mạng (Youtube, DeviantArt, Bilibili) các tệp hoạt ảnh MMD có đuôi `.vmd` (Ví dụ tìm từ khóa: *MMD Idle motion dl*, *MMD Walk motion* hoặc các bài nhảy).
2. **Nhập (Import) VMD vào Blender**: Bấm chọn bộ xương (`Kamisato Ayaka_arm`), sau đó vào *Tập Tin > Nhập > VMD (.vmd)* và chọn tệp vừa tải. Ayaka sẽ lập tức di chuyển cực kỳ mượt mà kèm theo cả biểu cảm khuôn mặt!
3. **Bake Physics (Nướng vật lý)**: (Tùy chọn) Sử dụng tính năng Build Physics của MMD Tools để Blender tính toán độ vung vẩy của váy và tóc theo chuyển động mới.

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
