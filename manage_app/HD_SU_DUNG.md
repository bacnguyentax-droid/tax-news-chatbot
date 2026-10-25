# HƯỚNG DẪN SỬ DỤNG MANAGE APP

**Manage App** là ứng dụng web quản lý, dò quét và tự động tải các văn bản pháp luật mới trên internet (Thuế, Hải quan, Đầu tư, Đất đai...) và đồng bộ lưu trữ trực tiếp lên các thư mục Google Drive tương ứng.

---

## 1. CÁCH KHỞI CHẠY ỨNG DỤNG

### Cách 1: Chạy bằng file Batch (Khuyên dùng)
- Click đúp vào file **`Chay_Manage_App.bat`** tại thư mục gốc.
- Hệ thống sẽ tự động bật backend server và mở trình duyệt web tại địa chỉ:
  👉 **`http://localhost:5055`**

### Cách 2: Khởi chạy bằng dòng lệnh
```bash
cd manage_app
python app.py
```

---

## 2. TỔNG QUAN CÁC TÍNH NĂNG THEO TAB

Giao diện được thiết kế dạng Tabs hiện đại trên thanh điều hướng đầu trang:

### 📌 TAB 1: Quét và Tải văn bản (Document Scanner & Downloader)
1. **Khu vực nhập liệu tìm kiếm:**
   - **Ô danh sách lĩnh vực:** Cho phép nhập tự do các lĩnh vực cần quét (ví dụ: *thuế, hải quan, đầu tư, đất đai, tài chính, lao động, bảo hiểm xã hội...*). Ngoài ra có các chip gợi ý để chọn nhanh trong 1 click.
   - **Tính năng tự động lưu:** Hệ thống tự động ghi nhớ và lưu lại giá trị nhập sau cùng vào cả trình duyệt (Local Storage) và file cấu hình máy chủ (`config.json`). Lần sau mở ứng dụng lên vẫn giữ nguyên chính xác giá trị đã nhập.
   - **Bộ lọc thời gian:** Cho phép chọn `Từ ngày` đến `Đến ngày` dựa theo ngày phát hành văn bản, kèm theo các nút chọn nhanh: *30 ngày qua, 90 ngày qua, Năm 2026, 2024 - 2026*.
   - **Nút "Bắt đầu dò quét văn bản":** Quét các văn bản mới trên internet khớp với lĩnh vực và khoảng thời gian.

2. **Khu vực hiển thị kết quả (Bảng danh sách văn bản):**
   - **Cột Checkbox:** Cho phép tick chọn từng văn bản hoặc chọn tất cả bằng checkbox ở tiêu đề bảng.
   - **Tên văn bản / Số hiệu:** Hiển thị số hiệu, loại văn bản (Nghị định, Thông tư, Quyết định, Công văn) và tên trích yếu. Bấm vào số hiệu để mở popup xem toàn văn bản.
   - **Đơn vị ban hành:** Được gắn nhãn màu sắc riêng biệt (Chính phủ, Bộ Tài chính, Tổng cục Thuế, Tổng cục Hải quan...).
   - **Ngày phát hành & Hiệu lực:** Ngày ban hành chính thức.
   - **Trích yếu / Nội dung chính:** Tóm tắt các điểm mới, phạm vi điều chỉnh và đối tượng áp dụng.
   - **Cột chọn thư mục Google Drive:** Dropdown hiển thị đầy đủ các thư mục trên Google Drive để người dùng chọn nhanh nơi lưu trữ cho từng văn bản.
   - **Thao tác hàng loạt (Batch Folder Selector):** Cho phép chọn nhanh 1 thư mục Google Drive trên thanh công cụ và bấm **"Áp dụng"** để gán cho tất cả các văn bản đang được tick chọn.

3. **Thao tác tải về & Đẩy lên Google Drive:**
   - **Nút "Tải về và lưu lên Google Drive":** Khi bấm nút này, hệ thống sẽ tự động tạo file văn bản định dạng chuẩn thể thức hành chính (bao gồm Quốc hiệu, Tiêu ngữ, Cơ quan ban hành, Trích yếu, Nội dung, Chữ ký), sau đó đẩy file trực tiếp vào đúng thư mục Google Drive đã chọn.
   - **Xem file trên Drive:** Sau khi tải lên thành công, trên từng dòng sẽ xuất hiện nút **"Xem trên Drive"** để mở trực tiếp file trên Google Drive chỉ với 1 click.
   - **Tải file về máy:** Có nút phụ để người dùng có thể tải file PDF về máy tính cá nhân để lưu trữ offline nếu muốn.

---

### ⚙️ TAB 2: Thiết lập cấu hình (Settings)
1. **Cấu hình & Kết nối Google Drive:**
   - Hiển thị thông tin tài khoản Google Drive đang liên kết (Tên người dùng, Email, Dung lượng lưu trữ đã dùng / Tổng dung lượng).
   - Nút **"Tự động phát hiện cấu hình trên máy":** Tự động phát hiện và kế thừa các file xác thực có sẵn trên máy tính mà không cần phải nhập lại.
   - Nút **"Kiểm tra kết nối Google Drive":** Kiểm tra xác thực API và tự động tải lại danh sách toàn bộ thư mục từ Drive.
   - Form cấu hình: Cho phép nhập hoặc cập nhật Client ID, Client Secret, Refresh Token. Thông tin được mã hóa và lưu trữ an toàn trong file `config.json` và `token.json`.
2. **Quản lý Thư mục Google Drive:**
   - Hiển thị danh sách/cây thư mục hiện có trên Google Drive của người dùng.
   - Cho phép chọn 1 thư mục làm **"Thư mục lưu trữ mặc định"** cho Tab 1.
   - Cho phép **"Tạo thư mục mới trực tiếp trên Google Drive"** ngay tại giao diện mà không cần phải mở website Google Drive.
