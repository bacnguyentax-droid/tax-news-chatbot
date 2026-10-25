import urllib.request
import re
import json
import sys
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

def extract_attachment_url(article_url: str) -> str:
    if not article_url or not article_url.startswith('http'):
        return ""
    # Encode spaces in URL
    clean_url = article_url.replace(" ", "%20")
    try:
        req = urllib.request.Request(clean_url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as res:
            html = res.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for "Tải file đính kèm" or "Tải về" or link with pdf/doc
        for a in soup.find_all('a'):
            t = a.get_text(strip=True).lower()
            h = a.get('href', '')
            if ('tải file đính kèm' in t or 'tải về' in t or 'đính kèm' in t) and h:
                if h.startswith('/'):
                    return f"https://www.gdt.gov.vn{h}"
                elif h.startswith('http'):
                    return h
                else:
                    return f"https://www.gdt.gov.vn/wps/portal/{h}"

        for a in soup.find_all('a'):
            h = a.get('href', '')
            if any(ext in h.lower() for ext in ['.pdf', '.doc', '.docx', '.zip']):
                if h.startswith('/'):
                    return f"https://www.gdt.gov.vn{h}"
                elif h.startswith('http'):
                    return h
    except Exception as e:
        pass
    return ""

# Test on 7163 and a few others
test_urls = [
    "https://www.gdt.gov.vn/wps/portal?1dmy&mapping=home/documents/detail&urile=wcm%3apath%3a/GDT%20Content/sa_gdt/sa_vanban/vbhd/vbhd_tct/09-2026/d12680b4-8b09-4f17-afd4-a206aa4148e6",
    "https://www.gdt.gov.vn/wps/portal?1dmy&mapping=home/documents/detail&urile=wcm%3apath%3a/GDT%20Content/sa_gdt/sa_vanban/vbhd/vbhd_tct/10-2026/1d2c43de-3d7e-4076-94d7-9560fd5c5bba" # 7815
]

for u in test_urls:
    att = extract_attachment_url(u)
    print(f"URL: {u[:60]}... -> Attachment: {att}")
