import os

# YouTube Data API Key v3 mặc định
DEFAULT_YOUTUBE_API_KEY = "AIzaSyDiC2ugIDBd_pyNFsfJgO87cvADaD14r3c"

# Đường dẫn thư mục lưu trữ mặc định
DEFAULT_OUTPUT_DIR = r"D:\Data_Video"
DEFAULT_EXCEL_PATH = os.path.join(DEFAULT_OUTPUT_DIR, "Danh_Sach_Video_Thue.xlsx")

import sys

# Đường dẫn thư mục hình ảnh Banner giao diện 9:16
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    APP_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = BASE_DIR

DEFAULT_ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DEFAULT_TOP_BANNER_PATH = os.path.join(DEFAULT_ASSETS_DIR, "_top2.png")
DEFAULT_BOTTOM_BANNER_PATH = os.path.join(DEFAULT_ASSETS_DIR, "_Bottom_1.png")
DEFAULT_FULL_TEMPLATE_PATH = os.path.join(DEFAULT_ASSETS_DIR, "full.png")
DEFAULT_COOKIE_PATH = os.path.join(DEFAULT_ASSETS_DIR, "cookies.txt")

# Tự động khởi tạo thư mục assets và sao chép ảnh banner nếu chưa có
os.makedirs(DEFAULT_ASSETS_DIR, exist_ok=True)
_artifact_dir = r"C:\Users\ADMIN\.gemini\antigravity\brain\aeaefff5-e4a9-4f8b-80b7-ab9908bb10d5"
_mapping = {
    "media__1791606747372.png": "_top2.png",
    "media__1791606809607.jpg": "_Bottom_1.png",
    "media__1791607025494.png": "full.png"
}
for _src, _dst in _mapping.items():
    _target = os.path.join(DEFAULT_ASSETS_DIR, _dst)
    if not os.path.exists(_target):
        _src_path = os.path.join(_artifact_dir, _src)
        if os.path.exists(_src_path):
            try:
                import shutil
                shutil.copy(_src_path, _target)
            except Exception:
                pass

# Danh sách từ khóa thuế mở rộng để quét phụ đề và ngữ cảnh liên quan
DEFAULT_TAX_KEYWORDS = [
    "thuế",
    "thuế phí",
    "phí sang tên",
    "thuế bán hàng",
    "thuế kinh doanh",
    "hộ kinh doanh",
    "cá nhân kinh doanh",
    "thuê tài sản",
    "doanh nghiệp",
    "hoàn thuế",
    "thuế nhà đất",
    "thuế đất",
    "thuế thu nhập",
    "thuế thu nhập cá nhân",
    "thuế doanh nghiệp",
    "thuế giá trị gia tăng",
    "vat",
    "thu ngân sách",
    "nghĩa vụ thuế",
    "kê khai thuế",
    "nộp thuế",
    "nợ thuế",
    "miễn thuế",
    "giảm thuế",
    "lệ phí",
    "mã số thuế",
    "ngành thuế",
    "cơ quan thuế",
    "cục thuế",
    "bộ tài chính",
    "hóa đơn điện tử",
    "quyết toán thuế",
    "thuế thành phố hồ chí minh",
    "thuế hà nội",
    "thuế tphcm",
    "dừng xuất cảnh",
    "cấm xuất cảnh"
]



# Danh sách các kênh truyền hình YouTube chính thức theo yêu cầu người dùng
DEFAULT_CHANNELS = [
    {"name": "VTV Nam Bộ - Tin Tức Tổng Hợp", "id": "UCuyLN6dFG4y316fEhe455fQ"},
    {"name": "Thời Sự VTV1 Hôm Nay", "id": "UC1AfsHpD-eAftexOwXd106Q"},
    {"name": "HTV Tin Tức", "id": "UCZYKmEA2iQOSbyKc6xj5Vfw"},
    {"name": "60 Giây Official", "id": "UCRjzfa1E0gA50lvDQipbDMg"},
    {"name": "VTV24", "id": "UCabsTV34JwALXKGMqHpvUiA"},
    {"name": "Tin tức sự kiện Thuế", "id": "UCLzi80M3Zdu8sQBty5V4ZNA"},
    {"name": "VTC News", "id": "UC68VHcQS5x-WNFmf5cAFtgg"}
]



# Cấu hình thuật toán gom nhóm bao trọn bài tin thời sự (Tính bằng giây)
MAX_GAP_SECONDS = 60       # Nối các câu trong cùng 1 bài tin nếu cách nhau dưới 60 giây
BUFFER_START_SECONDS = 25   # Lùi lại 25 giây trước từ đầu tiên để bắt trọn câu lời dẫn BTV
BUFFER_END_SECONDS = 35     # Tiến thêm 35 giây sau từ cuối cùng để lấy trọn kết luận bài đưa tin
