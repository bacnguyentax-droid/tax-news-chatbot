"""
Test and Demonstration script for VPDT Login (Phase 1)
Run:
    python -m vpdt_manager.test_login
or
    python vpdt_manager/test_login.py
"""

import sys
import os
import getpass
import argparse
from pathlib import Path

# Fix Windows console encoding if needed
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure parent directory is in path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from vpdt_manager.config import (
    load_config,
    save_config,
    get_credentials,
    set_credentials,
    CONFIG_FILE,
    SESSION_FILE,
    SCREENSHOT_PATH
)
from vpdt_manager.auth import VPDTAuthenticator


def main():
    parser = argparse.ArgumentParser(description="VPDT Login Tester - Phase 1")
    parser.add_argument("--user", "-u", help="Tên đăng nhập VPDT")
    parser.add_argument("--password", "-p", help="Mật khẩu VPDT")
    parser.add_argument("--headless", action="store_true", help="Chạy ẩn danh không mở cửa sổ trình duyệt")
    parser.add_argument("--check-session", action="store_true", help="Chỉ kiểm tra phiên đăng nhập đã lưu")
    args = parser.parse_args()

    print("=" * 65)
    print(" 🚀 VPDT AUTOMATION - GIAI ĐOẠN 1: KIỂM THỬ ĐĂNG NHẬP HỆ THỐNG ")
    print("=" * 65)

    auth = VPDTAuthenticator()

    if args.check_session:
        print("\n[*] Đang kiểm tra phiên làm việc đã lưu từ trước...")
        if auth.is_session_valid(headless=args.headless):
            print("[+] PHIÊN ĐĂNG NHẬP VẪN CÒN HIỆU LỰC!")
            sys.exit(0)
        else:
            print("[-] Phiên đăng nhập đã hết hạn hoặc chưa tồn tại.")
            print("[*] Chuyển sang quy trình đăng nhập mới...\n")

    cfg = load_config()
    username = args.user or cfg.get("username", "")
    password = args.password or cfg.get("password", "")

    # Prompt user if credentials are not yet saved or passed
    if not username:
        print("\n[?] Chưa có thông tin tài khoản trong cấu hình.")
        username = input("👉 Nhập Tên đăng nhập VPDT: ").strip()

    if not password:
        password = getpass.getpass("👉 Nhập Mật khẩu VPDT (ký tự sẽ ẩn khi gõ): ").strip()

    if not username or not password:
        print("[!] Lỗi: Không thể tiếp tục nếu thiếu Tên đăng nhập hoặc Mật khẩu.")
        sys.exit(1)

    # Ask if user wants to save credentials to config.json
    if not cfg.get("username"):
        save_choice = input("💾 Bạn có muốn lưu tài khoản này vào config.json cục bộ để các lần sau tự động đăng nhập? (y/n) [mặc định y]: ").strip().lower()
        if save_choice in ("", "y", "yes"):
            set_credentials(username, password)
            print(f"[+] Đã lưu thông tin đăng nhập vào: {CONFIG_FILE}")

    print("\n" + "-" * 65)
    print(f"[*] Bắt đầu quy trình tự động đăng nhập...")
    print(f"[*] Tài khoản: {username}")
    print(f"[*] Chế độ: {'Chạy ngầm (Headless)' if args.headless else 'Hiển thị trình duyệt Chrome/Edge'}")
    print("-" * 65)

    result = auth.login(
        username=username,
        password=password,
        headless=args.headless,
        save_session=True
    )

    print("\n" + "=" * 65)
    if result["success"]:
        print("🎉 ĐĂNG NHẬP THÀNH CÔNG VÀO HỆ THỐNG VPDT!")
        print(f"📍 URL hiện tại: {result['current_url']}")
        print(f"📸 Ảnh chụp màn hình: {result['screenshot_path']}")
        print(f"🔑 Phiên làm việc (Session) đã được lưu tại: {SESSION_FILE}")
        print("=" * 65)
        print("\n👉 GIAI ĐOẠN 1 ĐÃ HOÀN THÀNH XUẤT SẮC!")
        print("   Tiếp theo (Giai đoạn 2):")
        print("   Chúng ta sẽ bóc tách danh mục Văn bản đến / Bàn làm việc để bắt đầu lập quy tắc xử lý.")
    else:
        print("❌ ĐĂNG NHẬP THẤT BẠI!")
        print(f"⚠️ Chi tiết: {result['message']}")
        if result["screenshot_path"] and Path(result["screenshot_path"]).exists():
            print(f"📸 Xem ảnh chụp màn hình lúc thất bại tại: {result['screenshot_path']}")
        print("=" * 65)
        sys.exit(1)


if __name__ == "__main__":
    main()
