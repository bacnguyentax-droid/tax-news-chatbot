// TikTok Studio - Pipeline Client Controller



let tableData = [];



let tableColumns = [];



let currentRowIndex = 0;



let isDriveConnected = false;



document.addEventListener("DOMContentLoaded", async () => {



    await fetchStatus();



    await loadTableData();



    await checkAiConfigStatus();



    await loadIntegrationsStatus();



    const savedTab = localStorage.getItem("activeTab") || "content";



    switchTab(savedTab);



});



// Toast notification helper



function showToast(message, type = "success") {



    const container = document.getElementById("toastContainer");



    if (!container) return;



    const toast = document.createElement("div");



    toast.className = `toast pointer-events-auto px-4 py-3 rounded-2xl shadow-lg text-xs font-bold flex items-center space-x-2.5 border transition-all ${



        type === "success" 



            ? "bg-white border-emerald-200 text-emerald-800" 



            : type === "error"



            ? "bg-white border-rose-200 text-rose-800"



            : "bg-white border-[#f5d5c5] text-[#df8a5a]"



    }`;



    const icon = type === "success" ? "fa-circle-check text-emerald-600" : type === "error" ? "fa-circle-exclamation text-rose-600" : "fa-circle-info text-[#df8a5a]";



    toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;



    container.appendChild(toast);



    setTimeout(() => {



        toast.style.opacity = "0";



        toast.style.transform = "translateY(10px)";



        toast.style.transition = "all 0.3s ease";



        setTimeout(() => toast.remove(), 300);



    }, 3500);



}



// Helper chọn giá trị dropdown thông minh (bỏ qua số thứ tự 1., 2. nếu có)



function setSelectSmart(selectId, rawVal) {



    const el = document.getElementById(selectId);



    if (!el) return;



    const v = String(rawVal || "").trim();



    if (!v) {



        el.value = "";



        return;



    }



    // 1. Khớp chính xác



    el.value = v;



    if (el.value === v) return;



    // 2. Chuẩn hóa chuỗi và so khớp



    const norm = (s) => s.toLowerCase().replace(/^(giá\s*trị\s*)?[0-9]+[.\s:là-]*/i, '').trim();



    const vNorm = norm(v);



    for (let opt of el.options) {



        if (norm(opt.value) === vNorm || norm(opt.text) === vNorm) {



            el.value = opt.value;



            return;



        }



    }



    // 3. Nếu giá trị tùy chỉnh chưa có trong danh sách



    const newOpt = document.createElement("option");



    newOpt.value = v;



    newOpt.text = v;



    newOpt.selected = true;



    el.appendChild(newOpt);



}



// 1. Kiểm tra trạng thái Google Drive



async function fetchStatus() {



    try {



        const res = await fetch("/api/status");



        const data = await res.json();



        



        isDriveConnected = data.is_connected;



        const dot = document.getElementById("driveStatusDot");



        const text = document.getElementById("driveStatusText");



        const modalMsg = document.getElementById("modalStatusMessage");



        const fileNameEl = document.getElementById("currentFileName");



        if (data.is_connected) {



            dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-emerald-200";



            text.textContent = data.user_email ? `Drive: ${data.user_email}` : "Đã kết nối Google Drive";



            text.className = "text-[#0f5132] font-semibold";



            if (modalMsg) modalMsg.innerHTML = `<span class="text-[#0f5132] font-bold">✅ Đã kết nối với Google Drive!</span><br><span class="text-[#495057]">File: ${data.file_name} (${data.file_type})</span>`;



            if (fileNameEl) fileNameEl.textContent = data.file_name || "Thông tin";



            // Tự động load dữ liệu nếu bảng đang trống nhưng server đã có kết nối Drive



            if (tableData.length === 0 && data.total_rows > 0) {



                await loadTableData();



            }



        } else {



            dot.className = "w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse";



            text.textContent = "Chưa kết nối Google Drive";



            text.className = "text-amber-800 font-semibold";



            if (modalMsg) modalMsg.innerHTML = `<span class="text-amber-800 font-bold">⚠️ Chưa kết nối trực tiếp Google Drive Cloud.</span><br><span class="text-[#495057]">${data.connection_message}</span>`;



            if (fileNameEl) fileNameEl.textContent = "Chưa kết nối";



        }



    } catch (e) {



        console.error("Lỗi fetch status:", e);



    }



}



// 2. Nạp dữ liệu bảng tính



async function loadTableData() {



    try {



        const res = await fetch("/api/data");



        const data = await res.json();



        if (data.success) {



            tableData = data.rows || [];



            tableColumns = data.columns || [];



            document.getElementById("totalRowsCount").textContent = tableData.length;



            renderTable(tableData);



            if (tableData.length > 0) {



                // Tự động chọn dòng đầu tiên



                selectRow(0);



            } else {



                clearEditForm();



            }



        } else {



            showToast("Không thể nạp dữ liệu: " + data.message, "error");



        }



    } catch (e) {



        console.error("Lỗi loadTableData:", e);



        showToast("Lỗi khi tải dữ liệu từ máy chủ", "error");



    }



}



// 3. Render bảng dữ liệu



function renderTable(rows) {



    const tbody = document.getElementById("tableBody");



    if (!tbody) return;



    if (!rows || rows.length === 0) {



        if (!isDriveConnected) {



            tbody.innerHTML = `



                <tr>



                    <td colspan="12" class="py-14 text-center text-[#6b7588]">



                        <div class="max-w-md mx-auto space-y-4">



                            <div class="icon-3d mx-auto">



                                <i class="fa-brands fa-google-drive"></i>



                            </div>



                            <h3 class="text-base font-extrabold text-[#282d38]">Chưa kết nối Google Drive</h3>



                            <p class="text-xs text-[#6b7588] leading-relaxed">



                                Không có dữ liệu hiển thị. Vui lòng kết nối tài khoản Google Drive để tải danh sách chủ đề video thực tế từ thư mục:



                                <br><span class="font-mono text-[#df8a5a] bg-[#fdf4ee] px-3 py-1 rounded-full text-xs font-semibold border border-[#f5d5c5] inline-block mt-2">_____Xây dựng video_____ / Tạo video / Thông tin</span>



                            </p>



                            <button onclick="openDriveConfigModal()" class="btn-primary-mark text-xs inline-flex items-center space-x-2">



                                <i class="fa-solid fa-plug text-xs"></i>



                                <span>Kết Nối Google Drive Ngay</span>



                            </button>



                        </div>



                    </td>



                </tr>



            `;



        } else {



            tbody.innerHTML = `



                <tr>



                    <td colspan="12" class="py-12 text-center text-[#6b7588]">



                        <div class="icon-3d mx-auto mb-3">



                            <i class="fa-regular fa-folder-open"></i>



                        </div>



                        <p class="text-sm text-[#282d38] font-bold">File 'Thông tin' trên Google Drive hiện chưa có dòng dữ liệu nào.</p>



                        <p class="text-xs text-[#6b7588] mt-1">Bấm 'Thêm Dòng Mới' để bắt đầu thêm chủ đề video đầu tiên.</p>



                        <button onclick="addNewRowPrompt()" class="mt-3 btn-primary-mark text-xs inline-flex items-center space-x-2">



                            <i class="fa-solid fa-plus text-xs"></i>



                            <span>Thêm dòng đầu tiên</span>



                        </button>



                    </td>



                </tr>



            `;



        }



        return;



    }



    tbody.innerHTML = rows.map((row, index) => {



        const isSelected = index === currentRowIndex;



        



        // Helper badge render cho dấu 'x'



        const badge = (val) => {



            const isX = String(val).trim().toLowerCase() === 'x';



            return isX 



                ? `<span class="status-badge-active" title="Đã duyệt/hoàn thành"><i class="fa-solid fa-check"></i></span>`



                : `<span class="status-badge-empty" title="Chưa xong">-</span>`;



        };



        const stt = row["STT"] || (index + 1);



        const chuDe = row["Chủ đề"] || "(Chưa có chủ đề)";



        const yeuCauChuDe = row["Yêu cầu chủ đề"] || "";



        const noiDung = row["Nội dung"] || "";



        const noiDungPreview = noiDung.replace(/\r?\n+/g, ' ').trim();



        const escapeAttr = (s) => String(s || "").replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');



        const hagTag = row["Hag tag"] || row["Hashtag"] || "";



        const loaiVideo = row["Loại video"] || "";



        const dangVideo = row["Dạng video"] || "";



        const duyetCDHT = row["duyệt CĐ và HT"] || row["Duyệt CĐ"] || "";



        return `



            <tr onclick="selectRow(${index})" 



                id="row-${index}" 



                class="cursor-pointer hover:bg-[#fdf6f2] transition-colors border-b border-[#e3e7f0] ${isSelected ? 'selected-row' : ''}">



                <td class="py-3 px-3 text-center font-mono text-[#6b7588] font-bold">${stt}</td>



                <td class="py-3 px-3 font-extrabold text-[#282d38] max-w-[200px] truncate" title="${escapeAttr(chuDe)}">



                    ${chuDe}



                </td>



                <td class="py-3 px-3 text-[#df8a5a] font-semibold max-w-[220px] truncate" title="${escapeAttr(yeuCauChuDe)}">



                    ${yeuCauChuDe || '<span class="text-[#a4a7c5] italic font-normal">Trống</span>'}



                </td>



                <td class="py-3 px-3 text-[#5c687e] max-w-[480px] min-w-[440px] whitespace-normal leading-relaxed text-[11.5px] line-clamp-3" title="${escapeAttr(noiDungPreview)}">



                    ${noiDungPreview || '<span class="text-[#a4a7c5] italic font-normal">Trống</span>'}



                </td>



                <td class="py-3 px-3 text-[#6b7588] text-[11px] max-w-[140px] truncate" title="${escapeAttr(hagTag)}">



                    ${hagTag || '<span class="text-[#a4a7c5]">-</span>'}



                </td>



                <td class="py-3 px-3">



                    ${loaiVideo ? `<span class="px-2.5 py-0.5 rounded-full bg-[#fdf4ee] text-[#df8a5a] border border-[#f5d5c5] text-[11px] font-bold truncate inline-block max-w-[130px]">${loaiVideo}</span>` : '<span class="text-[#a4a7c5]">-</span>'}



                </td>



                <td class="py-3 px-3">



                    ${dangVideo ? `<span class="px-2.5 py-0.5 rounded-full bg-[#ffffff] text-[#5c687e] border border-[#e3e7f0] text-[11px] font-semibold truncate inline-block max-w-[150px]">${dangVideo}</span>` : '<span class="text-[#a4a7c5]">-</span>'}



                </td>



                <td class="py-3 px-2 text-center">${badge(duyetCDHT)}</td>



                <td class="py-3 px-2 text-center">${badge(row["Duyệt nội dung"])}</td>



                <td class="py-3 px-2 text-center">${badge(row["Tạo video"])}</td>



                <td class="py-3 px-2 text-center">${badge(row["Duyệt đăng"])}</td>



                <td class="py-3 px-2 text-center">${badge(row["Đăng bài"])}</td>



                <td class="py-3 px-3 text-center">



                    <button type="button" class="w-7 h-7 rounded-full bg-[#fdf4ee] hover:bg-[#df8a5a] text-[#df8a5a] hover:text-white transition inline-flex items-center justify-center text-xs" title="Xem & Chỉnh sửa">



                        <i class="fa-solid fa-pen-to-square"></i>



                    </button>



                </td>



            </tr>



        `;



    }).join("");



}



// 4. Khi người dùng click chọn 1 dòng



