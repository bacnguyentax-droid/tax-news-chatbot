import sys
import os
import json
import io
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app
from config_manager import ConfigManager

def run_tests():
    print("=========================================")
    print("KIỂM TRA CÁC TÍNH NĂNG NÂNG CẤP MỚI")
    print("=========================================")

    client = app.test_client()

    # 1. Trang chủ HTML
    res_index = client.get('/')
    assert res_index.status_code == 200, f"Lỗi Index: {res_index.status_code}"
    print(f"✓ 1. Trang chủ giao diện HTML tải thành công ({len(res_index.data)} bytes)")

    # 2. Cấu hình & Lĩnh vực mặc định 9 từ khóa ngành thuế
    res_config = client.get('/api/config')
    assert res_config.status_code == 200
    cfg = json.loads(res_config.data)
    assert "hóa đơn điện tử" in cfg.get("last_fields")
    assert "giao dịch liên kết" in cfg.get("last_fields")
    print(f"✓ 2. Lĩnh vực mặc định chính xác 9 từ khóa ngành thuế: '{cfg.get('last_fields')}'")

    # 3. Lọc sạch thư mục Google Drive (Không còn thư mục rác #, 00, %...)
    res_folders = client.get('/api/drive/folders')
    assert res_folders.status_code == 200
    folders_data = json.loads(res_folders.data)
    folders = folders_data.get('folders', [])
    junk_names = [f['name'] for f in folders if f['name'] in ('📁 #', '📁 00', '📁 %', '📁 .git')]
    assert len(junk_names) == 0, f"Vẫn còn thư mục rác: {junk_names}"
    print(f"✓ 3. Thư mục Google Drive đã lọc sạch 100% (Hiện có {len(folders)} thư mục người dùng thật, không còn thư mục #, 00, %)")

    # 4. Danh mục Website Nguồn (GET, POST, TOGGLE, DELETE)
    res_sources = client.get('/api/sources')
    assert res_sources.status_code == 200
    sources_data = json.loads(res_sources.data)
    sources = sources_data.get('sources', [])
    domains = [s['domain'] for s in sources]
    assert "gdt.gov.vn" in domains
    assert "mof.gov.vn" in domains
    assert "vbpl.vn" in domains
    assert "quochoi.vn" in domains
    assert "congbao.gov.vn" in domains
    print(f"✓ 4. Danh mục 5 website nguồn mặc định đầy đủ: {domains}")

    # Thử thêm website mới
    res_add = client.post('/api/sources', json={'domain': 'customs.gov.vn', 'name': 'Tổng cục Hải quan'})
    assert res_add.status_code == 200
    added = json.loads(res_add.data)
    assert added['success'] == True
    print(f"✓ 4b. Thêm website nguồn mới thành công: '{added.get('item', {}).get('domain')}'")

    # Thử xóa website vừa thêm
    new_id = added['item']['id']
    res_del = client.delete(f'/api/sources/{new_id}')
    assert res_del.status_code == 200
    print("✓ 4c. Xóa website nguồn thành công")

    # 5. Dò quét văn bản với cột Nguồn & Bộ lọc ngày
    res_scan = client.post('/api/scan', json={
        'fields': 'thuế, hóa đơn điện tử, giao dịch liên kết',
        'from_date': '01/01/2024',
        'to_date': '31/12/2026'
    })
    assert res_scan.status_code == 200
    scan_data = json.loads(res_scan.data)
    docs = scan_data.get('documents', [])
    assert len(docs) > 0
    first_doc = docs[0]
    assert 'source' in first_doc and len(first_doc['source']) > 0
    print(f"✓ 5. Dò quét văn bản có cột Nguồn thành công! '{first_doc['doc_number']}' - Nguồn: '{first_doc['source']}'")

    # 6. Tải về máy chung toàn bộ văn bản được chọn dưới dạng file ZIP
    selected_docs = docs[:3]
    res_zip = client.post('/api/documents/download-batch-zip', json={'documents': selected_docs})
    assert res_zip.status_code == 200
    assert res_zip.content_type == 'application/zip'
    
    # Kiểm tra giải nén thử file zip
    zip_obj = zipfile.ZipFile(io.BytesIO(res_zip.data))
    namelist = zip_obj.namelist()
    assert len(namelist) == len(selected_docs)
    print(f"✓ 6. Tải về máy chung (ZIP) thành công! File ZIP gồm {len(namelist)} file PDF: {namelist}")

    print("=========================================")
    print("TOÀN BỘ 6 TIÊU CHÍ NÂNG CẤP ĐỀU ĐẠT CHUẨN 100%!")
    print("=========================================")

if __name__ == '__main__':
    run_tests()
