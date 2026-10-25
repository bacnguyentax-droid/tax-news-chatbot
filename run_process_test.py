"""
Script tự động hóa xử lý toàn bộ các văn bản theo Loại văn bản được chỉ định.
Hỗ trợ 'CV Cảnh báo rủi ro', 'CV kiểm tra, xử lý hóa đơn', v.v.
Lặp lại cho đến khi xử lý hết các văn bản trong danh sách.

Cách chạy:
    python run_process_test.py                                  # Mặc định: CV kiểm tra, xử lý hóa đơn
    python run_process_test.py --type "CV Cảnh báo rủi ro"      # Chạy loại CV Cảnh báo rủi ro
    python run_process_test.py --max 5                          # Giới hạn xử lý tối đa 5 văn bản
    python run_process_test.py --dry-run                        # Xem trước không bấm Chuyển
    python run_process_test.py --headless                       # Chạy ẩn không mở cửa sổ Chrome
"""

import sys
import os
import argparse

# Console UTF-8 configuration
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vpdt_manager.document_processor import VPDTDocumentProcessor


def main():
    parser = argparse.ArgumentParser(description="VPDT Batch Document Processor")
    parser.add_argument(
        "--type", "-t",
        type=str,
        default="CV kiểm tra, xử lý hóa đơn",
        help="Loại văn bản cần lọc và xử lý (mặc định: 'CV kiểm tra, xử lý hóa đơn')"
    )
    parser.add_argument("--max", "-m", type=int, default=None, help="Số lượng văn bản tối đa cần xử lý (mặc định: xử lý hết)")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ điền thông tin và dừng lại xem trước, không bấm nút Chuyển")
    parser.add_argument("--headless", action="store_true", help="Chạy ẩn danh không mở cửa sổ trình duyệt")
    args = parser.parse_args()

    doc_type = args.type

    is_save_only = any(
        k in doc_type.lower()
        for k in ["xử phạt", "đính chính", "bỏ địa chỉ", "xphc"]
    )

    print("=" * 70)
    print(f" 🚀 VPDT AUTOMATION - TỰ ĐỘNG XỬ LÝ TOÀN BỘ '{doc_type}' ")
    print("=" * 70)
    print(" Quy trình tự động lặp lại cho từng văn bản:")
    print("  1. Vào 'Văn bản đến' -> 'Cần xử lý'")
    print(f"  2. Lọc Loại văn bản: '{doc_type}'")
    if is_save_only:
        print("  3. Mở văn bản -> Bấm nút 'Lưu văn bản' trên thanh thao tác")
        if args.dry_run:
            print("  4. [CHẾ ĐỘ XEM TRƯỚC / DRY-RUN]: Dừng lại để quan sát, không bấm xác nhận Lưu.")
        else:
            print("  4. Xác nhận lưu văn bản (confirm OK)")
    else:
        print("  3. Mở văn bản -> Bấm 'Phân công'")
        print("  4. Phân công:")
        print("     - Trang 1: Chọn Nam, Ngo Hoang Nam (DLRR-HCM)")
        print("     - Trang 3: Chọn Lanh, Nguyen Xuan Lanh (DLRR-HCM)")
        print("     - Cách thức xử lý: 'Lưu văn bản'")
        print("     - Chuyên viên xử lý chính: 'Nam, Ngo Hoang Nam (DLRR-HCM)'")
        if args.dry_run:
            print("     - [CHẾ ĐỘ XEM TRƯỚC / DRY-RUN]: Dừng lại để quan sát, không bấm Chuyển.")
        else:
            print("     - Bấm nút 'Chuyển' ở cuối trang")
    print(f"  5. Lặp lại cho đến khi hết văn bản (Giới hạn: {'Không giới hạn' if args.max is None else args.max}).")
    print("=" * 70 + "\n")

    processor = VPDTDocumentProcessor()
    res = processor.process_all_documents(
        doc_type=doc_type,
        max_documents=args.max,
        click_transfer=not args.dry_run,
        headless=args.headless
    )

    if res["success"]:
        print("\n" + "=" * 70)
        print("🎉 QUY TRÌNH HOÀN TẤT THÀNH CÔNG!")
        print(f"📋 Loại văn bản: {res.get('doc_type', doc_type)}")
        print(f"📊 Tổng số văn bản đã xử lý: {res['total_processed']}")
        for doc in res.get("processed_documents", []):
            print(f"   ✓ [#{doc['index']}] Số đến: {doc['doc_number']} - {doc.get('title', '')[:50]}")
        print(f"📸 Ảnh chụp màn hình: {res['screenshot']}")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print(f"❌ THẤT BẠI: {res['message']}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