function selectRow(index) {



    if (index < 0 || index >= tableData.length) return;



    currentRowIndex = index;



    const row = tableData[index];



    // Cập nhật highlight trên bảng



    document.querySelectorAll("#tableBody tr").forEach((tr, idx) => {



        if (idx === index) {



            tr.classList.add("selected-row");



        } else {



            tr.classList.remove("selected-row");



        }



    });



    // Cập nhật thông tin tiêu đề form



    const stt = row["STT"] || (index + 1);



    document.getElementById("detailBadgeStt").textContent = `#${stt}`;



    document.getElementById("detailRowBadge").textContent = `Dòng #${index + 1}`;



    document.getElementById("editRowIndex").value = index;



    const aiLabel = document.getElementById("aiSelectedRowLabel");



    if (aiLabel) {



        aiLabel.textContent = `Dòng #${index + 1} (STT: ${stt})`;



    }



    // Cập nhật thẻ hồ sơ đang chọn ở chân Sidebar bên trái



    const sideRowBadge = document.getElementById("sideActiveRowBadge");



    const sideTopicText = document.getElementById("sideActiveTopicText");



    if (sideRowBadge) sideRowBadge.textContent = `Dòng #${index + 1}`;



    if (sideTopicText) {



        sideTopicText.textContent = row["Chủ đề"] || "(Chưa có chủ đề)";



        sideTopicText.title = row["Chủ đề"] || "";



    }



    // Điền dữ liệu vào form theo thứ tự Cột A -> Cột K



    document.getElementById("field_STT").value = stt;



    document.getElementById("field_ChuDe").value = row["Chủ đề"] || "";



    document.getElementById("field_YeuCauChuDe").value = row["Yêu cầu chủ đề"] || "";



    document.getElementById("field_NoiDung").value = row["Nội dung"] || "";



    document.getElementById("field_HagTag").value = row["Hag tag"] || row["Hashtag"] || "";



    setSelectSmart("field_LoaiVideo", row["Loại video"]);



    setSelectSmart("field_DangVideo", row["Dạng video"]);



    // Checkbox trạng thái (Cột H, I, J, K)



    const isChecked = (key, altKey = null) => {



        let val = row[key];



        if (!val && altKey) {



            val = row[altKey];



        }



        return String(val || "").trim().toLowerCase() === "x";



    };



    document.getElementById("field_DuyetCDHT").checked = isChecked("duyệt CĐ và HT", "Duyệt CĐ");



    const duyetNdEl = document.getElementById("field_DuyetNoiDung");



    if (duyetNdEl) duyetNdEl.checked = isChecked("Duyệt nội dung");



    document.getElementById("field_TaoVideo").checked = isChecked("Tạo video");



    document.getElementById("field_DuyetDang").checked = isChecked("Duyệt đăng");



    document.getElementById("field_DangBai").checked = isChecked("Đăng bài");



    if (typeof onDangVideoChange === "function") {



        onDangVideoChange();



    }



    // URLs mở rộng



    const audioEl = document.getElementById("field_AudioURL");



    if (audioEl) audioEl.value = row["Audio URL"] || "";



    const videoDraftEl = document.getElementById("field_VideoDraftURL");



    if (videoDraftEl) videoDraftEl.value = row["Video Draft URL"] || "";



    const tiktokEl = document.getElementById("field_TikTokURL");



    if (tiktokEl) tiktokEl.value = row["TikTok URL"] || "";



    updateCharCount();



}



function clearEditForm() {



    document.getElementById("detailBadgeStt").textContent = "#0";



    document.getElementById("detailRowBadge").textContent = "Không có dữ liệu";



    document.getElementById("editRowIndex").value = -1;



    const aiLabel = document.getElementById("aiSelectedRowLabel");



    if (aiLabel) {



        aiLabel.textContent = "Chưa chọn dòng";



    }



    document.getElementById("field_STT").value = "";



    document.getElementById("field_ChuDe").value = "";



    document.getElementById("field_YeuCauChuDe").value = "";



    document.getElementById("field_NoiDung").value = "";



    document.getElementById("field_HagTag").value = "";



    document.getElementById("field_LoaiVideo").value = "";



    document.getElementById("field_DangVideo").value = "";



    document.getElementById("field_DuyetCDHT").checked = false;



    const duyetNdElClear = document.getElementById("field_DuyetNoiDung");



    if (duyetNdElClear) duyetNdElClear.checked = false;



    document.getElementById("field_TaoVideo").checked = false;



    document.getElementById("field_DuyetDang").checked = false;



    document.getElementById("field_DangBai").checked = false;



    const audioEl = document.getElementById("field_AudioURL");



    if (audioEl) audioEl.value = "";



    const videoDraftEl = document.getElementById("field_VideoDraftURL");



    if (videoDraftEl) videoDraftEl.value = "";



    const tiktokEl = document.getElementById("field_TikTokURL");



    if (tiktokEl) tiktokEl.value = "";



    updateCharCount();



}



function updateCharCount() {



    const val = document.getElementById("field_NoiDung").value || "";



    const counter = document.getElementById("contentLengthHint");



    if (counter) counter.textContent = `${val.length} ký tự`;



}



// 5. Lưu cập nhật dòng vào file Google Drive / Excel



async function saveCurrentRow() {



    const index = parseInt(document.getElementById("editRowIndex").value);



    if (isNaN(index) || index < 0 || index >= tableData.length) {



        showToast("Vui lòng chọn dòng cần cập nhật trước!", "error");



        return;



    }



    const btn = document.getElementById("btnSaveRow");



    const originalText = btn.innerHTML;



    btn.disabled = true;



    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i>Đang lưu vào Drive...`;



    // Thu thập giá trị từ form theo đúng thứ tự file Thông tin (Cột A - Cột K)



    const updatedFields = {



        "STT": document.getElementById("field_STT").value,



        "Chủ đề": document.getElementById("field_ChuDe").value.trim(),



        "Yêu cầu chủ đề": document.getElementById("field_YeuCauChuDe").value.trim(),



        "Nội dung": document.getElementById("field_NoiDung").value.trim(),



        "Hag tag": document.getElementById("field_HagTag").value.trim(),



        "Loại video": document.getElementById("field_LoaiVideo").value,



        "Dạng video": document.getElementById("field_DangVideo").value,



        "duyệt CĐ và HT": document.getElementById("field_DuyetCDHT").checked ? "x" : "",



        "Duyệt nội dung": (document.getElementById("field_DuyetNoiDung") && document.getElementById("field_DuyetNoiDung").checked) ? "x" : "",



        "Tạo video": document.getElementById("field_TaoVideo").checked ? "x" : "",



        "Duyệt đăng": document.getElementById("field_DuyetDang").checked ? "x" : "",



        "Đăng bài": document.getElementById("field_DangBai").checked ? "x" : ""



    };



    const audioEl = document.getElementById("field_AudioURL");



    if (audioEl && audioEl.value.trim()) updatedFields["Audio URL"] = audioEl.value.trim();



    const videoDraftEl = document.getElementById("field_VideoDraftURL");



    if (videoDraftEl && videoDraftEl.value.trim()) updatedFields["Video Draft URL"] = videoDraftEl.value.trim();



    const tiktokEl = document.getElementById("field_TikTokURL");



    if (tiktokEl && tiktokEl.value.trim()) updatedFields["TikTok URL"] = tiktokEl.value.trim();



    try {



        const res = await fetch("/api/row/update", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({ index: index, fields: updatedFields })



        });



        const result = await res.json();



        if (result.success) {



            // Cập nhật lại bộ nhớ cache



            tableData[index] = { ...tableData[index], ...updatedFields };



            renderTable(tableData);



            selectRow(index);



            showToast(result.message || "Đã lưu thành công vào file Thông tin!", "success");



        } else {



            showToast("Lỗi khi lưu: " + result.message, "error");



        }



    } catch (e) {



        console.error("Lỗi khi save row:", e);



        showToast("Lỗi kết nối khi gửi dữ liệu lưu", "error");



    } finally {



        btn.disabled = false;



        btn.innerHTML = originalText;



    }



}



// 6. Thêm dòng mới



async function addNewRowPrompt() {



    const inputEl = document.getElementById("newTopicInput");



    let topic = inputEl ? inputEl.value.trim() : "";



    if (!topic) {



        if (inputEl) {



            inputEl.focus();



            inputEl.classList.add("ring-2", "ring-[#df8a5a]", "border-[#df8a5a]");



            setTimeout(() => {



                inputEl.classList.remove("ring-2", "ring-[#df8a5a]", "border-[#df8a5a]");



            }, 1800);



        }



        showToast("Vui lòng nhập tên chủ đề video vào ô bên cạnh trước khi bấm Thêm!", "warning");



        return;



    }



    try {



        const newRow = {



            "STT": tableData.length + 1,



            "Chủ đề": topic,



            "Yêu cầu chủ đề": "",



            "Nội dung": "",



            "Hag tag": "",



            "Loại video": "Góc cảnh báo",



            "Dạng video": "Ảnh cuộn",



            "duyệt CĐ và HT": "",



            "Tạo video": "",



            "Duyệt đăng": "",



            "Đăng bài": ""



        };



        const res = await fetch("/api/row/add", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({ fields: newRow })



        });



        const result = await res.json();



        if (result.success) {



            if (inputEl) {



                inputEl.value = "";



                inputEl.focus();



            }



            showToast(`Đã thêm chủ đề "${topic}" thành công!`, "success");



            await loadTableData();



            selectRow(tableData.length - 1);



        } else {



            showToast("Không thể thêm dòng: " + result.message, "error");



        }



    } catch (e) {



        showToast("Lỗi khi thêm dòng mới: " + e.message, "error");



    }



}



// 7. Xóa dòng



async function deleteCurrentRow() {



    const index = parseInt(document.getElementById("editRowIndex").value);



    if (isNaN(index) || index < 0 || index >= tableData.length) return;



    const chuDe = tableData[index]["Chủ đề"] || `Dòng #${index + 1}`;



    if (!confirm(`Bạn có chắc muốn xóa dòng:\n"${chuDe}" khỏi file Google Drive?`)) {



        return;



    }



    try {



        const res = await fetch("/api/row/delete", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({ index: index })



        });



        const result = await res.json();



        if (result.success) {



            showToast(result.message || "Đã xóa dòng!", "success");



            await loadTableData();



            if (tableData.length > 0) {



                selectRow(Math.max(0, index - 1));



            } else {



                clearEditForm();



            }



        } else {



            showToast("Lỗi khi xóa: " + result.message, "error");



        }



    } catch (e) {



        showToast("Lỗi khi xóa dòng", "error");



    }



}



// 8. Lọc & Tìm kiếm dữ liệu bảng



function filterTable() {



    const query = (document.getElementById("searchInput").value || "").toLowerCase().trim();



    const statusFilter = document.getElementById("filterStatus").value;



    const filtered = tableData.filter(row => {



        // Text match



        const matchText = !query || 



            (row["Chủ đề"] && row["Chủ đề"].toLowerCase().includes(query)) ||



            (row["Yêu cầu chủ đề"] && row["Yêu cầu chủ đề"].toLowerCase().includes(query)) ||



            (row["Nội dung"] && row["Nội dung"].toLowerCase().includes(query)) ||



            (row["Hag tag"] && row["Hag tag"].toLowerCase().includes(query)) ||



            (row["Hashtag"] && row["Hashtag"].toLowerCase().includes(query)) ||



            (row["Loại video"] && row["Loại video"].toLowerCase().includes(query)) ||



            (row["Dạng video"] && row["Dạng video"].toLowerCase().includes(query));



        if (!matchText) return false;



        // Status filter



        const isX = (key, alt = null) => {



            let v = row[key];



            if (!v && alt) v = row[alt];



            return String(v || "").toLowerCase().trim() === "x";



        };



        if (statusFilter === "all") return true;



        if (statusFilter === "duyet_cd_ht") return isX("duyệt CĐ và HT", "Duyệt CĐ");



        if (statusFilter === "chua_duyet_cd_ht") return !isX("duyệt CĐ và HT", "Duyệt CĐ");



        if (statusFilter === "duyet_noi_dung") return isX("Duyệt nội dung");



        if (statusFilter === "tao_video") return isX("Tạo video");



        if (statusFilter === "duyet_dang") return isX("Duyệt đăng");



        if (statusFilter === "dang_bai") return isX("Đăng bài");



        return true;



    });



    renderTable(filtered);



}



// 9. Đồng bộ lại từ Drive



async function reloadFromDrive() {



    const spinIcons = document.querySelectorAll(".reload-spin-icon, #reloadIcon");



    spinIcons.forEach(ic => ic.classList.add("fa-spin"));



    try {



        showToast("Đang đồng bộ nạp lại file Excel từ Google Sheets...", "info");



        const res = await fetch("/api/reload", { method: "POST" });



        const result = await res.json();



        if (result.success) {



            showToast(result.message || "Đã nạp lại file Excel từ Google Sheets thành công!", "success");



        } else {



            showToast(result.message || "Lỗi nạp lại Google Sheets", "error");



        }



        await fetchStatus();



        await loadTableData();



    } catch (e) {



        showToast("Lỗi kết nối khi đồng bộ lại: " + e.message, "error");



    } finally {



        spinIcons.forEach(ic => ic.classList.remove("fa-spin"));



    }



}



// 10. Mở link ngoài



function openLink(elementId) {



    const val = document.getElementById(elementId).value.trim();



    if (!val) {



        showToast("Trường liên kết này đang trống", "error");



        return;



    }



    window.open(val, "_blank");



}



// 11. Modal Cấu hình Drive



function openDriveConfigModal() {



    document.getElementById("driveConfigModal").classList.remove("hidden");



    fetchStatus();



}



function closeDriveConfigModal() {



    document.getElementById("driveConfigModal").classList.add("hidden");



}



// Upload credentials.json



async function uploadCredentials() {



    const input = document.getElementById("credentialsFileInput");



    if (!input.files || input.files.length === 0) {



        showToast("Vui lòng chọn file credentials.json trước", "error");



        return;



    }



    const formData = new FormData();



    formData.append("file", input.files[0]);



    try {



        const res = await fetch("/api/credentials/upload", {



            method: "POST",



            body: formData



        });



        const result = await res.json();



        if (result.success) {



            showToast(result.message, "success");



            fetchStatus();



        } else {



            showToast(result.message, "error");



        }



    } catch (e) {



        showToast("Lỗi tải lên credentials.json", "error");



    }



}



