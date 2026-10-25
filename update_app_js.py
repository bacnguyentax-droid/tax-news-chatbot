import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

file_path = "tiktok_pipeline_app/static/js/app.js"
with open(file_path, "r", encoding="utf-8") as f:
    js = f.read()

# 1. Update sidebarTriggerAction to handle 'tiktok'
old_action_block = """    if (actionType === 'content') {
        setTimeout(() => {
            triggerGenerateContent();
        }, 150);
    } else if (actionType === 'slides') {
        setTimeout(() => {
            triggerGenerateSlides();
        }, 150);
    }
}"""

new_action_block = """    if (actionType === 'content') {
        setTimeout(() => {
            triggerGenerateContent();
        }, 150);
    } else if (actionType === 'slides') {
        setTimeout(() => {
            triggerGenerateSlides();
        }, 150);
    } else if (actionType === 'tiktok' || actionType === 'publish') {
        setTimeout(() => {
            triggerPublishTikTok();
        }, 150);
    }
}"""

js_norm = js.replace("\r\n", "\n")
old_block_norm = old_action_block.replace("\r\n", "\n")
new_block_norm = new_action_block.replace("\r\n", "\n")

if old_block_norm in js_norm:
    js_norm = js_norm.replace(old_block_norm, new_block_norm, 1)
    print("SUCCESS: Updated sidebarTriggerAction!")
else:
    print("ERROR: old_action_block not found in app.js")

# 2. Append TikTok publish functions to end of app.js
tiktok_functions = """

// =========================================================
// TIKTOK PUBLISHING LOGIC (ẢNH CUỘN & CHỈ MÌNH TÔI)
// =========================================================
async function triggerPublishTikTok() {
    if (currentRowIndex < 0 || !tableData[currentRowIndex]) {
        showToast('Vui lòng chọn một dòng chủ đề để đăng lên TikTok!', 'warning');
        return;
    }

    const row = tableData[currentRowIndex];
    const topic = row['Chủ đề'] || 'Chủ đề hiện tại';
    const stt = row['STT'] || (currentRowIndex + 1);

    // Thu thập dữ liệu form hiện tại
    const currentFields = collectFormData();

    // Hiển thị trạng thái đang xử lý
    showToast(`Đang quét thư mục ảnh cuộn và chuẩn bị đăng chủ đề "${topic}" lên TikTok...`, 'info', 4000);

    const btnDang = document.getElementById('menuItemDangTikTok');
    if (btnDang) {
        btnDang.classList.add('opacity-70', 'pointer-events-none');
    }

    try {
        const resp = await fetch('/api/tiktok/publish-carousel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                row_index: currentRowIndex,
                fields: currentFields
            })
        });

        const res = await resp.json();
        if (res.success) {
            showToast(res.message, 'success', 5000);

            // Tự động tích chọn checkbox Duyệt đăng và Đăng bài trên giao diện
            const cbDuyetDang = document.getElementById('field_DuyetDang');
            const cbDangBai = document.getElementById('field_DangBai');
            if (cbDuyetDang) cbDuyetDang.checked = true;
            if (cbDangBai) cbDangBai.checked = true;

            // Nạp lại dữ liệu bảng từ Google Drive để đồng bộ hiển thị
            if (typeof loadData === 'function') {
                loadData();
            }

            // Mở modal hiển thị kết quả xuất bản TikTok
            openTikTokPublishModal(res.data);
        } else {
            showToast(res.message || 'Không thể đăng lên TikTok!', 'error', 6000);
        }
    } catch (err) {
        console.error('Lỗi đăng TikTok:', err);
        showToast('Lỗi kết nối khi đăng lên TikTok: ' + err.message, 'error', 5000);
    } finally {
        if (btnDang) {
            btnDang.classList.remove('opacity-70', 'pointer-events-none');
        }
    }
}

function openTikTokPublishModal(data) {
    if (!data) return;
    const modal = document.getElementById('tiktokPublishModal');
    if (!modal) return;

    // Điền thông tin metadata
    const elAccount = document.getElementById('ttPubAccount');
    const elTime = document.getElementById('ttPubTime');
    const elCaption = document.getElementById('ttPubCaption');
    const elCount = document.getElementById('ttPubSlideCount');
    const elId = document.getElementById('ttPubId');
    const elLink = document.getElementById('ttPubOpenLink');

    if (elAccount) elAccount.textContent = data.target_account || '@thong_tin_ve_thue';
    if (elTime) elTime.textContent = data.published_at || new Date().toLocaleString('vi-VN');
    if (elCaption) elCaption.textContent = data.caption || data.chu_de || '';
    if (elCount) elCount.textContent = `(${data.image_count || 0} ảnh cuộn)`;
    if (elId) elId.textContent = data.publish_id || 'tt_pub_ready';
    if (elLink) elLink.href = data.post_url || `https://www.tiktok.com/${data.target_account || '@thong_tin_ve_thue'}`;

    // Render danh sách ảnh thumbnail
    const container = document.getElementById('ttPubSlidesContainer');
    if (container) {
        container.innerHTML = '';
        const files = data.media_files || [];
        if (files.length === 0) {
            container.innerHTML = '<div class="col-span-6 text-center text-slate-400 py-6 text-xs">Không có hình ảnh để hiển thị</div>';
        } else {
            files.forEach((f, idx) => {
                const card = document.createElement('div');
                card.className = 'group relative rounded-xl overflow-hidden border border-[#e3e7f0] bg-black aspect-[9/16] shadow-2xs hover:border-[#df8a5a] transition cursor-pointer';
                card.onclick = () => {
                    if (typeof openImageLightbox === 'function') {
                        openImageLightbox(f.url, `Slide ${f.index || idx + 1}: ${f.filename}`);
                    }
                };
                card.innerHTML = `
                    <img src="${f.url}" alt="${f.filename}" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                    <div class="absolute inset-x-0 bottom-0 p-1.5 bg-gradient-to-t from-black/80 via-black/40 to-transparent flex items-center justify-between">
                        <span class="text-[9px] font-bold text-white font-mono bg-black/60 px-1.5 py-0.5 rounded">#${f.index || idx + 1}</span>
                        <span class="text-[8px] text-amber-300 font-bold"><i class="fa-solid fa-expand"></i></span>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    }

    modal.classList.remove('hidden');
}

function closeTikTokPublishModal() {
    const modal = document.getElementById('tiktokPublishModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}
"""

js_norm += tiktok_functions

with open(file_path, "w", encoding="utf-8") as f:
    f.write(js_norm.replace("\n", "\r\n"))

print("SUCCESS: Finished updating app.js!")
