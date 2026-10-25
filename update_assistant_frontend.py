import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Update index.html
html_path = "tiktok_pipeline_app/templates/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

target_grid = """                <!-- Meta Info Pill Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                        <div class="text-slate-400 font-medium text-[10px]">Kênh đích phát hành</div>
                        <div id="ttPubAccount" class="font-bold text-slate-800 font-mono mt-0.5">@thong_tin_ve_thue</div>
                    </div>
                    <div class="p-3 bg-[#fdf4ee] rounded-xl border border-[#f5d5c5] text-xs">
                        <div class="text-slate-500 font-medium text-[10px]">Định dạng & Chế độ</div>
                        <div class="font-bold text-[#df8a5a] mt-0.5 flex items-center gap-1.5">
                            <i class="fa-solid fa-images"></i>
                            <span>Ảnh cuộn (Photo) • Chỉ mình tôi</span>
                        </div>
                    </div>
                    <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs">
                        <div class="text-emerald-600 font-medium text-[10px]">Google Sheet Cột L & K</div>
                        <div class="font-bold text-emerald-700 mt-0.5 flex items-center gap-1">
                            <i class="fa-solid fa-check-circle"></i>
                            <span>Đã tích chọn Duyệt & Đăng bài</span>
                        </div>
                    </div>
                </div>"""

new_grid_with_banner = """                <!-- Meta Info Pill Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                        <div class="text-slate-400 font-medium text-[10px]">Kênh đích phát hành</div>
                        <div id="ttPubAccount" class="font-bold text-slate-800 font-mono mt-0.5">@thong_tin_ve_thue</div>
                    </div>
                    <div class="p-3 bg-[#fdf4ee] rounded-xl border border-[#f5d5c5] text-xs">
                        <div class="text-slate-500 font-medium text-[10px]">Định dạng & Chế độ</div>
                        <div class="font-bold text-[#df8a5a] mt-0.5 flex items-center gap-1.5">
                            <i class="fa-solid fa-images"></i>
                            <span>Ảnh cuộn (Photo) • Chỉ mình tôi</span>
                        </div>
                    </div>
                    <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs">
                        <div class="text-emerald-600 font-medium text-[10px]">Google Sheet Cột L & K</div>
                        <div class="font-bold text-emerald-700 mt-0.5 flex items-center gap-1">
                            <i class="fa-solid fa-check-circle"></i>
                            <span>Đã tích chọn Duyệt & Đăng bài</span>
                        </div>
                    </div>
                </div>

                <!-- Status & Action Banner -->
                <div id="ttPubAuthNotice" class="p-4 bg-amber-50/90 border border-amber-200 rounded-2xl text-xs space-y-2.5">
                    <div class="flex items-center justify-between flex-wrap gap-2">
                        <div class="flex items-center gap-2 font-bold text-amber-900">
                            <i class="fa-solid fa-triangle-exclamation text-amber-600 text-sm"></i>
                            <span class="text-xs">Chưa có User Access Token TikTok — Hướng dẫn hoàn tất đăng thật:</span>
                        </div>
                        <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-200/70 text-amber-900 font-bold font-mono">Cần ủy quyền OAuth</span>
                    </div>
                    <p class="text-slate-600 leading-relaxed text-[11.5px]">
                        Hệ thống đã <strong>đóng gói hoàn chỉnh đủ bộ slide ảnh 9:16</strong> và <strong>kịch bản hashtag chuẩn SEO</strong>. Để bài đăng xuất hiện thật 100% trên kênh TikTok cá nhân của bạn, bấm nút dưới đây để trợ lý tự động copy Caption, mở thư mục ảnh và mở trang TikTok Studio:
                    </p>
                    <div class="flex items-center gap-3 pt-1 flex-wrap">
                        <button type="button" onclick="launchTikTokStudioAssistant()" class="btn-primary-mark py-2.5 px-5 text-xs font-bold shadow-md inline-flex items-center gap-2 cursor-pointer">
                            <i class="fa-solid fa-rocket"></i>
                            <span>Mở Thư Mục Ảnh & Đăng Thật Lên TikTok Ngay (1-Click)</span>
                        </button>
                        <span class="text-[11px] text-slate-500 italic">(Kéo thả 6 ảnh vào TikTok Studio, dán Caption, chọn "Chỉ mình tôi" và ấn Đăng)</span>
                    </div>
                </div>"""

