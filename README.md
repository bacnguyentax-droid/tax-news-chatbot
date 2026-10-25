# 🎬 Hướng Dẫn Sử Dụng Ứng Dụng Tự Động Tìm Kế & Cắt Video Thuế Từ Các Đài Truyền Hình (VTV, HTV...)

Ứng dụng Python tự động tìm kiếm các video thời sự, tin tức từ các đài truyền hình chính thức trên YouTube (VTV1, VTV24, HTV, Đài Hà Nội, BTV Bình Dương...), phân tích phụ đề tự động để phát hiện phân đoạn nói về **Thuế**, tự động cắt riêng phân đoạn đó bằng `yt-dlp` + `FFmpeg`, lưu video vào thư mục `D:\Data_Video\` và ghi nhật ký thông tin chi tiết vào file Excel.

---

## 📋 Mục Lục
1. [Yêu Cầu Hệ Thống & Cài Đặt Thư Viện](#1-yêu-cầu-hệ-thống--cài-đặt-thư-viện)
2. [Hướng Dẫn Lấy YouTube Data API v3 Key](#2-hướng-dẫn-lấy-youtube-data-api-v3-key)
3. [Hướng Dẫn Cài Đặt & Cấu Hình FFmpeg Trên Windows](#3-hướng-dẫn-cài-đặt--cấu-hình-ffmpeg-trên-windows)
4. [Hướng Dẫn Chạy Ứng Dụng](#4-hướng-dẫn-chạy-ứng-dụng)
5. [Cấu Trúc Lưu Trữ Dữ Liệu](#5-cấu-trúc-lưu-trữ-dữ-liệu)
6. [Xử Lý Lỗi Thường Gặp (Troubleshooting)](#6-xử-lý-lỗi-thường-gặp)

---

## 1. Yêu Cầu Hệ Thống & Cài Đặt Thư Viện

### Yêu cầu:
- **Hệ điều hành**: Windows 10/11 (hoặc Linux/macOS).
- **Python**: Phiên bản **Python 3.8** trở lên.

### Các bước cài đặt thư viện:
Mở **Command Prompt (cmd)** hoặc **PowerShell** tại thư mục dự án và chạy lệnh sau:

```bash
pip install -r requirements.txt
```

Nếu cài lẻ từng thư viện:
```bash
pip install google-api-python-client youtube-transcript-api yt-dlp pandas openpyxl
```

---

## 2. Hướng Dẫn Lấy YouTube Data API v3 Key

Để tìm kiếm video từ YouTube theo khoảng thời gian và kênh truyền hình, ứng dụng cần 1 **YouTube API Key** (miễn phí):

1. Truy cập **Google Cloud Console**: [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Đăng nhập tài khoản Google của bạn.
3. Tạo một **Project mới** (ví dụ đặt tên: `YouTube Tax Video Bot`).
4. Tại thanh tìm kiếm trên cùng, gõ **YouTube Data API v3** và chọn API này.
5. Bấm **ENABLE** (Bật API).
6. Vào mục **Credentials** (Thông tin xác thực) ở menu bên trái -> Bấm **+ CREATE CREDENTIALS** -> Chọn **API Key**.
7. Sao chép chuỗi **API Key** vừa nhận được (Dạng `AIzaSy...`).
8. Dán API Key này vào giao diện ứng dụng GUI hoặc tham số dòng lệnh CLI.

---

## 3. Hướng Dẫn Cài Đặt & Cấu Hình FFmpeg Trên Windows

`yt-dlp` bắt buộc phải có **FFmpeg** để thực hiện lệnh cắt trực tiếp phân đoạn video (`--download-sections`).

### Bước 1: Tải FFmpeg
1. Truy cập trang tải FFmpeg chính thức: [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Tại mục **release builds**, tải file `ffmpeg-release-full.7z` hoặc `ffmpeg-git-full.7z`.

### Bước 2: Giải nén
1. Giải nén thư mục vừa tải về.
2. Đổi tên thư mục thành `ffmpeg` và di chuyển nó vào thư mục gốc ổ `C:\` (Đường dẫn dạng: `C:\ffmpeg`).
3. Đảm bảo bên trong có đường dẫn `C:\ffmpeg\bin\ffmpeg.exe`.

### Bước 3: Thêm FFmpeg vào biến môi trường PATH của Windows
1. Nhấn phím `Windows + R`, gõ `sysdm.cpl` rồi nhấn **Enter**.
2. Thẻ **Advanced** (Nâng cao) -> Bấm vào **Environment Variables...** (Biến môi trường).
3. Tại ô **System variables** (Biến hệ thống), chọn dòng **Path** -> Bấm **Edit...** (Chỉnh sửa).
4. Bấm **New** (Tạo mới) -> Nhập `C:\ffmpeg\bin`.
5. Bấm **OK** ở tất cả các cửa sổ để lưu.

### Bước 4: Kiểm tra cài đặt FFmpeg
Mở cửa sổ Command Prompt (cmd) mới và gõ:
```bash
ffmpeg -version
```
Nếu màn hình hiển thị thông tin phiên bản FFmpeg là đã cài đặt thành công!

---

## 4. Hướng Dẫn Chạy Ứng Dụng

### Cách 1: Chạy Chế Độ Giao Diện Đồ Họa (GUI - Khuyên Dùng)
Mở terminal và gõ:
```bash
python main.py
```
- Nhập **API Key** của bạn.
- Nhập **Từ ngày** và **Đến ngày** (Định dạng: `DD/MM/YYYY`, ví dụ: `10/10/2026`).
- Chọn các đài truyền hình mong muốn (VTV, HTV, BTV...).
- Bấm **▶ BẮT ĐẦU XỬ LÝ TỰ ĐỘNG**.
- Quá trình chạy sẽ được cập nhật trực tiếp tại cửa sổ **Console Log**.

### Cách 2: Chạy Chế Độ Dòng Lệnh (CLI)
Nếu muốn tích hợp vào script tự động hóa:
```bash
python main.py --cli --api-key "YOUR_API_KEY_HERE" --start-date "01/10/2026" --end-date "10/10/2026" --output-dir "D:\Data_Video"
```

---

## 5. Cấu Trúc Lưu Trữ Dữ Liệu

1. **Thư mục lưu Video**: `D:\Data_Video\`
   - Tên file video tự động đặt theo quy chuẩn: `[Tên đài]_[Ngày]_[Từ khóa rút gọn]_doan[STT].mp4`
   - Ví dụ: `VTV_10102026_ThueDat_doan1.mp4`

2. **File Nhật ký Excel**: `D:\Data_Video\Danh_Sach_Video_Thue.xlsx`
   - Bảng tổng hợp tự động thêm dòng mới (append) với các cột:
     | Số thứ tự | Tên file | Nội dung thuế liên quan | Link gốc | Thời lượng cắt |
     | :---: | :--- | :--- | :--- | :---: |
     | 1 | VTV_10102026_ThueDat_doan1.mp4 | Chi tiết đề xuất sửa đổi thuế thu nhập cá nhân... | https://youtube.com/watch?v=... | 02:45 |

---

## 6. Xử Lý Lỗi Thường Gặp

- **Lỗi `TranscriptsDisabled` / không tìm thấy phụ đề**:
  - Một số video thời sự ngắn hoặc video cũ không bật tính năng phụ đề tự động của YouTube. Ứng dụng sẽ tự động ghi cảnh báo vào log và bỏ qua video đó để không gây dừng chương trình.
- **Lỗi `yt-dlp` báo thiếu FFmpeg**:
  - Đảm bảo bạn đã thực hiện đúng [Bước 3](#3-hướng-dẫn-cài-đặt--cấu-hình-ffmpeg-trên-windows) và khởi động lại cửa sổ terminal.
- **Vượt quá Quota YouTube API Key**:
  - Tài khoản Google miễn phí cung cấp 10.000 Quota/ngày, thừa đủ cho hàng trăm lượt tìm kiếm mỗi ngày.
