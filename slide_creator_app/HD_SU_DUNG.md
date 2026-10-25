# 📖 HƯỚNG DẪN SỬ DỤNG ỨNG DỤNG TẠO ẢNH SLIDE & INFOGRAPHIC

Ứng dụng giúp bạn tạo các slide infographic dạng dọc tỉ lệ **9:16** (1080 × 1920 px) hoặc **1:1**, **4:5**, **16:9** chuyên nghiệp chuẩn TikTok, Reels, Facebook, YouTube Shorts chỉ từ một đoạn văn bản thô.

---

## 🚀 1. Cách Khởi Chạy Ứng Dụng

Bạn có thể chạy ứng dụng theo **3 cách cực kỳ đơn giản**:

### Cách 1: Click đúp file `.bat` (Khuyên dùng nhất)
- Tìm file `Chay_Ung_Dung_Tao_Slide.bat` ở thư mục gốc của dự án.
- **Click đúp** vào file này.
- Hệ thống sẽ tự động bật máy chủ cục bộ và tự động mở trình duyệt web tới địa chỉ `http://localhost:8520`.

### Cách 2: Mở trực tiếp file `index.html`
- Vào thư mục `slide_creator_app`.
- **Click đúp** trực tiếp vào file `index.html` (mở bằng Google Chrome, Microsoft Edge, Cốc Cốc, Brave...).
- Không cần cài đặt bất kỳ môi trường nào!

### Cách 3: Chạy bằng lệnh Python CLI (Không cần mở trình duyệt)
Nếu bạn muốn tạo ảnh tự động từ file text:
```bash
python slide_creator_app/generate_slide_cli.py --file slide_creator_app/sample_input.txt --output ket_qua.png
```

---

## ⚡ 2. Cách Nhập Nội Dung Bằng Tính Năng "Nhập Nhanh" (Auto-Detect)

1. Trên thanh công cụ trên cùng, bấm nút **⚡ Nhập văn bản nhanh**.
2. Dán đoạn nội dung bất kỳ của bạn vào ô text, ví dụ:
```text
SLIDE 2: XÓA BỎ THUẾ KHOÁN
Tiêu đề: 🚫 CHÍNH THỨC XÓA BỎ THUẾ KHOÁN, CHUYỂN SANG TỰ KÊ KHAI
Nội dung:
Bãi bỏ hoàn toàn hình thức thuế khoán định mức cố định hàng năm.
Hộ kinh doanh chuyển sang tự khai - tự tính - tự nộp thuế theo doanh thu thực tế.
Dữ liệu kinh doanh được kiểm soát chặt qua hóa đơn điện tử và dòng tiền ngân hàng.
Chấm dứt tình trạng "khoán tượng trưng" đối với các cơ sở kinh doanh quy mô lớn.
```
3. Bấm **🚀 Phân tích & Tạo ngay**.
4. Hệ thống sẽ **tự động**:
   - Trích xuất huy hiệu: `CHÍNH SÁCH THUẾ HỘ KINH DOANH • SLIDE 02/08`
   - Nhận diện icon cấm: `🚫` và chia dòng tiêu đề đẹp mắt.
   - Trích xuất 4 ý gạch đầu dòng.
   - Tự động nhận diện và **tô đỏ các từ khóa quan trọng** (như: *thuế khoán định mức*, *tự khai - tự tính - tự nộp thuế*, *hóa đơn điện tử và dòng tiền ngân hàng*).

---

## ✨ 3. Tùy Chỉnh Chi Tiết

- **Tô đỏ từ khóa thủ công**:
  - Dùng cú pháp Markdown: `**từ khóa cần tô màu**`.
  - Hoặc bôi đen từ khóa trong ô nhập rồi bấm nút **✨ Đặt từ khóa**.
- **Chọn Icon Tiêu Đề**:
  - Bấm chọn nhanh các icon phổ biến: `🚫 Cấm`, `⚠️ Cảnh báo`, `📢 Thông báo`, `⚖️ Luật`, `💰 Tiền tệ`, `🏢 Doanh nghiệp`, `💡 Lưu ý`.
- **Đổi Tỷ Lệ Khung Hình**:
  - `9:16`: Tỷ lệ dọc chuẩn TikTok, Reels, Story (1080 × 1920).
  - `1:1`: Vuông chuẩn Instagram, Facebook (1080 × 1080).
  - `4:5`: Dọc bài viết Fanpage Facebook (1080 × 1350).
  - `16:9`: Khung ngang bài thuyết trình hoặc video (1920 × 1080).
- **Bộ Màu Sắc (Themes)**:
  - 🍷 **Đỏ Rượu (Thuế & Pháp luật - Giống 100% mẫu tham khảo)**
  - 🔷 **Xanh Sapphire (Tài chính & Ngân hàng)**
  - 🌿 **Xanh Lục Emerald (Môi trường & Đầu tư)**
  - 🔶 **Cam Hổ Phách (Thương mại & Bán lẻ)**
  - 🔮 **Tím Thạch Anh (Công nghệ & AI)**
  - 🖤 **Dark Luxury (Hắc Kim Sang Trọng)**

---

## 📥 4. Xuất Ảnh & Chia Sẻ

- **Tải ảnh PNG (HD)**: Bấm `📥 Tải ảnh PNG (HD)` để lưu file ảnh độ phân giải cao 1080p sắc nét.
- **Sao chép ảnh (Clipboard)**: Bấm `📋 Sao chép ảnh`, sau đó mở Zalo, Messenger, Photoshop hoặc Canva và nhấn `Ctrl + V` để dán ngay lập tức.
- **Tải trọn bộ Slides (ZIP)**: Nếu bạn tạo nhiều slide (Slide 1, Slide 2, Slide 3...), chỉ cần bấm `📦 Tải tất cả (ZIP)` để tải về trọn bộ trong một file nén.