target_footer = """                    <button type="button" onclick="closeTikTokPublishModal()" class="btn-outline-mark py-2 px-4 text-xs">
                        Đóng
                    </button>
                    <a id="ttPubOpenLink" href="https://www.tiktok.com/@thong_tin_ve_thue" target="_blank" class="btn-primary-mark py-2 px-4 text-xs inline-flex items-center gap-1.5">
                        <i class="fa-brands fa-tiktok"></i>
                        <span>Xem Trên TikTok</span>
                    </a>"""

new_footer = """                    <button type="button" onclick="closeTikTokPublishModal()" class="btn-outline-mark py-2 px-4 text-xs">
                        Đóng
                    </button>
                    <button type="button" onclick="launchTikTokStudioAssistant()" class="btn-primary-mark py-2 px-5 text-xs font-bold inline-flex items-center gap-2 cursor-pointer">
                        <i class="fa-brands fa-tiktok"></i>
                        <span>Đăng Thật Qua TikTok Studio (1-Click)</span>
                    </button>
                    <a id="ttPubOpenLink" href="https://www.tiktok.com/@thong_tin_ve_thue" target="_blank" class="btn-outline-mark py-2 px-3 text-xs inline-flex items-center gap-1 text-slate-600 hover:text-slate-900">
                        <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                        <span>Trang Kênh</span>
                    </a>"""

html_norm = html.replace("\r\n", "\n")
target_grid_norm = target_grid.replace("\r\n", "\n")
new_grid_norm = new_grid_with_banner.replace("\r\n", "\n")

if target_grid_norm in html_norm:
    html_norm = html_norm.replace(target_grid_norm, new_grid_norm, 1)
    print("SUCCESS: Added ttPubAuthNotice banner!")
else:
    print("ERROR: target_grid not found!")

target_footer_norm = target_footer.replace("\r\n", "\n")
new_footer_norm = new_footer.replace("\r\n", "\n")

if target_footer_norm in html_norm:
    html_norm = html_norm.replace(target_footer_norm, new_footer_norm, 1)
    print("SUCCESS: Updated modal footer buttons!")
else:
    print("ERROR: target_footer not found!")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_norm.replace("\n", "\r\n"))

print("SUCCESS: index.html updated!")

# 2. Update app.js
js_path = "tiktok_pipeline_app/static/js/app.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

assistant_js = """
let currentTikTokReceipt = null;

async function launchTikTokStudioAssistant() {
    if (!currentTikTokReceipt) {
        showToast('Không tìm thấy dữ liệu bài đăng!', 'warning');
        return;
    }

    showToast('Đang sao chép Caption, mở thư mục 6 slide ảnh và mở TikTok Studio...', 'info', 4000);

    try {
        const resp = await fetch('/api/tiktok/open-studio-assistant', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                stt: currentTikTokReceipt.stt || '1',
                chu_de: currentTikTokReceipt.chu_de || '',
                caption: currentTikTokReceipt.caption || ''
            })
        });
        const res = await resp.json();
        if (res.success) {
            showToast(res.message, 'success', 6000);
        } else {
            showToast(res.message || 'Lỗi mở trợ lý TikTok!', 'error', 5000);
            window.open('https://www.tiktok.com/tiktokstudio/upload', '_blank');
        }
    } catch (e) {
        console.error('Lỗi gọi trợ lý:', e);
        window.open('https://www.tiktok.com/tiktokstudio/upload', '_blank');
    }
}
"""

old_open_fn = """function openTikTokPublishModal(data) {
    if (!data) return;
    const modal = document.getElementById('tiktokPublishModal');
    if (!modal) return;"""

new_open_fn = """function openTikTokPublishModal(data) {
    if (!data) return;
    currentTikTokReceipt = data;
    const modal = document.getElementById('tiktokPublishModal');
    if (!modal) return;

    // Hiển thị banner trợ lý nếu chưa có live API token
    const banner = document.getElementById('ttPubAuthNotice');
    if (banner) {
        if (data.is_live_api_sent) {
            banner.classList.add('hidden');
        } else {
            banner.classList.remove('hidden');
        }
    }"""

js_norm = js.replace("\r\n", "\n")
old_open_norm = old_open_fn.replace("\r\n", "\n")
new_open_norm = new_open_fn.replace("\r\n", "\n")

if old_open_norm in js_norm:
    js_norm = js_norm.replace(old_open_norm, new_open_norm, 1)
    js_norm = assistant_js + "\n\n" + js_norm
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_norm.replace("\n", "\r\n"))
    print("SUCCESS: app.js updated with launchTikTokStudioAssistant!")
else:
    print("ERROR: old_open_fn not found in app.js!")