// Bắt đầu OAuth Login



async function startGoogleAuth() {



    const btn = document.getElementById("btnStartAuth");



    const originalHtml = btn ? btn.innerHTML : "";



    if (btn) {



        btn.disabled = true;



        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-base"></i><span>Đang chuẩn bị trang đăng nhập Google...</span>`;



    }



    try {



        const res = await fetch("/api/auth/start", { method: "POST" });



        const result = await res.json();



        



        if (result.success && result.auth_url) {



            showToast("Đang mở trang đăng nhập Google trên tab mới...", "info");



            



            // Mở tab Google OAuth đăng nhập trực tiếp



            window.open(result.auth_url, "_blank");



            // Tự động kiểm tra trạng thái xác thực mỗi 2 giây



            let checks = 0;



            const timer = setInterval(async () => {



                checks++;



                await fetchStatus();



                if (isDriveConnected) {



                    clearInterval(timer);



                    showToast("🎉 Kết nối Google Drive thành công!", "success");



                    await loadTableData();



                    closeDriveConfigModal();



                    if (btn) {



                        btn.disabled = false;



                        btn.innerHTML = originalHtml;



                    }



                }



                if (checks > 90) { // Quá 3 phút



                    clearInterval(timer);



                    if (btn) {



                        btn.disabled = false;



                        btn.innerHTML = originalHtml;



                    }



                }



            }, 2000);



        } else {



            showToast(result.message || "Không thể khởi động xác thực", "error");



            if (btn) {



                btn.disabled = false;



                btn.innerHTML = originalHtml;



            }



        }



    } catch (e) {



        console.error("Lỗi OAuth:", e);



        showToast("Lỗi kết nối khi kích hoạt xác thực", "error");



        if (btn) {



            btn.disabled = false;



            btn.innerHTML = originalHtml;



        }



    }



}



// Tự động tạo cây thư mục và file trên Drive



async function createDriveStructure() {



    try {



        showToast("Đang tạo cây thư mục '_____Xây dựng video_____ / Tạo video / Thông tin' trên Drive...", "info");



        const res = await fetch("/api/create_drive_structure", { method: "POST" });



        const result = await res.json();



        if (result.success) {



            showToast(result.message, "success");



            await fetchStatus();



            await loadTableData();



            closeDriveConfigModal();



        } else {



            showToast("Lỗi tạo thư mục: " + result.message, "error");



        }



    } catch (e) {



        showToast("Lỗi gửi yêu cầu tạo thư mục", "error");



    }



}



// ==========================================



// 12. DÃY CHỨC NĂNG TÁC NGHIỆP AI & GEMINI / NOTEBOOKLM



// ==========================================



// Kiểm tra trạng thái API Key Gemini



async function checkAiConfigStatus() {



    try {



        const res = await fetch("/api/ai/config");



        const data = await res.json();



        const badge = document.getElementById("aiConfigBadge");



        if (badge) {



            if (data.has_api_key) {



                badge.className = "w-2 h-2 rounded-full bg-emerald-500 ml-0.5";



                badge.title = "Gemini API đã sẵn sàng";



            } else {



                badge.className = "w-2 h-2 rounded-full bg-amber-500 animate-pulse ml-0.5";



                badge.title = "Chưa có Gemini API Key";



            }



        }



    } catch (e) {



        console.error("Lỗi kiểm tra cấu hình AI:", e);



    }



}



// Modal Cấu hình Gemini & NotebookLM



async function openAiConfigModal() {



    try {



        const res = await fetch("/api/ai/config");



        const cfg = await res.json();



        



        const keyInput = document.getElementById("cfg_geminiApiKey");



        if (keyInput) keyInput.value = cfg.api_key || "";



        



        const modelSelect = document.getElementById("cfg_geminiModel");



        if (modelSelect) modelSelect.value = cfg.model || "gemini-2.5-flash";



        



        const nbInput = document.getElementById("cfg_notebooklmName");



        if (nbInput) nbInput.value = cfg.notebooklm_name || "Tax_Nghiệp vụ thuế";



        



        const searchCheck = document.getElementById("cfg_enableWebSearch");



        if (searchCheck) searchCheck.checked = cfg.enable_web_search !== false;



        



        const customTax = document.getElementById("cfg_customTaxKnowledge");



        if (customTax) customTax.value = cfg.custom_tax_knowledge || "";



        



        const badge = document.getElementById("cfg_keyStatusBadge");



        if (badge) {



            if (cfg.has_api_key) {



                badge.textContent = "Đã nạp (" + (cfg.api_key_preview || "OK") + ")";



                badge.className = "text-[10px] text-emerald-700 font-mono font-semibold";



            } else {



                badge.textContent = "Chưa có Key";



                badge.className = "text-[10px] text-amber-700 font-mono font-semibold";



            }



        }



        document.getElementById("aiConfigModal").classList.remove("hidden");



    } catch (e) {



        showToast("Lỗi nạp cấu hình Gemini / NotebookLM", "error");



    }



}



function closeAiConfigModal() {



    document.getElementById("aiConfigModal").classList.add("hidden");



}



async function saveAiConfig() {



    const btn = document.getElementById("btnSaveAiConfig");



    const origHtml = btn ? btn.innerHTML : "";



    if (btn) {



        btn.disabled = true;



        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Đang lưu...</span>`;



    }



    const payload = {



        api_key: (document.getElementById("cfg_geminiApiKey").value || "").trim(),



        model: document.getElementById("cfg_geminiModel").value,



        notebooklm_name: (document.getElementById("cfg_notebooklmName").value || "").trim() || "Tax_Nghiệp vụ thuế",



        enable_web_search: document.getElementById("cfg_enableWebSearch").checked,



        custom_tax_knowledge: (document.getElementById("cfg_customTaxKnowledge").value || "").trim()



    };



    try {



        const res = await fetch("/api/ai/config", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify(payload)



        });



        const result = await res.json();



        if (result.success) {



            showToast(result.message || "Đã lưu cấu hình AI thành công!", "success");



            closeAiConfigModal();



            await checkAiConfigStatus();



        } else {



            showToast("Lỗi lưu cấu hình: " + (result.message || "Thất bại"), "error");



        }



    } catch (e) {



        showToast("Lỗi gửi yêu cầu lưu cấu hình", "error");



    } finally {



        if (btn) {



            btn.disabled = false;



            btn.innerHTML = origHtml;



        }



    }



}



// Modal Xem Kết quả Sinh Kịch bản Slide



function openAiResultModal(result) {



    const modal = document.getElementById("aiResultModal");



    if (!modal) return;



    const resFolderName = document.getElementById("resFolderName");



    const resFolderLink = document.getElementById("resFolderLink");



    const resDocLink = document.getElementById("resDocLink");



    const resSlideScript = document.getElementById("resSlideScript");



    if (resFolderName) resFolderName.textContent = result.folder_name || "Thư mục Drive";



    if (resFolderLink) {



        resFolderLink.href = result.folder_link || "#";



        if (!result.folder_link) resFolderLink.removeAttribute("target");



        else resFolderLink.setAttribute("target", "_blank");



    }



    if (resDocLink) {



        resDocLink.href = result.doc_link || "#";



        if (!result.doc_link) resDocLink.removeAttribute("target");



        else resDocLink.setAttribute("target", "_blank");



    }



    if (resSlideScript) {



        resSlideScript.textContent = result.slide_script || "";



    }



    modal.classList.remove("hidden");



}



function closeAiResultModal() {



    const modal = document.getElementById("aiResultModal");



    if (modal) modal.classList.add("hidden");



}



function copyAiScript() {



    const scriptEl = document.getElementById("resSlideScript");



    if (!scriptEl) return;



    const text = scriptEl.textContent;



    if (!text) {



        showToast("Chưa có nội dung kịch bản để sao chép", "error");



        return;



    }



    navigator.clipboard.writeText(text).then(() => {



        showToast("Đã sao chép kịch bản slide vào clipboard!", "success");



        const btnText = document.getElementById("btnCopyScriptText");



        if (btnText) {



            btnText.textContent = "Đã sao chép!";



            setTimeout(() => {



                btnText.textContent = "Sao chép kịch bản";



            }, 2500);



        }



    }).catch(err => {



        showToast("Không thể sao chép tự động: " + err, "error");



    });



}



// Chức năng Tạo nội dung (Kịch bản Slide TikTok 9:16)



async function triggerGenerateContent() {



    if (currentRowIndex < 0 || currentRowIndex >= tableData.length) {



        showToast("Vui lòng click chọn một dòng dữ liệu trên bảng trước!", "error");



        return;



    }



    const chuDe = (document.getElementById("field_ChuDe").value || "").trim();



    if (!chuDe) {



        showToast("Dòng này chưa có 'Chủ đề'. Vui lòng nhập chủ đề trước khi tạo nội dung!", "error");



        return;



    }



    let loaiVideo = (document.getElementById("field_LoaiVideo").value || "").trim();



    let dangVideo = (document.getElementById("field_DangVideo").value || "").trim();



    // Điều kiện: Dạng video là Ảnh cuộn và Loại video là Chính sách thuế



    const isChinhSachThue = loaiVideo.includes("Chính sách thuế");



    const isAnhCuon = dangVideo.includes("Ảnh cuộn");



    if (!isChinhSachThue || !isAnhCuon) {



        const confirmChange = confirm(



            "Chức năng 'Tạo nội dung' áp dụng cho:\n" +



            "• Dạng video: Ảnh cuộn\n" +



            "• Loại video: Chính sách thuế\n\n" +



            "Bạn có muốn hệ thống tự động gán Loại video = 'Chính sách thuế' và Dạng video = 'Ảnh cuộn' cho dòng này để tiếp tục không?"



        );



        if (!confirmChange) return;



        setSelectSmart("field_LoaiVideo", "Chính sách thuế");



        setSelectSmart("field_DangVideo", "Ảnh cuộn");



        loaiVideo = "Chính sách thuế";



        dangVideo = "Ảnh cuộn";



    }



    const btn = document.getElementById("btnGenerateContent");



    const progressBanner = document.getElementById("aiProgressBanner");



    const origBtnHtml = btn ? btn.innerHTML : "";



    if (btn) {



        btn.disabled = true;



        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-amber-300"></i><span>Đang tạo nội dung AI...</span>`;



    }



    if (progressBanner) {



        progressBanner.classList.remove("hidden");



    }



    const fields = {



        "STT": (document.getElementById("field_STT").value || "").trim(),



        "Chủ đề": chuDe,



        "Yêu cầu chủ đề": (document.getElementById("field_YeuCauChuDe").value || "").trim(),



        "Nội dung": (document.getElementById("field_NoiDung").value || "").trim(),



        "Hag tag": (document.getElementById("field_HagTag").value || "").trim(),



        "Loại video": loaiVideo,



        "Dạng video": dangVideo



    };



    try {



        const res = await fetch("/api/ai/generate_content", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({ index: currentRowIndex, fields: fields })



        });



        const result = await res.json();



        if (result.success) {



            showToast(result.message || "Tạo nội dung AI thành công!", "success");



            // Cập nhật dòng hiện tại



            if (result.row) {



                tableData[currentRowIndex] = result.row;



                document.getElementById("field_NoiDung").value = result.row["Nội dung"] || "";



                document.getElementById("field_HagTag").value = result.row["Hag tag"] || result.row["Hashtag"] || "";



                setSelectSmart("field_LoaiVideo", result.row["Loại video"] || "Chính sách thuế");



                setSelectSmart("field_DangVideo", result.row["Dạng video"] || "Ảnh cuộn");



                updateCharCount();



            }



            // Vẽ lại bảng và giữ chọn dòng



            renderTable(tableData);



            selectRow(currentRowIndex);



            // Mở modal kết quả xem Google Drive Folder & Doc



            openAiResultModal(result);



        } else {



            showToast("Lỗi: " + (result.message || "Không thể tạo nội dung"), "error");



            if (result.message && (result.message.includes("API Key") || result.message.includes("API key"))) {



                openAiConfigModal();



            }



        }



    } catch (e) {



        console.error("Lỗi triggerGenerateContent:", e);



        showToast("Lỗi kết nối khi gọi máy chủ tạo nội dung AI", "error");



    } finally {



        if (progressBanner) progressBanner.classList.add("hidden");



        if (btn) {



            btn.disabled = false;



            btn.innerHTML = origBtnHtml;



        }



    }



}



// ==========================================



// 13. QUẢN LÝ TAB & TRUNG TÂM KẾT NỐI (INTEGRATIONS HUB)



// ==========================================



