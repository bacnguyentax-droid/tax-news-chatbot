import sqlite3, sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

db_path = r'C:\Users\ADMIN\AppData\Local\Google\DriveFS\101322887468073177531\metadata_sqlite_db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT item_stable_id, value FROM item_properties WHERE key='local-title'")
rows = c.fetchall()
print(f'Total items with local-title: {len(rows)}')
for item_id, title in rows:
    if isinstance(title, bytes):
        try:
            title_str = title.decode('utf-8')
        except:
            title_str = str(title)
    else:
        title_str = str(title)
    if any(k in title_str.lower() for k in ['xây dựng', 'xay dung', 'tạo video', 'tao video', 'video', 'thông tin', 'thong tin', 'excel']):
        print(f'Item {item_id}: {title_str}')
