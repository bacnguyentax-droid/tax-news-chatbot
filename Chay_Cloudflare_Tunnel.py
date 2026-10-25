import os
import sys
import time
import re
import json
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "tiktok_pipeline_app", "integrations_config.json")

# Tim duong dan cloudflared
cf_candidates = [
    r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
    r"C:\Program Files\cloudflared\cloudflared.exe",
    "cloudflared"
]
cf_exe = None
for c in cf_candidates:
    if os.path.isabs(c) and os.path.exists(c):
        cf_exe = c
        break
if not cf_exe:
    cf_exe = "cloudflared"

print("=" * 75)
print("🚀 TIKTOK STUDIO 2026 - KHỞI ĐỘNG CLOUDFLARE HTTPS TUNNEL (KHÔNG BỊ CHẶN)")
print("=" * 75)
print("[*] Đang khởi động đường hầm Cloudflare cho cổng 5150...")

proc = subprocess.Popen(
    [cf_exe, "tunnel", "--url", "http://localhost:5150"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="ignore"
)

tunnel_url = None
start_time = time.time()
while time.time() - start_time < 20:
    line = proc.stdout.readline()
    if not line:
        continue
    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
    if match:
        tunnel_url = match.group(0)
        break

if tunnel_url:
    print("\n" + "=" * 75)
    print("✅ ĐÃ TẠO ĐƯỜNG HẦM CLOUDFLARE HTTPS THÀNH CÔNG (KHÔNG BỊ TRANG CẢNH BÁO):")
    print(f"👉 {tunnel_url}")
    print("=" * 75)

    # Luu truc tiep vao integrations_config.json
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg.setdefault("tiktok", {})["public_base_url"] = tunnel_url
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            print("[*] Đã tự động cập nhật đường dẫn vào cấu hình Web App!")
        except Exception as e:
            print(f"[!] Lỗi ghi config: {e}")

    print("\n💡 Bây giờ bạn có thể:")
    print("1. Mở Web App tại: http://127.0.0.1:5150")
    print("2. Vào 'Tạo ảnh cuộn' -> bấm 'Đăng video lên tiktok'")
    print("3. Bấm 'Mở Xem Slide' để thấy ảnh mở thẳng trực tiếp không còn trang cảnh báo!")
    print("\n[*] Giữ cửa sổ này mở để duy trì đường hầm. Nhấn Ctrl+C để dừng.")
    print("-" * 75)

    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
    except KeyboardInterrupt:
        print("\n[*] Đang dừng tunnel...")
        proc.terminate()
else:
    print("[!] Không tìm thấy đường dẫn tunnel sau 20s. Vui lòng kiểm tra lại kết nối mạng.")
    proc.terminate()