function switchTab(tabName, focusTarget = null) {



    const tabContent = document.getElementById("tabContentSection");



    const tabIntegrations = document.getElementById("tabIntegrationsSection");



    const btnContent = document.getElementById("tabBtnContent");



    const btnIntegrations = document.getElementById("tabBtnIntegrations");



    if (!tabContent || !tabIntegrations) return;



    if (tabName === "integrations") {



        tabContent.classList.add("hidden");



        tabIntegrations.classList.remove("hidden");



        if (btnIntegrations) btnIntegrations.classList.add("active");



        if (btnContent) btnContent.classList.remove("active");



        localStorage.setItem("activeTab", "integrations");



        loadIntegrationsStatus();



        // Cập nhật trạng thái active trên Sidebar



        const sideContent = document.getElementById("sideNavContent");



        const sideInteg = document.getElementById("sideNavIntegrations");



        if (sideContent && sideInteg) {



            sideInteg.className = "w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-bold transition text-[#df8a5a] bg-[#fdf4ee] border border-[#f5d5c5]/80 shadow-2xs";



            sideContent.className = "w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent";



        }



        if (focusTarget) {



            setTimeout(() => {



                const el = document.getElementById(focusTarget) || document.getElementById(`card_${focusTarget}`);



                if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });



            }, 100);



        }



    } else {



        // Tab Nội dung (mặc định)



        tabIntegrations.classList.add("hidden");



        tabContent.classList.remove("hidden");



        if (btnContent) btnContent.classList.add("active");



        if (btnIntegrations) btnIntegrations.classList.remove("active");



        localStorage.setItem("activeTab", "content");



        // Cập nhật trạng thái active trên Sidebar



        const sideContent = document.getElementById("sideNavContent");



        const sideInteg = document.getElementById("sideNavIntegrations");



        if (sideContent && sideInteg) {



            sideContent.className = "w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-bold transition text-[#df8a5a] bg-[#fdf4ee] border border-[#f5d5c5]/80 shadow-2xs";



            sideInteg.className = "w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-medium transition text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent";



        }



    }



}



function togglePasswordVis(inputId, btn) {



    const input = document.getElementById(inputId);



    if (!input) return;



    const isPass = input.type === "password";



    input.type = isPass ? "text" : "password";



    const icon = btn.querySelector("i");



    if (icon) {



        icon.className = isPass ? "fa-solid fa-eye-slash" : "fa-solid fa-eye";



    }



}



