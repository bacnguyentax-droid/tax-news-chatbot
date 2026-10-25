#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Công cụ kết nối Google Drive, truy cập thư mục:
_____Xây dựng video_____ -> Tạo video -> File Excel 'Thông tin'
và hiển thị toàn bộ dữ liệu lên màn hình.
"""

import os
import io
import sys
import argparse
import pandas as pd
from tabulate import tabulate

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thư viện Google API
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def display_dataframe(df, sheet_name="Sheet1"):
    """In dữ liệu DataFrame ra màn hình với định dạng bảng đẹp mắt"""
    print("\n" + "=" * 90)
    print(f"📊 DỮ LIỆU BẢNG TÍNH: [ {sheet_name} ] - Tổng số: {len(df)} dòng, {len(df.columns)} cột")
    print("=" * 90)
    
    if df.empty:
        print("(Bảng tính không có dữ liệu)")
        return
        
    # Xử lý hiển thị toàn bộ dữ liệu không bị cắt ngắn
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 1000)
    
    try:
        print(tabulate(df, headers='keys', tablefmt='psql', showindex=True))
    except Exception:
        print(df.to_string())
    print("=" * 90 + "\n")


def check_local_google_drive():
    """Quét các ổ đĩa và thư mục đồng bộ Google Drive trên máy tính"""
    print("🔍 Đang kiểm tra các ổ đĩa và thư mục đồng bộ cục bộ...")
    
    candidate_roots = []
    # Các ổ đĩa có thể mount
    for letter in ['G', 'J', 'H', 'I', 'D', 'E', 'F', 'C']:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            candidate_roots.append(drive)
            my_drive = os.path.join(drive, "My Drive")
            if os.path.exists(my_drive):
                candidate_roots.append(my_drive)
                
    user_home = os.path.expanduser("~")
    candidate_roots.extend([
        os.path.join(user_home, "Google Drive"),
        os.path.join(user_home, "Google Drive (myxteamvn@gmail.com)")
    ])
    
    folder_name_variations = [
        "_____Xây dựng video_____",
        "Xây dựng video",
        "_____Xay dung video_____",
        "Xay dung video"
    ]
    
    subfolder_variations = [
        "Tạo video",
        "Tao video"
    ]
    
    for root in candidate_roots:
        if not os.path.exists(root):
            continue
            
        for f1 in folder_name_variations:
            p1 = os.path.join(root, f1)
            if os.path.exists(p1):
                for f2 in subfolder_variations:
                    p2 = os.path.join(p1, f2)
                    if os.path.exists(p2):
                        # Tìm file excel Thông tin
                        for file in os.listdir(p2):
                            if file.lower().startswith("thông tin") or file.lower().startswith("thong tin"):
                                if file.endswith(".xlsx") or file.endswith(".xls") or file.endswith(".csv"):
                                    full_path = os.path.join(p2, file)
                                    print(f"✅ ĐÃ TÌM THẤY FILE TRÊN MÁY: {full_path}")
                                    return full_path
                                    
    return None


def read_local_excel(file_path):
    """Đọc file Excel hoặc CSV từ máy tính"""
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
            display_dataframe(df, os.path.basename(file_path))
        else:
            excel_file = pd.ExcelFile(file_path)
            for sheet in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet)
                display_dataframe(df, sheet)
        return True
    except Exception as e:
        print(f"❌ Lỗi khi đọc file Excel cục bộ: {e}")
        return False


def get_google_drive_service():
    """Xác thực và tạo Google Drive Service"""
    creds = None
    
    # Kiểm tra token đã lưu
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None
            
    # Nếu chưa có hoặc hết hạn
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
                
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                return None, "CHUA_CO_CREDENTIALS"
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Lưu token
        with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
            
    service = build('drive', 'v3', credentials=creds)
    return service, "OK"


def search_and_read_from_gdrive(service):
    """Tìm thư mục và đọc file từ Google Drive Cloud"""
    print("\n🔍 Đang tìm kiếm thư mục '_____Xây dựng video_____' trên Google Drive...")
    
    # 1. Tìm thư mục cha _____Xây dựng video_____
    query_folder1 = "name contains 'Xây dựng video' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query_folder1, fields="files(id, name)").execute()
    folders = results.get('files', [])
    
    if not folders:
        # Thử tìm không dấu
        query_folder1_fallback = "name contains 'Xay dung video' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query_folder1_fallback, fields="files(id, name)").execute()
        folders = results.get('files', [])
        
    if not folders:
        print("❌ Không tìm thấy thư mục '_____Xây dựng video_____' trên tài khoản Google Drive này.")
        print("💡 Hãy kiểm tra xem tài khoản đăng nhập có quyền truy cập vào thư mục này không.")
        return False
        
    parent_folder = folders[0]
    parent_id = parent_folder['id']
    print(f"📁 Đã tìm thấy thư mục: '{parent_folder['name']}' (ID: {parent_id})")
    
    # 2. Tìm thư mục con 'Tạo video'
    print("🔍 Đang tìm thư mục con 'Tạo video'...")
    query_folder2 = f"'{parent_id}' in parents and (name contains 'Tạo video' or name contains 'Tao video') and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results2 = service.files().list(q=query_folder2, fields="files(id, name)").execute()
    subfolders = results2.get('files', [])
    
    if not subfolders:
        print(f"❌ Không tìm thấy thư mục con 'Tạo video' bên trong '{parent_folder['name']}'.")
        return False
        
    subfolder = subfolders[0]
    subfolder_id = subfolder['id']
    print(f"📁 Đã tìm thấy thư mục con: '{subfolder['name']}' (ID: {subfolder_id})")
    
    # 3. Tìm file Excel 'Thông tin'
    print("🔍 Đang tìm file 'Thông tin'...")
    query_file = f"'{subfolder_id}' in parents and (name contains 'Thông tin' or name contains 'Thong tin') and trashed = false"
    results3 = service.files().list(q=query_file, fields="files(id, name, mimeType)").execute()
    files = results3.get('files', [])
    
    if not files:
        print(f"❌ Không tìm thấy file 'Thông tin' nào trong thư mục '{subfolder['name']}'.")
        return False
        
    target_file = files[0]
    file_id = target_file['id']
    file_name = target_file['name']
    mime_type = target_file['mimeType']
    print(f"📄 Đã tìm thấy file: '{file_name}' (Loại: {mime_type})")
    
    # 4. Tải và đọc dữ liệu
    print("⏳ Đang tải và đọc dữ liệu...")
    
    # Trường hợp là Google Sheet
    if mime_type == 'application/vnd.google-apps.spreadsheet':
        # Xuất ra dạng Excel (.xlsx)
        request = service.files().export_media(
            fileId=file_id, 
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        fh.seek(0)
        excel_file = pd.ExcelFile(fh)
        for sheet in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            display_dataframe(df, sheet)
        return True
        
    # Trường hợp là file Excel tải lên (.xlsx / .xls)
    else:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        fh.seek(0)
        excel_file = pd.ExcelFile(fh)
        for sheet in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            display_dataframe(df, sheet)
        return True


def show_credentials_guide():
    """Hướng dẫn tạo file credentials.json để kết nối Google Drive API"""
    print("\n" + "=" * 80)
    print("🔑 CHƯA TÌM THẤY FILE XÁC THỰC GOOGLE DRIVE (credentials.json)")
    print("=" * 80)
    print("Để kết nối trực tiếp với Google Drive qua API, bạn chỉ cần làm theo 3 bước sau:")
    print("1. Truy cập: https://console.cloud.google.com/")
    print("2. Vào mục 'APIs & Services' -> Bật 'Google Drive API' (Enable API).")
    print("3. Vào mục 'Credentials' -> Bấm '+ CREATE CREDENTIALS' -> Chọn 'OAuth client ID':")
    print("   - Application type: Desktop app")
    print("   - Name: Google Drive Reader")
    print("   - Bấm CREATE -> Tải file JSON về máy và đổi tên thành: credentials.json")
    print("   - Đặt file credentials.json vào thư mục dự án này.")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Đọc file Excel Thông tin trên Google Drive")
    parser.add_argument("--url", type=str, help="Link Google Sheet chia sẻ trực tiếp (nếu có)")
    parser.add_argument("--local-only", action="store_true", help="Chỉ tìm trên máy tính")
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 TRÌNH KẾT NỐI GOOGLE DRIVE & ĐỌC DỮ LIỆU EXCEL")
    print("=" * 70)
    
    # 1. Nếu có truyền link trực tiếp
    if args.url:
        print(f"🔗 Đang đọc dữ liệu từ đường dẫn: {args.url}")
        try:
            # Chuyển link Google Sheet sang dạng export CSV
            if "docs.google.com/spreadsheets" in args.url:
                import re
                match = re.search(r"/d/([a-zA-Z0-9-_]+)", args.url)
                if match:
                    sheet_id = match.group(1)
                    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                    df = pd.read_csv(csv_url)
                    display_dataframe(df, "Dữ liệu Google Sheet")
                    return
            df = pd.read_excel(args.url)
            display_dataframe(df, "Dữ liệu Excel")
            return
        except Exception as e:
            print(f"❌ Không thể tải từ URL: {e}")
            
    # 2. Thử tìm trên ổ đĩa cục bộ trước (Nhanh và không cần đăng nhập nếu đã đồng bộ)
    local_file = check_local_google_drive()
    if local_file:
        read_local_excel(local_file)
        return
        
    if args.local_only:
        print("⚠️ Không tìm thấy file trên các ổ đĩa cục bộ.")
        return
        
    # 3. Kết nối Google Drive Cloud API
    print("\n🌐 Bắt đầu kết nối đám mây Google Drive...")
    service, status = get_google_drive_service()
    
    if status == "CHUA_CO_CREDENTIALS":
        show_credentials_guide()
        
        # Cho phép người dùng dán trực tiếp link file Thông tin nếu có
        try:
            print("👉 HOẶC BẠN CÓ THỂ DÁN ĐƯỜNG LINK GOOGLE SHEET / DRIVE CỦA FILE:")
            user_url = input("Dán link file tại đây (hoặc nhấn Enter để bỏ qua): ").strip()
            if user_url:
                if "docs.google.com/spreadsheets" in user_url:
                    import re
                    match = re.search(r"/d/([a-zA-Z0-9-_]+)", user_url)
                    if match:
                        sheet_id = match.group(1)
                        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                        df = pd.read_csv(csv_url)
                        display_dataframe(df, "Dữ liệu Google Sheet 'Thông tin'")
                        return
                df = pd.read_excel(user_url)
                display_dataframe(df, "Dữ liệu Excel")
                return
        except Exception as e:
            print(f"❌ Không thể tải từ đường link: {e}")
        return
    elif status == "OK" and service:
        search_and_read_from_gdrive(service)
    else:
        print("❌ Không thể khởi tạo kết nối Google Drive.")


if __name__ == "__main__":
    main()
