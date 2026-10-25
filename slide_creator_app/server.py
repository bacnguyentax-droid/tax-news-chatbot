#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Web Server & Desktop Launcher cho Trình Tạo Slide Infographic
Tự động mở trình duyệt và phục vụ giao diện ứng dụng
"""

import os
import sys
import json
import webbrowser
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8520
APP_DIR = os.path.dirname(os.path.abspath(__file__))

class SlideServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def do_POST(self):
        if self.path == "/api/generate_python":
            # API gọi trực tiếp script Pillow nếu muốn
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_len).decode('utf-8')
                data = json.loads(post_body)
                
                from generate_slide_cli import create_slide_image
                out_name = f"slide_gen_{data.get('slideNum', 1)}.png"
                out_path = os.path.join(APP_DIR, out_name)
                
                create_slide_image(
                    header_tag=data.get("headerTag", ""),
                    title=data.get("title", ""),
                    bullets=data.get("bullets", []),
                    footer_tag=data.get("footerTag", ""),
                    output_path=out_path
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "file": out_name}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server = HTTPServer(("127.0.0.1", PORT), SlideServerHandler)
    url = f"http://localhost:{PORT}"
    print("=" * 60)
    print("🚀 TRÌNH TẠO ẢNH SLIDE & INFOGRAPHIC ĐÃ KHỞI ĐỘNG THÀNH CÔNG!")
    print(f"👉 Truy cập giao diện tại: {url}")
    print("=" * 60)
    print("Nhấn Ctrl + C để dừng máy chủ.")
    
    # Mở trình duyệt sau 0.8 giây
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng máy chủ.")
        server.server_close()

if __name__ == "__main__":
    run_server()