async function loadIntegrationsStatus() {



    try {



        const res = await fetch("/api/integrations/status");



        const data = await res.json();



        if (!data.success) return;



        const count = data.connected_count || 0;



        const total = data.total_count || 6;



        // Badge tổng quan



        const badgeCount = document.getElementById("integrationsBadgeCount");



        if (badgeCount) badgeCount.textContent = `${count}/${total}`;



        const statCount = document.getElementById("statConnectedCount");



        if (statCount) statCount.textContent = `${count}/${total}`;



        const setDot = (id, isConn) => {



            const el = document.getElementById(id);



            if (el) {



                el.className = isConn 



                    ? "w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-emerald-200" 



                    : "w-2.5 h-2.5 rounded-full bg-slate-300";



            }



        };



        const setStatusBadge = (id, isConn) => {



            const el = document.getElementById(id);



            if (el) {



                if (isConn) {



                    el.className = "px-2.5 py-0.5 rounded text-[11px] font-bold bg-[#d1e7dd] text-[#0f5132] border border-[#badbcc] flex items-center gap-1.5";



                    el.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-600"></span><span>Đã kết nối</span>`;



                } else {



                    el.className = "px-2.5 py-0.5 rounded text-[11px] font-bold bg-[#f8f9fa] text-[#6c757d] border border-[#dee2e6] flex items-center gap-1.5";



                    el.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span><span>Chưa kết nối</span>`;



                }



            }



        };



        const integ = data.integrations || {};



        // 1. Google Drive



        const drive = integ.google_drive || {};



        setStatusBadge("card_status_drive", drive.is_connected);



        setDot("badge_dot_drive", drive.is_connected);



        const driveEmail = document.getElementById("integ_drive_email");



        if (driveEmail) driveEmail.textContent = drive.user_email || "Chưa đăng nhập";



        const driveFile = document.getElementById("integ_drive_filename");



        if (driveFile) driveFile.textContent = drive.file_name || "Thông tin";



        const credBadge = document.getElementById("credentialsStatusBadge");



        if (credBadge) {



            if (drive.has_credentials) {



                credBadge.textContent = "Đã nạp";



                credBadge.className = "text-[10px] text-emerald-700 font-mono font-semibold";



            } else {



                credBadge.textContent = "Chưa có file";



                credBadge.className = "text-[10px] text-amber-700 font-mono font-semibold";



            }



        }



        // 2. Gemini & NotebookLM



        const gemini = integ.gemini || {};



        setStatusBadge("card_status_gemini", gemini.is_connected);



        setDot("badge_dot_gemini", gemini.is_connected);



        const geminiKey = document.getElementById("integ_gemini_key");



        if (geminiKey && gemini.api_key) geminiKey.value = gemini.api_key;



        const geminiModel = document.getElementById("integ_gemini_model");



        if (geminiModel && gemini.model) geminiModel.value = gemini.model;



        const geminiNotebook = document.getElementById("integ_notebooklm_name");



        if (geminiNotebook && gemini.notebooklm_name) geminiNotebook.value = gemini.notebooklm_name;



        const geminiSearch = document.getElementById("integ_gemini_websearch");



        if (geminiSearch) geminiSearch.checked = gemini.enable_web_search !== false;



        const geminiCustom = document.getElementById("integ_gemini_custom");



        if (geminiCustom && gemini.custom_tax_knowledge) geminiCustom.value = gemini.custom_tax_knowledge;



        const geminiKeyBadge = document.getElementById("integ_gemini_key_badge");



        if (geminiKeyBadge) {



            geminiKeyBadge.textContent = gemini.api_key ? `Đã nạp (${gemini.api_key_preview})` : "Chưa có Key";



            geminiKeyBadge.className = gemini.api_key ? "text-[10px] text-emerald-700 font-mono font-semibold" : "text-[10px] text-amber-700 font-mono font-semibold";



        }



        // 3. Telegram



        const telegram = integ.telegram || {};



        setStatusBadge("card_status_telegram", telegram.is_connected);



        setDot("badge_dot_telegram", telegram.is_connected);



        const tgToken = document.getElementById("integ_telegram_token");



        if (tgToken && telegram.bot_token) tgToken.value = telegram.bot_token;



        const tgChat = document.getElementById("integ_telegram_chatid");



        if (tgChat && telegram.chat_id) tgChat.value = telegram.chat_id;



        const tgHint = document.getElementById("integ_telegram_botname_hint");



        if (tgHint && telegram.bot_name) {



            tgHint.innerHTML = `<span class="text-emerald-700 font-semibold">✅ Đã liên kết bot: ${telegram.bot_name}</span>`;



        }



        // 4. HeyGen



        const heygen = integ.heygen || {};



        setStatusBadge("card_status_heygen", heygen.is_connected);



        setDot("badge_dot_heygen", heygen.is_connected);



        const heygenKey = document.getElementById("integ_heygen_key");



        if (heygenKey && heygen.api_key) heygenKey.value = heygen.api_key;



        const heygenAvatar = document.getElementById("integ_heygen_avatar");



        if (heygenAvatar && heygen.avatar_id) heygenAvatar.value = heygen.avatar_id;



        const heygenVoice = document.getElementById("integ_heygen_voice");



        if (heygenVoice && heygen.voice_id) heygenVoice.value = heygen.voice_id;



        // 5. ElevenLabs



        const eleven = integ.elevenlabs || {};



        setStatusBadge("card_status_elevenlabs", eleven.is_connected);



        setDot("badge_dot_elevenlabs", eleven.is_connected);



        const elevenKey = document.getElementById("integ_elevenlabs_key");



        if (elevenKey && eleven.api_key) elevenKey.value = eleven.api_key;



        const elevenVoice = document.getElementById("integ_elevenlabs_voice");



        if (elevenVoice && eleven.voice_id) elevenVoice.value = eleven.voice_id;



        const elevenModel = document.getElementById("integ_elevenlabs_model");



        if (elevenModel && eleven.model_id) elevenModel.value = eleven.model_id;



        // 6. TikTok



        const tiktok = integ.tiktok || {};



        setStatusBadge("card_status_tiktok", tiktok.is_connected);



        setDot("badge_dot_tiktok", tiktok.is_connected);



        const ttUser = document.getElementById("integ_tiktok_username");



        if (ttUser && tiktok.username) ttUser.value = tiktok.username;



        const ttToken = document.getElementById("integ_tiktok_token");



        if (ttToken && tiktok.access_token) ttToken.value = tiktok.access_token;



        const ttPrivacy = document.getElementById("integ_tiktok_privacy");



        if (ttPrivacy && tiktok.privacy_level) ttPrivacy.value = tiktok.privacy_level;



        const ttKey = document.getElementById("integ_tiktok_client_key");



        if (ttKey && tiktok.client_key) ttKey.value = tiktok.client_key;

        const ttPublicUrl = document.getElementById("integ_tiktok_public_url");
        if (ttPublicUrl && tiktok.public_base_url) {
            ttPublicUrl.value = tiktok.public_base_url;
            updateTikTokHelperLinks({ tunnel_url: tiktok.public_base_url });
        }



        const ttHint = document.getElementById("integ_tiktok_token_hint");



        if (ttHint && tiktok.is_connected) {



            ttHint.innerHTML = `<span class="text-sky-700 font-semibold">✅ Đã liên kết kênh: ${tiktok.display_name || tiktok.username}</span>`;



        }



    } catch (e) {



        console.error("Lỗi loadIntegrationsStatus:", e);



    }



}



async function saveIntegration(platform) {



    const btn = document.getElementById(`btnSave_${platform}`);



    const origHtml = btn ? btn.innerHTML : "";



    if (btn) {



        btn.disabled = true;



        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Đang lưu...</span>`;



    }



    let fields = {};



    if (platform === "gemini") {



        fields = {



            api_key: (document.getElementById("integ_gemini_key").value || "").trim(),



            model: document.getElementById("integ_gemini_model").value,



            notebooklm_name: (document.getElementById("integ_notebooklm_name").value || "").trim(),



            enable_web_search: document.getElementById("integ_gemini_websearch").checked,



            custom_tax_knowledge: (document.getElementById("integ_gemini_custom").value || "").trim()



        };



    } else if (platform === "telegram") {



        fields = {



            bot_token: (document.getElementById("integ_telegram_token").value || "").trim(),



            chat_id: (document.getElementById("integ_telegram_chatid").value || "").trim()



        };



    } else if (platform === "heygen") {



        fields = {



            api_key: (document.getElementById("integ_heygen_key").value || "").trim(),



            avatar_id: (document.getElementById("integ_heygen_avatar").value || "").trim(),



            voice_id: (document.getElementById("integ_heygen_voice").value || "").trim()



        };



    } else if (platform === "elevenlabs") {



        fields = {



            api_key: (document.getElementById("integ_elevenlabs_key").value || "").trim(),



            voice_id: (document.getElementById("integ_elevenlabs_voice").value || "").trim(),



            model_id: document.getElementById("integ_elevenlabs_model").value



        };



    } else if (platform === "tiktok") {



        fields = {



            username: (document.getElementById("integ_tiktok_username").value || "").trim(),



            access_token: (document.getElementById("integ_tiktok_token").value || "").trim(),



            privacy_level: document.getElementById("integ_tiktok_privacy").value,



            client_key: (document.getElementById("integ_tiktok_client_key").value || "").trim(),



            client_secret: (document.getElementById("integ_tiktok_client_secret").value || "").trim(),
            public_base_url: (document.getElementById("integ_tiktok_public_url") ? document.getElementById("integ_tiktok_public_url").value : "").trim()



        };



    }



    try {



        const res = await fetch("/api/integrations/save", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({ platform, fields })



        });



        const result = await res.json();



        if (result.success) {



            showToast(result.message || "Đã lưu cấu hình thành công!", "success");



            await loadIntegrationsStatus();



            await checkAiConfigStatus();



        } else {



            showToast("Lỗi lưu cấu hình: " + (result.message || "Thất bại"), "error");



        }



    } catch (e) {



        showToast("Lỗi kết nối máy chủ khi lưu cấu hình", "error");



    } finally {



        if (btn) {



            btn.disabled = false;



            btn.innerHTML = origHtml;



        }



    }



}



async function testIntegration(platform) {



    const btn = document.getElementById(`btnTest_${platform}`);



    const origHtml = btn ? btn.innerHTML : "";



    if (btn) {



        btn.disabled = true;



        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Đang kiểm tra...</span>`;



    }



    let fields = {};



    if (platform === "gemini") {



        fields = {



            api_key: (document.getElementById("integ_gemini_key").value || "").trim(),



            model: document.getElementById("integ_gemini_model").value



        };



    } else if (platform === "telegram") {



        fields = {



            bot_token: (document.getElementById("integ_telegram_token").value || "").trim(),



            chat_id: (document.getElementById("integ_telegram_chatid").value || "").trim()



        };



    } else if (platform === "heygen") {



        fields = {



            api_key: (document.getElementById("integ_heygen_key").value || "").trim(),



            avatar_id: (document.getElementById("integ_heygen_avatar").value || "").trim()



        };



    } else if (platform === "elevenlabs") {



        fields = {



            api_key: (document.getElementById("integ_elevenlabs_key").value || "").trim(),



            voice_id: (document.getElementById("integ_elevenlabs_voice").value || "").trim(),



            model_id: document.getElementById("integ_elevenlabs_model").value



        };



    } else if (platform === "tiktok") {



        fields = {



            username: (document.getElementById("integ_tiktok_username").value || "").trim(),



            access_token: (document.getElementById("integ_tiktok_token").value || "").trim(),



            privacy_level: document.getElementById("integ_tiktok_privacy").value,



            client_key: (document.getElementById("integ_tiktok_client_key").value || "").trim(),



            client_secret: (document.getElementById("integ_tiktok_client_secret").value || "").trim(),
            public_base_url: (document.getElementById("integ_tiktok_public_url") ? document.getElementById("integ_tiktok_public_url").value : "").trim()



        };



    }



    try {



        const res = await fetch("/api/integrations/test", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({ platform, fields })



        });



        const result = await res.json();



        if (result.success) {



            showToast("🎉 " + result.message, "success");



            await loadIntegrationsStatus();



        } else {



            showToast("❌ " + (result.message || "Kiểm tra thất bại"), "error");



        }



    } catch (e) {



        showToast("Lỗi khi gửi yêu cầu kiểm tra kết nối", "error");



    } finally {



        if (btn) {



            btn.disabled = false;



            btn.innerHTML = origHtml;



        }



    }



}



async function uploadCredentialsFromTab() {



    const input = document.getElementById("integ_credentialsFileInput");



    if (!input.files || input.files.length === 0) {



        showToast("Vui lòng chọn file credentials.json trước", "error");



        return;



    }



    const formData = new FormData();



    formData.append("file", input.files[0]);



    try {



        showToast("Đang tải lên credentials.json...", "info");



        const res = await fetch("/api/credentials/upload", {



            method: "POST",



            body: formData



        });



        const result = await res.json();



        if (result.success) {



            showToast(result.message, "success");



            await fetchStatus();



            await loadIntegrationsStatus();



        } else {



            showToast(result.message, "error");



        }



    } catch (e) {



        showToast("Lỗi tải lên credentials.json", "error");



    }



}



// =========================================================



// TELEGRAM INTERACTIVE APPROVAL TEST (Duyệt hai chiều Telegram)



// =========================================================



let telegramPollInterval = null;



let currentTelegramPromptId = null;



async function autoDetectTelegramChatId() {



    const token = (document.getElementById("integ_telegram_token").value || "").trim();



    if (!token) {



        showToast("Vui lòng nhập Telegram Bot Token trước!", "error");



        return;



    }



    showToast("🔍 Đang quét tin nhắn gửi tới Bot...", "info");



    try {



        const res = await fetch("/api/telegram/detect_chat_id", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({ bot_token: token })



        });



        const result = await res.json();



        if (result.success && result.details) {



            const chatIdInput = document.getElementById("integ_telegram_chatid");



            if (chatIdInput) {



                chatIdInput.value = result.details.chat_id;



            }



            showToast(`🎉 ${result.message}`, "success");



            await loadIntegrationsStatus();



        } else {



            const botUser = (result.details && result.details.bot_username) || "BoomNam_Bot";



            showToast(result.message || `Chưa tìm thấy tin nhắn! Hãy mở Telegram, tìm @${botUser} và nhắn /start trước!`, "error");



        }



    } catch (e) {



        showToast("Lỗi khi tự động nhận diện Chat ID", "error");



    }



}



async function startTelegramApprovalTest() {



    const btn = document.getElementById("btnSendTelegramQuestion");



    const origHtml = btn ? btn.innerHTML : "";



    



    const token = (document.getElementById("integ_telegram_token").value || "").trim();



    let chatId = (document.getElementById("integ_telegram_chatid").value || "").trim();



    const question = (document.getElementById("integ_telegram_test_question").value || "bạn có đồng ý chỉnh sửa không?").trim();



    const resultBox = document.getElementById("telegram_test_result_box");



    if (!token) {



        showToast("Vui lòng nhập Telegram Bot Token!", "error");



        return;



    }



    // Nếu chat_id trống hoặc là tên bot (@BoomNam_Bot), cảnh báo ngay



    if (!chatId || (chatId.startsWith("@") && chatId.toLowerCase().includes("bot"))) {



        showToast("⚠️ Chat ID không thể là tên của chính Bot! Đang thử tự động quét Chat ID từ tin nhắn của bạn...", "info");



        await autoDetectTelegramChatId();



        chatId = (document.getElementById("integ_telegram_chatid").value || "").trim();



        if (!chatId || (chatId.startsWith("@") && chatId.toLowerCase().includes("bot"))) {



            showToast("Vui lòng mở Telegram, tìm @BoomNam_Bot và bấm /start để Bot lấy Chat ID của bạn!", "error");



            return;



        }



    }



    if (btn) {



        btn.disabled = true;



        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Đang gửi...</span>`;



    }



    // Hiển thị trạng thái đang gửi



    resultBox.classList.remove("hidden");



    resultBox.innerHTML = `



        <div class="p-3 bg-[#DAEAF9]/60 border border-[#b6d4f1] rounded flex items-center justify-between text-xs">



            <span class="text-[#002D62] flex items-center gap-2 font-semibold">



                <i class="fa-solid fa-spinner fa-spin text-[#006FBC]"></i>



                <span>Đang kết nối API Telegram để gửi câu hỏi phê duyệt...</span>



            </span>



        </div>



    `;



    try {



        const res = await fetch("/api/telegram/send_question", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({



                bot_token: token,



                chat_id: chatId,



                question: question



            })



        });



        const data = await res.json();



        if (!data.success) {



            resultBox.innerHTML = `



                <div class="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-xs space-y-2">



                    <div class="font-bold text-rose-800 flex items-center gap-1.5">



                        <i class="fa-solid fa-triangle-exclamation text-rose-600"></i>



                        <span>Không thể gửi câu hỏi tới Telegram!</span>



                    </div>



                    <div class="text-[#5c687e]">${data.message}</div>



                    <div class="pt-1 flex items-center gap-2">



                        <a href="https://t.me/BoomNam_Bot" target="_blank" class="btn-primary-mark py-1.5 px-3 text-xs inline-flex items-center gap-1.5">



                            <i class="fa-brands fa-telegram"></i> Mở @BoomNam_Bot trên Telegram



                        </a>



                        <button type="button" onclick="autoDetectTelegramChatId()" class="btn-outline-mark py-1.5 px-3 text-xs">



                            Tự nhận diện Chat ID



                        </button>



                    </div>



                </div>



            `;



            showToast("❌ " + data.message, "error");



            return;



        }



        const promptId = data.details.prompt_id;



        currentTelegramPromptId = promptId;



        // Render trạng thái chờ phản hồi



        resultBox.innerHTML = `



            <div class="p-4 bg-[#ffffff] border border-[#f5d5c5] rounded-2xl space-y-3 text-xs">



                <div class="flex items-center justify-between">



                    <span class="font-extrabold text-[#282d38] flex items-center gap-2">



                        <span class="w-2.5 h-2.5 rounded-full bg-[#df8a5a] animate-ping"></span>



                        <i class="fa-solid fa-paper-plane text-[#df8a5a]"></i>



                        <span>ĐÃ GỬI CÂU HỎI TỚI TELEGRAM!</span>



                    </span>



                    <button type="button" onclick="cancelTelegramPolling()" class="text-[#6b7588] hover:text-[#df8a5a] text-[11px] font-semibold underline">



                        Hủy chờ



                    </button>



                </div>



                <div class="text-[#282d38]">



                    Câu hỏi: <span class="font-extrabold text-[#df8a5a]">"${question}"</span>



                </div>



                <div class="p-3 bg-white rounded-xl border border-[#e3e7f0] text-[11px] text-[#5c687e] flex items-center gap-2 shadow-xs">



                    <i class="fa-solid fa-spinner fa-spin text-[#df8a5a] text-sm"></i>



                    <span>Đang chờ bạn mở Telegram và chọn <b>[✅ Đồng ý]</b>, <b>[❌ Từ chối]</b> hoặc gõ chữ trả lời...</span>



                </div>



            </div>



        `;



        showToast("🔔 Đã gửi câu hỏi tới Telegram! Hãy kiểm tra Telegram để trả lời.", "info");



        // Dừng polling cũ nếu có



        if (telegramPollInterval) clearInterval(telegramPollInterval);



        // Bắt đầu Polling kiểm tra kết quả mỗi 1.5 giây



        telegramPollInterval = setInterval(async () => {



            await checkTelegramResponse(promptId, question);



        }, 1500);



    } catch (e) {



        showToast("Lỗi kết nối khi gửi câu hỏi Telegram", "error");



        resultBox.classList.add("hidden");



    } finally {



        if (btn) {



            btn.disabled = false;



            btn.innerHTML = origHtml;



        }



    }



}



async function checkTelegramResponse(promptId, question) {



    if (currentTelegramPromptId !== promptId) return;



    try {



        const res = await fetch(`/api/telegram/poll_response?prompt_id=${encodeURIComponent(promptId)}`);



        const data = await res.json();



        if (data.success && data.answered) {



            // Đã nhận được câu trả lời!



            if (telegramPollInterval) {



                clearInterval(telegramPollInterval);



                telegramPollInterval = null;



            }



            const resultBox = document.getElementById("telegram_test_result_box");



            if (!resultBox) return;



            const isApprove = data.response && (data.response.includes("Đồng ý") || data.response.toLowerCase().includes("dong y") || data.response.toLowerCase().includes("yes"));



            const badgeColor = isApprove ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-[#fdf4ee] text-[#df8a5a] border-[#f5d5c5]";



            const iconClass = isApprove ? "fa-circle-check text-emerald-600" : "fa-comment-dots text-[#df8a5a]";



            resultBox.innerHTML = `



                <div class="p-4 bg-white border border-[#f5d5c5] rounded-2xl space-y-3 text-xs shadow-sm">



                    <div class="flex items-center justify-between border-b border-[#e3e7f0] pb-2.5">



                        <div class="flex items-center gap-2.5">



                            <div class="w-8 h-8 rounded-full bg-[#fdf4ee] border border-[#f5d5c5] flex items-center justify-center text-sm">



                                <i class="fa-solid ${iconClass}"></i>



                            </div>



                            <div>



                                <span class="font-extrabold text-[#282d38] text-sm">ĐÃ NHẬN PHẢN HỒI TỪ TELEGRAM!</span>



                                <div class="text-[10px] text-[#6b7588]">Quy trình hỏi đáp hai chiều trực tuyến hoàn tất</div>



                            </div>



                        </div>



                        <span class="text-[10px] font-bold font-mono px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">



                            HOÀN TẤT



                        </span>



                    </div>



                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-[#ffffff] p-3.5 rounded-xl border border-[#e3e7f0]">



                        <div>



                            <span class="text-[#6b7588] text-[11px] block font-semibold">Câu hỏi gửi đi:</span>



                            <div class="font-bold text-[#282d38] text-xs mt-0.5">"${question}"</div>



                        </div>



                        <div>



                            <span class="text-[#6b7588] text-[11px] block font-semibold">Nội dung đã trả lời:</span>



                            <div class="mt-0.5 inline-block font-extrabold text-sm px-3 py-1 rounded-full border ${badgeColor}">



                                ${data.response}



                            </div>



                        </div>



                        <div>



                            <span class="text-[#6b7588] text-[11px] block font-semibold">Người phản hồi:</span>



                            <div class="text-[#282d38] font-bold text-xs mt-0.5 flex items-center gap-1.5">



                                <i class="fa-solid fa-user text-[#6b7588] text-[10px]"></i>



                                <span>${data.responder || "Người dùng Telegram"}</span>



                            </div>



                        </div>



                        <div>



                            <span class="text-[#6b7588] text-[11px] block font-semibold">Thời gian tiếp nhận:</span>



                            <div class="text-[#5c687e] font-mono text-xs mt-0.5 flex items-center gap-1.5">



                                <i class="fa-regular fa-clock text-[#6b7588] text-[10px]"></i>



                                <span>${data.answered_at || "Vừa xong"}</span>



                            </div>



                        </div>



                    </div>



                    <div class="flex items-center justify-between pt-1">



                        <span class="text-[11px] text-emerald-700 font-semibold flex items-center gap-1.5">



                            <i class="fa-solid fa-check-double text-emerald-600"></i>



                            <span>Hệ thống đã tự động gửi tin nhắn xác nhận ngược lại Telegram của bạn!</span>



                        </span>



                        <button type="button" onclick="startTelegramApprovalTest()" class="btn-outline-mark py-1.5 px-3 text-xs">



                            Thử lại câu khác



                        </button>



                    </div>



                </div>



            `;



            showToast(`🎉 Telegram đã phản hồi: "${data.response}"!`, "success");



        }



    } catch (e) {



        console.error("Lỗi poll telegram:", e);



    }



}



function cancelTelegramPolling() {



    if (telegramPollInterval) {



        clearInterval(telegramPollInterval);



        telegramPollInterval = null;



    }



    currentTelegramPromptId = null;



    const resultBox = document.getElementById("telegram_test_result_box");



    if (resultBox) {



        resultBox.classList.add("hidden");



    }



    showToast("Đã dừng chờ phản hồi Telegram.", "info");



}



// ==========================================



// 13. QUẢN LÝ THÔNG SỐ ẢNH CUỘN (CAROUSEL PRESETS)



// ==========================================



let carouselPresets = [];



async function loadCarouselPresets() {



    try {



        const res = await fetch("/api/carousel-presets");



        const data = await res.json();



        if (data.success && data.presets) {



            carouselPresets = data.presets;



            renderCarouselPresetsUI();



            populateCarouselPresetSelect();



        }



    } catch (e) {



        console.error("Lỗi tải carousel presets:", e);



    }



}



let currentPresetCategoryFilter = 'all';

function filterCarouselPresets(cat) {
    currentPresetCategoryFilter = cat;
    document.querySelectorAll(".preset-filter-btn").forEach(btn => {
        btn.classList.remove("bg-[#df8a5a]", "text-white");
        btn.classList.add("bg-white", "text-slate-700");
    });
    const activeBtn = (cat === 'all') ? document.getElementById("presetFilter_all") :
        (cat === 'Xanh & Trắng') ? document.getElementById("presetFilter_blue") :
        (cat === 'Đỏ - Trắng - Đen') ? document.getElementById("presetFilter_red") :
        (cat === 'Cam Vàng - Trắng - Đen') ? document.getElementById("presetFilter_orange") : null;
    if (activeBtn) {
        activeBtn.classList.remove("bg-white", "text-slate-700");
        activeBtn.classList.add("bg-[#df8a5a]", "text-white");
    }
    renderCarouselPresetsUI();
}

function populateCarouselPresetSelect(selectedId = null) {
    const sel = document.getElementById("field_CarouselPresetId");
    if (!sel) return;

    const hasCategories = carouselPresets.some(p => p.category);
    if (!hasCategories) {
        sel.innerHTML = carouselPresets.map(p => `
            <option value="${p.id}" ${p.is_default && !selectedId ? 'selected' : (p.id === selectedId ? 'selected' : '')}>
                ${p.name} ${p.is_default ? '★ (Mặc định)' : ''}
            </option>
        `).join("");
    } else {
        const groups = {};
        carouselPresets.forEach(p => {
            const cat = p.category || "Khác";
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(p);
        });

        let html = "";
        for (const [catName, list] of Object.entries(groups)) {
            html += `<optgroup label="📁 ${catName}">`;
            list.forEach(p => {
                const isSel = (selectedId && p.id === selectedId) || (!selectedId && p.is_default);
                html += `<option value="${p.id}" ${isSel ? 'selected' : ''}>${p.name} ${p.is_default ? '★ (Mặc định)' : ''}</option>`;
            });
            html += `</optgroup>`;
        }
        sel.innerHTML = html;
    }
    onCarouselPresetChange();
}



function onDangVideoChange() {



    const dangVideo = (document.getElementById("field_DangVideo").value || "").trim();



    const container = document.getElementById("carouselPresetSelectContainer");



    if (!container) return;



    if (dangVideo.includes("Ảnh cuộn")) {



        container.classList.remove("hidden");



        onCarouselPresetChange();



    } else {



        container.classList.add("hidden");



    }



}



function onCarouselPresetChange() {



    const sel = document.getElementById("field_CarouselPresetId");



    const preview = document.getElementById("presetDescPreview");



    if (!sel || !preview) return;



    const chosenId = sel.value;



    const preset = carouselPresets.find(p => p.id === chosenId) || carouselPresets[0];



    const imgPreview = document.getElementById("presetImgPreview");



    if (preset) {



        preview.innerHTML = `<strong>${preset.name}:</strong> ${preset.description || preset.instruction || ''}`;



        if (imgPreview) {



            imgPreview.src = preset.image_url || "/static/images/presets/preset_mark_dao_infographic.jpg";



        }



    } else {



        preview.textContent = "Chưa chọn thông số ảnh cuộn";



    }



}



function renderCarouselPresetsUI() {



    const listEl = document.getElementById("carouselPresetsList");



    if (!listEl) return;
    const filteredPresets = (currentPresetCategoryFilter === 'all') 
        ? carouselPresets 
        : carouselPresets.filter(p => p.category === currentPresetCategoryFilter);

    if (!filteredPresets.length) {
        listEl.innerHTML = `
            <div class="col-span-2 p-8 text-center text-slate-400 bg-slate-50/60 rounded-2xl border border-slate-200">
                <i class="fa-solid fa-folder-open text-2xl mb-2 text-slate-300"></i>
                <div>Chưa có kiểu thiết kế nào trong danh mục này.</div>
            </div>
        `;
        return;
    }

    listEl.innerHTML = filteredPresets.map(p => {



        const imgUrl = p.image_url || "/static/images/presets/preset_mark_dao_infographic.jpg";



        return `



            <div class="mark-card p-4 flex flex-col sm:flex-row gap-4 border-2 ${p.is_default ? 'border-[#df8a5a] bg-[#fdf6f2]/40' : 'border-[#e3e7f0] bg-white'} relative transition shadow-xs hover:shadow-md">



                <!-- Cột trái: Ảnh minh họa phong cách (tỷ lệ dọc 9:16) -->



                <div class="w-28 sm:w-32 aspect-[4/5] rounded-xl overflow-hidden shrink-0 border border-[#df8a5a]/30 shadow-xs relative bg-slate-100 group/img cursor-pointer" onclick="viewLargeImage('${imgUrl}', '${p.name.replace(/'/g, "\\'")}')" title="Bấm để xem ảnh mẫu phóng to 4:5">
                    <img src="${imgUrl}" alt="${p.name}" class="w-full h-full object-cover transition-transform duration-300 group-hover/img:scale-105" loading="lazy">
                    <span class="absolute bottom-1.5 left-1.5 right-1.5 text-center text-[8.5px] font-bold bg-black/60 text-white py-0.5 rounded-md backdrop-blur-xs flex items-center justify-center gap-1">
                        <i class="fa-solid fa-magnifying-glass text-[7.5px]"></i> Ảnh mẫu 4:5
                    </span>
                </div>



                <!-- Cột phải: Thông tin chi tiết, mô tả & chỉ dẫn AI -->



                <div class="flex-1 flex flex-col justify-between space-y-2.5 min-w-0">



                    <div>



                        <div class="flex items-start justify-between gap-2 mb-1.5">



                            <h5 class="text-xs font-bold text-[#282d38] flex items-center gap-1.5 truncate">



                                <i class="fa-solid fa-layer-group text-[#df8a5a]"></i>



                                <span class="truncate">${p.name}</span>



                            </h5>
                                ${p.category ? `
                                    <span class="px-2 py-0.5 rounded-md text-[9px] font-bold shrink-0 ${
                                        p.category.includes('Xanh') ? 'bg-blue-100 text-blue-700 border border-blue-200' :
                                        p.category.includes('Đỏ') ? 'bg-red-100 text-red-700 border border-red-200' :
                                        'bg-amber-100 text-amber-800 border border-amber-200'
                                    }">
                                        <i class="fa-solid fa-folder text-[8px] mr-0.5"></i> ${p.category}
                                    </span>
                                ` : ''}



                            ${p.is_default ? `



                                <span class="px-2 py-0.5 rounded-full bg-[#df8a5a] text-white text-[9px] font-bold shrink-0">



                                    ★ Mặc định



                                </span>



                            ` : `



                                <button type="button" onclick="setDefaultPreset('${p.id}')" class="text-[10px] text-slate-400 hover:text-[#df8a5a] font-medium transition shrink-0" title="Đặt làm mặc định">



                                    Đặt mặc định



                                </button>



                            `}



                        </div>



                        <p class="text-[11px] text-slate-600 line-clamp-2 leading-relaxed mb-2">${p.description || "Chưa có mô tả"}</p>



                        <div class="bg-white/90 p-2.5 rounded-xl border border-[#e3e7f0] text-[10.5px] font-mono text-slate-700 leading-relaxed max-h-24 overflow-y-auto scrollbar-thin">



                            <div class="text-[9.5px] font-bold text-[#df8a5a] uppercase font-sans mb-0.5 flex items-center justify-between">



                                <span>Chỉ dẫn AI tạo ảnh:</span>



                                <span class="text-[8.5px] text-slate-400 font-normal">Cơ sở sinh ảnh</span>



                            </div>



                            ${p.instruction || "Chưa có chỉ dẫn"}



                        </div>



                    </div>



                    <div class="flex items-center justify-end gap-2 pt-2 border-t border-[#e3e7f0]">



                        <button type="button" onclick="openEditPresetModal('${p.id}')" class="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-[#df8a5a] hover:text-white text-slate-700 text-[11px] font-semibold transition flex items-center gap-1 shadow-2xs">



                            <i class="fa-solid fa-pen-to-square text-[10px]"></i>



                            <span>Sửa</span>



                        </button>



                        <button type="button" onclick="deletePreset('${p.id}')" class="px-2.5 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 text-[11px] font-semibold transition" title="Xóa kiểu này">



                            <i class="fa-regular fa-trash-can"></i>



                        </button>



                    </div>



                </div>



            </div>



        `;



    }).join("");



}



function openPlatformConfigModal() {



    loadCarouselPresets();



    const modal = document.getElementById("platformConfigModal");



    if (modal) modal.classList.remove("hidden");



}



function closePlatformConfigModal() {



    const modal = document.getElementById("platformConfigModal");



    if (modal) modal.classList.add("hidden");



}



function switchPlatformTab(tabName) {



    ['carousel', 'video', 'ai'].forEach(t => {



        const btn = document.getElementById(`tabBtn_platform_${t}`);



        const content = document.getElementById(`platformTab_${t}`);



        if (!btn || !content) return;



        if (t === tabName) {



            btn.className = "px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-2 bg-[#fdf4ee] text-[#df8a5a] border border-[#f5d5c5]";



            content.classList.remove("hidden");



        } else {



            btn.className = "px-3.5 py-1.5 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-100 transition flex items-center gap-2";



            content.classList.add("hidden");



        }



    });



}



function openCreatePresetModal() {



    document.getElementById("presetEditModalTitle").textContent = "Thêm Thông Số Ảnh Cuộn Mới";



    document.getElementById("editPresetId").value = "";



    document.getElementById("presetForm_name").value = "";
    if (document.getElementById("presetForm_category")) document.getElementById("presetForm_category").value = "Xanh & Trắng";



    document.getElementById("presetForm_description").value = "";



    document.getElementById("presetForm_instruction").value = "";



    const imgInput = document.getElementById("presetForm_imageUrl");



    const imgPrev = document.getElementById("presetForm_imagePreview");



    if (imgInput) imgInput.value = "/static/images/presets/preset_mark_dao_infographic.jpg";



    if (imgPrev) imgPrev.src = "/static/images/presets/preset_mark_dao_infographic.jpg";



    document.getElementById("presetForm_isDefault").checked = false;



    document.getElementById("presetEditSubModal").classList.remove("hidden");



}



function openEditPresetModal(presetId) {



    const p = carouselPresets.find(item => item.id === presetId);



    if (!p) return;



    document.getElementById("presetEditModalTitle").textContent = "Chỉnh Sửa Thông Số Ảnh Cuộn";



    document.getElementById("editPresetId").value = p.id;



    document.getElementById("presetForm_name").value = p.name || "";
    if (document.getElementById("presetForm_category")) document.getElementById("presetForm_category").value = p.category || "Xanh & Trắng";



    document.getElementById("presetForm_description").value = p.description || "";



    document.getElementById("presetForm_instruction").value = p.instruction || "";



    const imgInput = document.getElementById("presetForm_imageUrl");



    const imgPrev = document.getElementById("presetForm_imagePreview");



    const sampleUrl = p.image_url || "/static/images/presets/preset_mark_dao_infographic.jpg";



    if (imgInput) imgInput.value = sampleUrl;



    if (imgPrev) imgPrev.src = sampleUrl;



    document.getElementById("presetForm_isDefault").checked = !!p.is_default;



    document.getElementById("presetEditSubModal").classList.remove("hidden");



}



function closePresetEditModal() {



    document.getElementById("presetEditSubModal").classList.add("hidden");



}



async function generatePresetAiPrompt() {
    const nameEl = document.getElementById("presetForm_name");
    const descEl = document.getElementById("presetForm_description");
    const instEl = document.getElementById("presetForm_instruction");
    const btn = document.getElementById("btnGeneratePresetAiPrompt");
    const icon = document.getElementById("iconGeneratePresetAiPrompt");
    const txt = document.getElementById("textGeneratePresetAiPrompt");

    const name = nameEl ? nameEl.value.trim() : "";
    const description = descEl ? descEl.value.trim() : "";

    if (!description && !name) {
        showToast("Vui lòng nhập 'Mô tả phong cách ảnh cuộn' trước khi bấm AI Prompt!", "error");
        if (descEl) descEl.focus();
        return;
    }

    if (btn) btn.disabled = true;
    if (icon) icon.className = "fa-solid fa-spinner fa-spin text-[11px]";
    if (txt) txt.textContent = "Đang tạo...";

    try {
        const res = await fetch("/api/carousel-presets/generate-prompt", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, description })
        });
        const data = await res.json();
        if (data.success && data.instruction) {
            if (instEl) {
                instEl.value = data.instruction;
                instEl.focus();
            }
            showToast(data.message || "AI đã tạo chỉ dẫn tạo ảnh thành công!", "success");
        } else {
            showToast("Lỗi tạo AI Prompt: " + (data.message || "Không xác định"), "error");
        }
    } catch (e) {
        showToast("Lỗi kết nối tới AI: " + e.message, "error");
    } finally {
        if (btn) btn.disabled = false;
        if (icon) icon.className = "fa-solid fa-wand-magic-sparkles text-[11px]";
        if (txt) txt.textContent = "AI Prompt";
    }
}



