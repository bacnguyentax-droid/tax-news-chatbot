import json
import os
import sys

# Add directory to sys.path so we can import slide_generator_service
sys.path.insert(0, os.path.abspath("tiktok_pipeline_app"))

from slide_generator_service import generate_slide_image

presets_file = "tiktok_pipeline_app/carousel_presets.json"
out_dir = "tiktok_pipeline_app/static/images/presets"
os.makedirs(out_dir, exist_ok=True)

with open(presets_file, "r", encoding="utf-8") as f:
    presets = json.load(f)

print(f"Loaded {len(presets)} presets.")

sample_slide = {
    "slide_num": 1,
    "slide_type": "HOOK / TỔNG QUAN",
    "title": "CHÍNH SÁCH THUẾ MỚI\nÁP DỤNG TỪ 2026",
    "bullets": [
        "Toàn bộ quy định then chốt doanh nghiệp & hộ cá nhân cần nắm vững.",
        "Mức giảm trừ gia cảnh mới và lộ trình áp dụng cụ thể từ quý I/2026.",
        "Quy định chuyển tiếp thuế GTGT và hóa đơn điện tử khởi tạo từ máy tính tiền.",
        "Các trường hợp được miễn, hoãn và chính sách ưu đãi ngành nghề trọng điểm."
    ]
}

for i, p in enumerate(presets, 1):
    pid = p["id"]
    pname = p["name"]
    out_path = os.path.join(out_dir, f"{pid}.jpg")
    
    # Generate slide image using the preset design
    img = generate_slide_image(
        slide_info=sample_slide,
        chu_de="CHÍNH SÁCH THUẾ 2026",
        preset=p,
        total_slides=5
    )
    
    # Resize to high quality preview thumbnail (e.g. 540x675 or full 1080x1350)
    # Keeping 540x675 makes loading fast in UI while retaining razor-sharp text
    thumb = img.resize((540, 675))
    thumb.save(out_path, "JPEG", quality=90)
    print(f"[{i:02d}/20] Rendered {pid} -> {out_path}")

print("All 20 presets rendered successfully!")