async function submitPresetForm() {



    const id = document.getElementById("editPresetId").value;



    const name = document.getElementById("presetForm_name").value.trim();
    const category = document.getElementById("presetForm_category") ? document.getElementById("presetForm_category").value : "Xanh & Trắng";



    const description = document.getElementById("presetForm_description").value.trim();



    const instruction = document.getElementById("presetForm_instruction").value.trim();



    const image_url = (document.getElementById("presetForm_imageUrl") ? document.getElementById("presetForm_imageUrl").value.trim() : "");



    const is_default = document.getElementById("presetForm_isDefault").checked;



    if (!name) {



        showToast("Vui lòng nhập tên thông số ảnh cuộn!", "error");



        return;



    }



    try {



        const res = await fetch("/api/carousel-presets", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify({ id, name, category, description, instruction, image_url, is_default })



        });



        const data = await res.json();



        if (data.success) {



            showToast(data.message || "Đã lưu thông số thành công!", "success");



            closePresetEditModal();



            loadCarouselPresets();



        } else {



            showToast("Lỗi lưu thông số: " + data.message, "error");



        }



    } catch (e) {



        showToast("Lỗi kết nối khi lưu thông số", "error");



    }



}



async function deletePreset(presetId) {



    if (!confirm("Bạn có chắc chắn muốn xóa kiểu thông số ảnh cuộn này?")) return;



    try {



        const res = await fetch(`/api/carousel-presets/${presetId}`, { method: "DELETE" });



        const data = await res.json();



        if (data.success) {



            showToast(data.message || "Đã xóa thành công!", "success");



            loadCarouselPresets();



        } else {



            showToast("Lỗi khi xóa: " + data.message, "error");



        }



    } catch (e) {



        showToast("Lỗi kết nối khi xóa", "error");



    }



}



async function setDefaultPreset(presetId) {



    try {



        const res = await fetch(`/api/carousel-presets/${presetId}/default`, { method: "POST" });



        const data = await res.json();



        if (data.success) {



            showToast("Đã đặt làm mẫu mặc định!", "success");



            loadCarouselPresets();



        }



    } catch (e) {



        showToast("Lỗi đặt mặc định", "error");



    }



}



// ==========================================



// 14. TẠO SLIDE HÌNH ẢNH (AI SLIDE GENERATOR)



// ==========================================



async function triggerGenerateSlides() {



    if (currentRowIndex < 0 || currentRowIndex >= tableData.length) {



        showToast("Vui lòng click chọn một dòng dữ liệu trên bảng trước!", "error");



        return;



    }



    // Yêu cầu: Kiểm tra duyệt CĐ và HT đã được checked



    const duyetCDHT = document.getElementById("field_DuyetCDHT").checked;



    if (!duyetCDHT) {



        showToast("Vui lòng duyệt CĐ và HT (tích chọn 'duyệt CĐ và HT' ở Cột H) trước khi thực hiện Tạo Slide hình ảnh!", "error");



        document.getElementById("field_DuyetCDHT").focus();



        return;



    }



    const noiDung = (document.getElementById("field_NoiDung").value || "").trim();



    if (!noiDung) {



        showToast("Nội dung kịch bản đang trống! Vui lòng bấm 'TẠO NỘI DUNG SLIDE' trước để AI sinh kịch bản.", "error");



        return;



    }



    const chuDe = (document.getElementById("field_ChuDe").value || "").trim();



    const presetId = document.getElementById("field_CarouselPresetId") ? document.getElementById("field_CarouselPresetId").value : "";



    const btn = document.getElementById("btnGenerateSlides");



    const origBtnHtml = btn ? btn.innerHTML : "";



    const progressBanner = document.getElementById("aiProgressBanner");



    const progressText = document.getElementById("aiProgressText");



    if (btn) {



        btn.disabled = true;



        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-emerald-200"></i><span>Đang tạo Slide ảnh AI...</span>`;



    }



    if (progressBanner) {



        if (progressText) progressText.textContent = "AI đang thiết kế hình ảnh từng slide 9:16 & lưu vào Google Drive...";



        progressBanner.classList.remove("hidden");



    }



    const payload = {



        index: currentRowIndex,



        preset_id: presetId,



        fields: {



            "STT": document.getElementById("field_STT").value,



            "Chủ đề": chuDe,



            "Yêu cầu chủ đề": (document.getElementById("field_YeuCauChuDe").value || "").trim(),



            "Nội dung": noiDung,



            "Hag tag": (document.getElementById("field_HagTag").value || "").trim(),



            "Loại video": document.getElementById("field_LoaiVideo").value,



            "Dạng video": document.getElementById("field_DangVideo").value,



            "duyệt CĐ và HT": "x",



            "Duyệt nội dung": (document.getElementById("field_DuyetNoiDung") && document.getElementById("field_DuyetNoiDung").checked) ? "x" : ""



        }



    };



    try {



        const res = await fetch("/api/ai/generate_slides", {



            method: "POST",



            headers: { "Content-Type": "application/json" },



            body: JSON.stringify(payload)



        });



        const result = await res.json();



        if (result.success) {



            showToast(result.message || `Đã tạo ${result.total_slides} slide thành công!`, "success");



            openSlidePreviewModal(result);



        } else {



            showToast("Lỗi tạo slide: " + (result.message || "Thất bại"), "error");



        }



    } catch (e) {



        console.error("Lỗi triggerGenerateSlides:", e);



        showToast("Lỗi kết nối khi gửi yêu cầu tạo slide", "error");



    } finally {



        if (btn) {



            btn.disabled = false;



            btn.innerHTML = origBtnHtml;



        }



        if (progressBanner) progressBanner.classList.add("hidden");



    }



}



function openSlidePreviewModal(result) {



    const modal = document.getElementById("slidePreviewModal");



    if (!modal) return;



    const folderLink = document.getElementById("slideFolderLink");



    const folderName = document.getElementById("slideFolderName");



    const totalBadge = document.getElementById("slideTotalBadge");



    const presetUsed = document.getElementById("slidePresetUsed");



    const container = document.getElementById("slidesGalleryContainer");



    if (totalBadge) totalBadge.textContent = `${result.total_slides || 0} Slides`;



    if (presetUsed) presetUsed.textContent = `Phong cách: ${result.preset_name || 'Infographic'}`;



    if (folderLink && result.folder_url) {



        folderLink.href = result.folder_url;



        folderLink.setAttribute("target", "_blank");



    }



    if (folderName) {



        folderName.textContent = `Thư mục lưu trữ: ${result.folder_id ? 'Đã đồng bộ Drive' : 'Local & Drive'}`;



    }



    if (container && result.slides) {



        container.innerHTML = result.slides.map(s => `



            <div class="mark-card p-2 flex flex-col space-y-2 border border-[#e3e7f0] group hover:border-emerald-500 transition shadow-2xs">



                <div class="relative aspect-[9/16] bg-slate-100 rounded-xl overflow-hidden border border-slate-200 shadow-inner">



                    <img src="${s.local_url}?v=${Date.now()}" alt="${s.title}" class="w-full h-full object-cover transition duration-300 group-hover:scale-105" loading="lazy">



                    <div class="absolute top-1.5 left-1.5 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-white font-mono text-[9px] font-bold">



                        Slide ${s.slide_num}



                    </div>



                </div>



                <div class="px-1">



                    <div class="text-[11px] font-bold text-slate-800 truncate" title="${s.title}">${s.title}</div>



                    <div class="text-[10px] text-slate-500 flex items-center justify-between mt-1">



                        <span class="font-mono">${s.filename}</span>



                        ${s.drive_url ? `<a href="${s.drive_url}" target="_blank" class="text-emerald-600 hover:underline font-bold" title="Xem trên Drive"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>` : ''}



                    </div>



                </div>



            </div>



        `).join("");



    }



    modal.classList.remove("hidden");



}



function closeSlidePreviewModal() {



    const modal = document.getElementById("slidePreviewModal");



    if (modal) modal.classList.add("hidden");



}



// Tải ảnh minh họa phong cách từ máy tính lên máy chủ



async function uploadPresetImageFile(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];

    // NGAY LẬP TỨC: hiển thị ảnh người dùng vừa chọn lên khung xem trước
    try {
        const localBlobUrl = URL.createObjectURL(file);
        const imgPrev = document.getElementById("presetForm_imagePreview");
        if (imgPrev) {
            imgPrev.src = localBlobUrl;
        }
    } catch (err) {
        console.warn("Không tạo được blob preview:", err);
    }

    const formData = new FormData();
    formData.append("file", file);

    showToast("Đang tải ảnh minh họa lên server...", "info");

    try {
        const res = await fetch("/api/carousel-presets/upload-image", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (data.success && data.image_url) {
            const imgInput = document.getElementById("presetForm_imageUrl");
            const imgPrev = document.getElementById("presetForm_imagePreview");
            if (imgInput) imgInput.value = data.image_url;
            if (imgPrev) imgPrev.src = data.image_url;
            showToast("Đã tải ảnh minh họa lên thành công!", "success");
        } else {
            showToast("Lỗi tải ảnh: " + (data.message || "Thất bại"), "error");
        }
    } catch (e) {
        showToast("Lỗi kết nối khi tải ảnh: " + e.message, "error");
    } finally {
        input.value = "";
    }
}



// Phóng to ảnh mẫu minh họa phong cách



function viewLargeImage(url, title) {



    const modal = document.getElementById("imageLightboxModal");



    const img = document.getElementById("lightboxImg");



    const cap = document.getElementById("lightboxCaption");



    if (!modal || !img) return;



    img.src = url;



    if (cap) cap.textContent = `Ảnh minh họa phong cách: ${title}`;



    modal.classList.remove("hidden");



}



function closeImageLightbox() {



    const modal = document.getElementById("imageLightboxModal");



    if (modal) modal.classList.add("hidden");



}



function viewLargePresetCurrent() {



    const sel = document.getElementById("field_CarouselPresetId");



    if (!sel) return;



    const chosenId = sel.value;



    const preset = carouselPresets.find(p => p.id === chosenId) || carouselPresets[0];



    if (preset) {



        viewLargeImage(preset.image_url || "/static/images/presets/preset_mark_dao_infographic.jpg", preset.name);



    }



}



// ==========================================



// 15. ĐIỀU HƯỚNG MENU 2 CẤP BÊN TRÁI (SIDEBAR)



// ==========================================



function toggleSidebarMenu(menuId) {



    const submenu = document.getElementById(menuId + 'Submenu');



    const icon = document.getElementById(menuId + 'Icon');



    if (!submenu) return;



    if (submenu.classList.contains('hidden')) {



        submenu.classList.remove('hidden');



        if (icon) icon.style.transform = 'rotate(0deg)';



    } else {



        submenu.classList.add('hidden');



        if (icon) icon.style.transform = 'rotate(-90deg)';



    }



}



function toggleSidebarMobile(forceState = null) {



    const sidebar = document.getElementById('appSidebar');



    const backdrop = document.getElementById('sidebarBackdrop');



    if (!sidebar || !backdrop) return;



    const isClosed = sidebar.classList.contains('-translate-x-full');



    const shouldOpen = forceState !== null ? forceState : isClosed;



    if (shouldOpen) {



        sidebar.classList.remove('-translate-x-full');



        backdrop.classList.remove('hidden');



    } else {



        sidebar.classList.add('-translate-x-full');



        backdrop.classList.add('hidden');



    }



}



function sidebarTriggerAction(actionType) {



    // 1. Tự động đóng menu trên mobile nếu đang mở



    toggleSidebarMobile(false);



    // 2. Chuyển sang tab Nội Dung & Dữ Liệu nếu đang ở tab Integrations



    switchTab('content');



    // Nếu là mở cấu hình ảnh cuộn -> mở modal ngay



    if (actionType === 'config' || actionType === 'preset') {



        setTimeout(() => {



            openPlatformConfigModal();



        }, 100);



        return;



    }



    // 3. Nếu chưa chọn dòng nào, mặc định chọn dòng đầu tiên



    if (currentRowIndex < 0 && tableData.length > 0) {



        selectRow(0);



    }



    // 4. Cuộn mượt mà đến vùng form biên tập & action bar



    const detailSec = document.getElementById('detailSection');



    if (detailSec) {



        detailSec.scrollIntoView({ behavior: 'smooth', block: 'center' });



    }



    // 5. Kích hoạt đúng chức năng yêu cầu



    if (actionType === 'content') {



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

}



// =========================================================



// TIKTOK PUBLISHING LOGIC (ẢNH CUỘN & CHỈ MÌNH TÔI)



// =========================================================



// Helper lấy dữ liệu hiện tại từ form chi tiết
function collectFormData() {
    return {
        "STT": document.getElementById("field_STT") ? document.getElementById("field_STT").value : "",
        "Chủ đề": document.getElementById("field_ChuDe") ? document.getElementById("field_ChuDe").value : "",
        "Yêu cầu chủ đề": document.getElementById("field_YeuCau") ? document.getElementById("field_YeuCau").value : "",
        "Nội dung": document.getElementById("field_NoiDung") ? document.getElementById("field_NoiDung").value : "",
        "Hag tag": document.getElementById("field_HagTag") ? document.getElementById("field_HagTag").value : "",
        "Loại video": document.getElementById("field_LoaiVideo") ? document.getElementById("field_LoaiVideo").value : "",
        "Dạng video": document.getElementById("field_DangVideo") ? document.getElementById("field_DangVideo").value : "",
        "duyệt CĐ và HT": (document.getElementById("field_DuyetCdHt") && document.getElementById("field_DuyetCdHt").checked) ? "x" : "",
        "Duyệt nội dung": (document.getElementById("field_DuyetNoiDung") && document.getElementById("field_DuyetNoiDung").checked) ? "x" : "",
        "Tạo video": (document.getElementById("field_TaoVideo") && document.getElementById("field_TaoVideo").checked) ? "x" : "",
        "Duyệt đăng": (document.getElementById("field_DuyetDang") && document.getElementById("field_DuyetDang").checked) ? "x" : "",
        "Đăng bài": (document.getElementById("field_DangBai") && document.getElementById("field_DangBai").checked) ? "x" : ""
    };
}

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




let currentTikTokReceipt = null;

function copyTextToClipboard(text) {
    if (!text) return;
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).catch(() => {
            fallbackCopyText(text);
        });
    } else {
        fallbackCopyText(text);
    }
}

function fallbackCopyText(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand('copy');
    } catch (err) {
        console.error('Fallback copy error:', err);
    }
    document.body.removeChild(textArea);
}

function copyTikTokCaption() {
    let caption = '';
    if (currentTikTokReceipt && currentTikTokReceipt.caption) {
        caption = currentTikTokReceipt.caption;
    } else {
        const elCap = document.getElementById('ttPubCaption');
        if (elCap) caption = elCap.innerText || elCap.textContent || '';
    }
    if (!caption) {
        showToast('Chưa có nội dung Caption để sao chép!', 'warning', 2500);
        return;
    }
    copyTextToClipboard(caption);
    showToast('✅ Đã sao chép Tiêu đề & Hashtags vào Clipboard!', 'success', 3000);
}

function downloadSlidesZip() {
    const stt = currentTikTokReceipt ? (currentTikTokReceipt.stt || '1') : '1';
    const chu_de = currentTikTokReceipt ? (currentTikTokReceipt.chu_de || '') : '';
    showToast('📦 Đang tải trọn bộ slide ảnh (.zip)...', 'info', 3000);
    window.location.href = `/api/tiktok/download-slides-zip?stt=${encodeURIComponent(stt)}&chu_de=${encodeURIComponent(chu_de)}`;
}

function copyLocalFolderPath() {
    const el = document.getElementById('ttPubLocalPath');
    const path = el ? (el.innerText || el.textContent || '') : '';
    if (!path) {
        showToast('Chưa có đường dẫn thư mục!', 'warning', 2500);
        return;
    }
    copyTextToClipboard(path);
    showToast('✅ Đã sao chép đường dẫn thư mục vào Clipboard!', 'success', 3500);
}

async function openTikTokFolderOnly() {
    const stt = currentTikTokReceipt ? (currentTikTokReceipt.stt || '1') : '1';
    const chu_de = currentTikTokReceipt ? (currentTikTokReceipt.chu_de || '') : '';
    try {
        showToast('Đang mở thư mục slide ảnh trên máy tính...', 'info', 2500);
        const resp = await fetch('/api/tiktok/open-studio-assistant', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stt, chu_de })
        });
        const res = await resp.json();
        if (res.success) {
            showToast('📂 ' + res.message, 'success', 3500);
        } else {
            showToast('Lỗi: ' + (res.message || 'Không thể mở thư mục'), 'error', 3500);
        }
    } catch (e) {
        console.error('Lỗi mở thư mục:', e);
        showToast('Lỗi kết nối mở thư mục: ' + e.message, 'error', 3500);
    }
}

async function launchTikTokStudioAssistant() {
    // 1. Lấy dữ liệu caption và STT
    let caption = '';
    let stt = '1';
    let chu_de = '';
    if (currentTikTokReceipt) {
        caption = currentTikTokReceipt.caption || '';
        stt = currentTikTokReceipt.stt || '1';
        chu_de = currentTikTokReceipt.chu_de || '';
    }
    if (!caption) {
        const elCap = document.getElementById('ttPubCaption');
        if (elCap) caption = elCap.innerText || elCap.textContent || '';
    }

    // 2. MỞ TRÌNH DUYỆT NGAY LẬP TỨC (Đồng bộ trong click context để Chrome/Edge không chặn popup)
    window.open('https://www.tiktok.com/tiktokstudio/upload', '_blank');

    // 3. SAO CHÉP CAPTION VÀO CLIPBOARD TRÌNH DUYỆT TRỰC TIẾP
    if (caption) {
        copyTextToClipboard(caption);
        showToast('✅ Đã sao chép Tiêu đề & Hashtags vào Clipboard!', 'success', 4000);
    }

    // 4. GỌI SERVER MỞ THƯ MỤC TRONG WINDOWS EXPLORER
    try {
        const resp = await fetch('/api/tiktok/open-studio-assistant', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stt, chu_de, caption })
        });
        const res = await resp.json();
        if (res.success) {
            showToast('📂 ' + res.message, 'info', 4000);
        }
    } catch (e) {
        console.error('Lỗi gọi mở thư mục:', e);
    }
}

function openTikTokPublishModal(data) {



    if (!data) return;
    currentTikTokReceipt = data;



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

    const elLocalPath = document.getElementById('ttPubLocalPath');
    if (elLocalPath) {
        const fullP = data.local_abs_dir || data.folder_path || '';
        elLocalPath.textContent = fullP;
        elLocalPath.title = fullP;
    }

    const elTunnel = document.getElementById('ttPubTunnelUrl');
    if (elTunnel) {
        const tunnel = data.tunnel_url || data.public_base_url;
        if (tunnel) {
            elTunnel.innerHTML = `<span class="text-emerald-700 font-bold">🟢 ${tunnel.replace('https://', '')}</span>`;
            elTunnel.title = tunnel;
        } else {
            elTunnel.innerHTML = `<span class="text-amber-600 font-bold">⚪ Chưa bật Ngrok</span>`;
        }
    }

    const elTestImg = document.getElementById('ttPubTestImageLink');
    if (elTestImg) {
        if (data.first_public_image) {
            elTestImg.href = data.first_public_image;
            elTestImg.style.display = 'inline-flex';
        } else {
            elTestImg.style.display = 'none';
        }
    }



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

// ==========================================
// TIKTOK & NGROK INTEGRATION HELPERS
// ==========================================
function copyHelperText(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = (el.innerText || el.textContent || '').trim();
    if (!text || text.includes('...')) {
        showToast('Chưa có đường hầm nào hoạt động!', 'warning', 3000);
        return;
    }
    const copySuccess = () => showToast('📋 Đã sao chép: ' + text, 'success', 3000);
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(copySuccess).catch(() => {
            const temp = document.createElement('textarea');
            temp.value = text;
            document.body.appendChild(temp);
            temp.select();
            document.execCommand('copy');
            document.body.removeChild(temp);
            copySuccess();
        });
    } else {
        const temp = document.createElement('textarea');
        temp.value = text;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
        copySuccess();
    }
}

function updateTikTokHelperLinks(data) {
    const rawUrl = (data && data.tunnel_url) ? data.tunnel_url : (document.getElementById('integ_tiktok_public_url') ? document.getElementById('integ_tiktok_public_url').value : '');
    if (!rawUrl) return;
    const base = rawUrl.trim().replace(/\/+$/, '');
    if (!base.startsWith('http')) return;
    
    const elWeb = document.getElementById('helper_web_url');
    if (elWeb) elWeb.textContent = base + '/';
    
    const elTerms = document.getElementById('helper_terms_url');
    if (elTerms) elTerms.textContent = base + '/terms';
    
    const elPrivacy = document.getElementById('helper_privacy_url');
    if (elPrivacy) elPrivacy.textContent = base + '/privacy';
    
    const elRedirect = document.getElementById('helper_redirect_url');
    if (elRedirect) elRedirect.textContent = base + '/api/tiktok/oauth-callback';
}

async function autoDetectNgrokTunnel() {
    const btn = document.querySelector('[onclick="autoDetectNgrokTunnel()"]');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-amber-500"></i><span>Đang quét...</span>`;
    }

    try {
        showToast('Đang quét đường hầm Cloudflare / Ngrok...', 'info', 2500);
        const resp = await fetch('/api/tiktok/tunnel-status', {
            headers: { 'Accept': 'application/json' }
        });

        if (!resp.ok) {
            throw new Error(`Máy chủ trả về mã HTTP ${resp.status}`);
        }

        const cType = resp.headers.get('content-type') || '';
        if (!cType.includes('application/json')) {
            throw new Error('Máy chủ phản hồi HTML thay vì JSON. Vui lòng tải lại trang.');
        }

        const data = await resp.json();
        if (data.success && data.tunnel_url) {
            const input = document.getElementById('integ_tiktok_public_url');
            if (input) input.value = data.tunnel_url;

            updateTikTokHelperLinks(data);

            try {
                await fetch('/api/tiktok/apply-tunnel-url', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tunnel_url: data.tunnel_url })
                });
            } catch (postErr) {
                console.warn('Lỗi lưu cấu hình tunnel:', postErr);
            }

            const typeLabel = data.tunnel_type === 'cloudflare' ? 'Cloudflare Tunnel' : (data.tunnel_type === 'ngrok' ? 'Ngrok' : 'Đường hầm');
            showToast(`✅ Đã nhận diện ${typeLabel} thành công: ${data.tunnel_url}`, 'success', 5000);
        } else {
            showToast('⚠️ Chưa phát hiện đường hầm HTTPS nào đang chạy! Hãy click chạy file Chay_Cloudflare_Tunnel.bat hoặc Chay_Ngrok_TikTok.bat.', 'warning', 6000);
        }
    } catch (e) {
        console.error('Lỗi nhận diện đường hầm:', e);
        showToast('Lỗi nhận diện đường hầm: ' + (e.message || e), 'error', 5000);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    }
}

// Lắng nghe sự kiện gõ vào input để tự động cập nhật bảng 4 link
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('integ_tiktok_public_url');
    if (input) {
        input.addEventListener('input', () => {
            updateTikTokHelperLinks({ tunnel_url: input.value });
        });
        if (input.value) {
            updateTikTokHelperLinks({ tunnel_url: input.value });
        }
    }
});

async function authorizeTikTokOAuth() {
    try {
        const resp = await fetch('/api/tiktok/oauth-url');
        const data = await resp.json();
        if (data.success && data.auth_url) {
            window.open(data.auth_url, '_blank');
        } else {
            showToast('Lỗi lấy liên kết ủy quyền TikTok: ' + (data.message || 'Không xác định'), 'error', 4000);
        }
    } catch (e) {
        console.error('Lỗi ủy quyền TikTok:', e);
        showToast('Lỗi kết nối ủy quyền: ' + e.message, 'error', 4000);
    }
}
