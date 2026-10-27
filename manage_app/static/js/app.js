const { createApp, ref, computed, onMounted, watch } = Vue;
createApp({
    setup() {
        // TAB HIỆN TẠI: 'scanner' (Tab 1) | 'settings' (Tab 2)
        // ==================== ĐIỀU HƯỚNG MENU BÊN TRÁI (LEFT SIDEBAR) ====================
        // 'admin_checker' | 'admin_composer' | 'scanner' | 'uploader' | 'policy_settings' | 'general_settings'
        const urlParams = new URLSearchParams(window.location.search);
        const urlMenu = urlParams.get('menu') || window.location.hash.replace('#', '');
        const validMenus = ['office', 'admin_checker', 'admin_composer', 'scanner', 'uploader', 'policy_settings', 'general_settings', 'ai_assistants_settings', 'ai_assistant_chat', 'secretaries_settings', 'music_settings', 'chief_secretary_reminders', 'chief_secretary_kpi', 'chief_secretary_settings'];
        const activeMenu = ref((validMenus.includes(urlMenu) || urlMenu.startsWith('asst_')) ? urlMenu : 'office');
        const isSidebarCollapsed = ref(false);
        // Mở / Đóng các nhóm menu cấp 1 (expand / collapse)
        const menuGroupsOpen = ref({
            admin_docs: true,
            policy_docs: true,
            ai_assistants: true,
            ai_secretaries: true,
            chief_secretary: true,
            general_settings: true
        });
        const toggleMenuGroup = (groupKey) => {
            if (menuGroupsOpen.value[groupKey] !== undefined) {
                menuGroupsOpen.value[groupKey] = !menuGroupsOpen.value[groupKey];
            }
        };
        const activeTab = computed({
            get: () => activeMenu.value,
            set: (v) => { 
                if (v === 'settings') {
                    activeMenu.value = 'general_settings';
                } else {
                    activeMenu.value = v; 
                }
            }
        });
        // ==================== TAB 1: QUÉT VÀ TẢI VĂN BẢN ====================
        // Danh mục mặc định chuẩn 9 từ khóa ngành thuế theo yêu cầu
        const suggestedTags = [
            'thuế',
            'hộ kinh doanh',
            'thu nhập cá nhân',
            'doanh nghiệp',
            'tổ chức',
            'giá trị gia tăng',
            'thu nhập doanh nghiệp',
            'giao dịch liên kết',
            'hóa đơn điện tử'
        ];
        const fieldsInput = ref('thuế, hộ kinh doanh, thu nhập cá nhân, doanh nghiệp, tổ chức, giá trị gia tăng, thu nhập doanh nghiệp, giao dịch liên kết, hóa đơn điện tử');
        // Tính ngày mặc định: 7 ngày trước đến ngày hiện hành
        const formatD = (d) => {
            const day = String(d.getDate()).padStart(2, '0');
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const year = d.getFullYear();
            return `${day}/${month}/${year}`;
        };
        const now = new Date();
        const todayStr = formatD(now);
        // Mặc định Từ ngày, Đến ngày là ngày hiện tại
        const fromDate = ref(todayStr);
        const toDate = ref(todayStr);
        const datePreset = ref('today');
        const isScanning = ref(false);
        const hasScanned = ref(false);
        const autoSaveStatus = ref('Đã lưu');
        let autoSaveTimer = null;
        // Kết quả quét
        const documents = ref([]);
        const selectedDocIds = ref([]);
        const searchQuery = ref('');
        const agencyFilter = ref('all');
        const sourceFilter = ref('all');
        const typeFilter = ref('all');
        const selectedFolderForBatch = ref('1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK');
        // Modal chi tiết văn bản
        const previewDoc = ref(null);
        // Tiến độ nén và tải về máy chung (ZIP)
        const isDownloadingBatch = ref(false);
        // Modal tiến độ Tải về & Đẩy lên Google Drive
        const uploadModalOpen = ref(false);
        const isUploading = ref(false);
        const uploadResults = ref([]);
        const uploadSummary = ref({ total: 0, success: 0, fail: 0 });
        // ==================== TAB 2: THIẾT LẬP CẤU HÌNH ====================
        const driveStatus = ref({
            connected: false,
            user: null
        });
        const allDriveFolders = ref([]);
        const filterTaxOnly = ref(localStorage.getItem('filterTaxOnly') !== 'false');
        const allNotebooks = ref([]);
        const updateTaxFilteredLists = () => {
            if (filterTaxOnly.value) {
                folders.value = allDriveFolders.value.filter(f => f.is_tax || (f.name && f.name.toLowerCase().includes('tax')) || (f.raw_name && f.raw_name.toLowerCase().includes('tax')));
                notebooks.value = allNotebooks.value.filter(n => n.is_tax || (n.name && n.name.toLowerCase().includes('tax')));
            } else {
                folders.value = [...allDriveFolders.value];
                notebooks.value = [...allNotebooks.value];
            }
        };
        const handleTaxFilterToggle = () => {
            localStorage.setItem('filterTaxOnly', filterTaxOnly.value ? 'true' : 'false');
            updateTaxFilteredLists();
        };
        const folders = ref([
            { id: '1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK', name: '📁 Tax_Nghiệp vụ thuế ⭐ [Mặc định]' }
        ]);
        const defaultFolderId = ref('1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK');
        const defaultFolderName = ref('📁 Tax_Nghiệp vụ thuế');
        const isTestingConnection = ref(false);
        // Tạo thư mục mới trên Drive
        const newFolderName = ref('');
        const newFolderParent = ref('root');
        const isCreatingFolder = ref(false);
        // Form thông tin xác thực
        const clientIdInput = ref('');
        const clientSecretInput = ref('');
        const refreshTokenInput = ref('');
        const isSavingDriveCreds = ref(false);
        // ==================== QUẢN LÝ DANH MỤC WEBSITE NGUỒN ====================
        const sources = ref([]);
        const newSourceDomain = ref('');
        const newSourceName = ref('');
        const isSavingSource = ref(false);
        // ==================== NOTEBOOKLM TÍCH HỢP ====================
        const notebooks = ref([
            { id: 'nb_tax_default', name: 'Tax_Nghiệp vụ thuế', url: 'https://notebooklm.google.com/', folder_name: 'Tax_Nghiệp vụ thuế', description: 'Kho tri thức nghiệp vụ thuế & chính sách tổng hợp (Mặc định)', is_default: true },
            { id: 'nb_tax_invoice', name: 'Chính sách Thuế & Hóa đơn điện tử', url: 'https://notebooklm.google.com/', folder_name: 'Chính sách Thuế & Hóa đơn điện tử', description: 'Nghị định 123, Thông tư 78, hóa đơn điện tử', is_default: false },
            { id: 'nb_tax_cit', name: 'Thuế TNDN, Chống chuyển giá & Giao dịch liên kết', url: 'https://notebooklm.google.com/', folder_name: 'Thuế TNDN & Giao dịch liên kết', description: 'Nghị định 132, chi phí được trừ, ưu đãi thuế TNDN', is_default: false },
            { id: 'nb_tax_pit', name: 'Quyết toán Thuế TNCN & Hộ kinh doanh', url: 'https://notebooklm.google.com/', folder_name: 'Thuế TNCN & Hộ kinh doanh', description: 'Thông tư 111, Thông tư 40, giảm trừ gia cảnh', is_default: false },
            { id: 'nb_tax_vat', name: 'Thuế GTGT, Xuất nhập khẩu & Tiền thuê đất', url: 'https://notebooklm.google.com/', folder_name: 'Thuế GTGT & Tiền thuê đất', description: 'Giảm thuế GTGT 2%, hoàn thuế GTGT', is_default: false },
            { id: 'nb_tax_law', name: 'Pháp luật Thuế, Doanh nghiệp & Đầu tư 2026', url: 'https://notebooklm.google.com/', folder_name: 'Pháp luật Thuế & Doanh nghiệp', description: 'Luật Quản lý thuế số 38, Luật Doanh nghiệp', is_default: false },
            { id: 'nb_tax_all', name: 'CSDL Văn bản Pháp quy Toàn văn (Tổng hợp)', url: 'https://notebooklm.google.com/', folder_name: 'CSDL Văn bản Pháp quy', description: 'Tổng hợp toàn bộ các văn bản quy phạm pháp luật', is_default: false }
        ]);
        const defaultNotebookId = ref('nb_tax_default');
        const selectedNotebookForBatch = ref('nb_tax_default');
        const batchUploadedNotebookId = ref('nb_tax_default');
        const notebooklmStorageDir = ref('C:/NotebookLM_Sources');
        // Tiến trình và Modal Lưu lên NotebookLM
        const isSavingNotebook = ref(false);
        const isSavingUploadedToNotebook = ref(false);
        const notebookModalOpen = ref(false);
        const notebookSummary = ref({ total: 0, success: 0, fail: 0, notebookName: '' });
        const notebookResults = ref([]);
        // Quản lý Notebooks trong Tab 2
        const newNotebookName = ref('');
        const newNotebookUrl = ref('https://notebooklm.google.com/');
        const newNotebookDesc = ref('');
        const isSavingNotebookItem = ref(false);
        // Tự động hóa NotebookLM (100% tự động qua notebooklm-py)
        const notebooklmAutoStatus = ref({ connected: false, email: '', message: '' });
        const isCheckingAutoStatus = ref(false);
        const isTriggeringLogin = ref(false);
        const isSyncingGoogleNotebooks = ref(false);

        // Thông báo Toast nhỏ phong cách Cổng Dịch vụ công (Xanh, Trắng, Không dùng đỏ)
        const showToast = (message, icon = 'success') => {
            if (window.Swal) {
                const Toast = Swal.mixin({
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000,
                    timerProgressBar: true,
                    background: '#ffffff',
                    color: '#003b73',
                    customClass: {
                        popup: 'border border-[#b9d2ec] shadow-lg text-xs font-semibold'
                    }
                });
                Toast.fire({ icon, title: message });
            } else {
                alert(message);
            }
        };
        // ==================== KHỞI TẠO & AUTO-SAVE ====================
        const initApp = async () => {
            // 1. Nạp từ localStorage trước nếu có
            const localSavedFields = localStorage.getItem('manage_app_last_fields');
            if (localSavedFields) {
                fieldsInput.value = localSavedFields;
            }
            // 2. Lấy cấu hình hệ thống từ Backend
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                if (data.success) {
                    if (data.last_fields) {
                        fieldsInput.value = data.last_fields;
                    }
                    if (data.default_folder_id) {
                        defaultFolderId.value = data.default_folder_id;
                        defaultFolderName.value = data.default_folder_name || '📁 My Drive (Thư mục gốc)';
                        selectedFolderForBatch.value = data.default_folder_id;
                    }
                    if (data.sources) {
                        sources.value = data.sources;
                    }
                    if (data.notebooks) {
                        notebooks.value = data.notebooks;
                    }
                    if (data.default_notebook_id) {
                        defaultNotebookId.value = data.default_notebook_id;
                        selectedNotebookForBatch.value = data.default_notebook_id;
                        batchUploadedNotebookId.value = data.default_notebook_id;
                    }
                    if (data.notebooklm_storage_dir) {
                        notebooklmStorageDir.value = data.notebooklm_storage_dir;
                    }
                    driveStatus.value.connected = data.drive_connected;
                    driveStatus.value.user = data.drive_user;
                }
            } catch (e) {
                console.error('Lỗi nạp config:', e);
            }
            // 3. Nạp danh sách thư mục Google Drive sạch
            loadDriveFolders();
            // 4. Nạp danh mục website nguồn
            loadSources();
            // 5. Nạp danh mục NotebookLM
            loadNotebooks();
            checkNotebookLMAutoStatus();
            // Lưu ý: Mặc định mở lên không thực hiện dò quét tự động
        };
        // Tự động lưu giá trị Lĩnh vực nhập sau cùng
        const handleFieldsChange = () => {
            autoSaveStatus.value = 'Đang lưu...';
            localStorage.setItem('manage_app_last_fields', fieldsInput.value);
            if (autoSaveTimer) clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(async () => {
                try {
                    await fetch('/api/config/save-fields', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ fields: fieldsInput.value })
                    });
                    autoSaveStatus.value = 'Đã lưu cấu hình';
                } catch (e) {
                    autoSaveStatus.value = 'Lỗi lưu';
                }
            }, 600);
        };
        // Chọn nhanh Tag lĩnh vực chuẩn 9 mục
        const toggleTag = (tag) => {
            const current = fieldsInput.value ? fieldsInput.value.split(',').map(s => s.trim()).filter(Boolean) : [];
            const index = current.findIndex(s => s.toLowerCase() === tag.toLowerCase());
            if (index >= 0) {
                current.splice(index, 1);
            } else {
                current.push(tag);
            }
            fieldsInput.value = current.join(', ');
            handleFieldsChange();
        };
        const isTagSelected = (tag) => {
            if (!fieldsInput.value) return false;
            return fieldsInput.value.toLowerCase().includes(tag.toLowerCase());
        };
        // Thiết lập bộ lọc ngày nhanh chuẩn: Hôm nay, 1 tuần qua, 2 tuần qua, 30 ngày qua, năm hiện hành, tất cả văn bản
        const applyDatePreset = (preset) => {
            datePreset.value = preset;
            const current = new Date();
            toDate.value = formatD(current);
            if (preset === 'today') {
                fromDate.value = formatD(current);
            } else if (preset === '1_week') {
                const past = new Date(current.getTime() - 7 * 24 * 60 * 60 * 1000);
                fromDate.value = formatD(past);
            } else if (preset === '2_weeks') {
                const past = new Date(current.getTime() - 14 * 24 * 60 * 60 * 1000);
                fromDate.value = formatD(past);
            } else if (preset === '30_days') {
                const past = new Date(current.getTime() - 30 * 24 * 60 * 60 * 1000);
                fromDate.value = formatD(past);
            } else if (preset === 'current_year') {
                fromDate.value = `01/01/${current.getFullYear()}`;
            } else if (preset === 'all_time') {
                fromDate.value = '01/01/2020';
            }
            // Tự động quét lại để cập nhật bảng kết quả
            runScan();
        };
        // ==================== THAO TÁC QUÉT VĂN BẢN ====================
        const runScan = async () => {
            if (!fieldsInput.value.trim()) {
                showToast('Vui lòng nhập hoặc chọn ít nhất một lĩnh vực cần quét.', 'warning');
                return;
            }
            isScanning.value = true;
            hasScanned.value = true;
            try {
                const res = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        fields: fieldsInput.value,
                        from_date: fromDate.value,
                        to_date: toDate.value
                    })
                });
                const data = await res.json();
                if (data.success) {
                    documents.value = data.documents.map(d => ({
                        ...d,
                        selected_folder_id: d.selected_folder_id || defaultFolderId.value || 'root',
                        selected_notebook_id: d.selected_notebook_id || selectedNotebookForBatch.value || defaultNotebookId.value || 'nb_tax_default',
                        upload_status: 'idle',
                        notebook_status: 'idle',
                        is_downloaded: false,
                        drive_link: ''
                    }));
                    selectedDocIds.value = [];
                    showToast(`Quét hoàn tất: Tìm thấy ${data.total} văn bản từ các website nguồn đã chọn.`, 'success');
                } else {
                    showToast(data.message || 'Lỗi trong quá trình quét văn bản', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối máy chủ khi quét', 'error');
            } finally {
                isScanning.value = false;
            }
        };
        // Danh sách hiển thị sau khi lọc tìm kiếm nội bộ
        const filteredDocuments = computed(() => {
            return documents.value.filter(doc => {
                const q = searchQuery.value.toLowerCase().trim();
                const matchSearch = !q ||
                    doc.doc_number.toLowerCase().includes(q) ||
                    doc.title.toLowerCase().includes(q) ||
                    doc.issuing_body.toLowerCase().includes(q) ||
                    doc.summary.toLowerCase().includes(q) ||
                    (doc.source && doc.source.toLowerCase().includes(q));
                const matchAgency = agencyFilter.value === 'all' || doc.issuing_body === agencyFilter.value;
                const matchSource = sourceFilter.value === 'all' || doc.source === sourceFilter.value;
                const matchType = typeFilter.value === 'all' || doc.doc_type === typeFilter.value;
                return matchSearch && matchAgency && matchSource && matchType;
            });
        });
        // Danh sách các cơ quan ban hành độc nhất để lọc
        const uniqueAgencies = computed(() => {
            const set = new Set();
            documents.value.forEach(d => { if (d.issuing_body) set.add(d.issuing_body); });
            return Array.from(set);
        });
        // Danh sách nguồn website xuất hiện trong kết quả
        const uniqueSources = computed(() => {
            const set = new Set();
            documents.value.forEach(d => { if (d.source) set.add(d.source); });
            return Array.from(set);
        });
        // ==================== CHECKBOX & SELECTION ====================
        const isAllSelected = computed(() => {
            if (filteredDocuments.value.length === 0) return false;
            return filteredDocuments.value.every(d => selectedDocIds.value.includes(d.id));
        });
        const toggleSelectAll = () => {
            if (isAllSelected.value) {
                const currentIds = new Set(filteredDocuments.value.map(d => d.id));
                selectedDocIds.value = selectedDocIds.value.filter(id => !currentIds.has(id));
            } else {
                const set = new Set(selectedDocIds.value);
                filteredDocuments.value.forEach(d => set.add(d.id));
                selectedDocIds.value = Array.from(set);
            }
        };
        const toggleSelectDoc = (id) => {
            const idx = selectedDocIds.value.indexOf(id);
            if (idx >= 0) {
                selectedDocIds.value.splice(idx, 1);
            } else {
                selectedDocIds.value.push(id);
            }
        };
        // Áp dụng nhanh thư mục Drive cho toàn bộ dòng được tick
        const applyBatchFolder = () => {
            if (selectedDocIds.value.length === 0) {
                showToast('Vui lòng tick chọn ít nhất một văn bản để đổi thư mục.', 'warning');
                return;
            }
            const folder = folders.value.find(f => f.id === selectedFolderForBatch.value);
            const folderName = folder ? folder.name : 'Thư mục đã chọn';
            documents.value.forEach(doc => {
                if (selectedDocIds.value.includes(doc.id)) {
                    doc.selected_folder_id = selectedFolderForBatch.value;
                }
            });
            showToast(`Đã áp dụng thư mục "${folderName}" cho ${selectedDocIds.value.length} văn bản được chọn.`, 'success');
        };
        // Lấy tên Notebook theo ID
        const getNotebookName = (id) => {
            const nb = notebooks.value.find(n => n.id === id);
            return nb ? nb.name : 'Tax_Nghiệp vụ thuế';
        };
        // Áp dụng nhanh Notebook cho toàn bộ dòng được tick
        const applyBatchNotebook = () => {
            if (selectedDocIds.value.length === 0) {
                showToast('Vui lòng tick chọn ít nhất một văn bản để đổi Notebook.', 'warning');
                return;
            }
            const nbName = getNotebookName(selectedNotebookForBatch.value);
            documents.value.forEach(doc => {
                if (selectedDocIds.value.includes(doc.id)) {
                    doc.selected_notebook_id = selectedNotebookForBatch.value;
                }
            });
            showToast(`Đã áp dụng Notebook "${nbName}" cho ${selectedDocIds.value.length} văn bản được chọn.`, 'success');
        };
        // ==================== NÚT TẢI VỀ MÁY CHUNG CHO TẤT CẢ VĂN BẢN ĐÃ CHỌN (ZIP) ====================
        const downloadBatchZip = async () => {
            if (selectedDocIds.value.length === 0) {
                showToast('Vui lòng tick chọn ít nhất một văn bản để tải về máy.', 'warning');
                return;
            }
            const docsToDownload = documents.value.filter(d => selectedDocIds.value.includes(d.id));
            isDownloadingBatch.value = true;
            showToast(`Đang đóng gói ${docsToDownload.length} văn bản chuẩn thể thức dạng ZIP...`, 'info');
            try {
                const res = await fetch('/api/documents/download-batch-zip', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ documents: docsToDownload })
                });
                if (!res.ok) throw new Error('Lỗi máy chủ khi tạo file ZIP');
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const dStr = formatD(new Date()).replace(/\//g, '');
                a.download = `VanBan_PhapLuat_Thue_${dStr}.zip`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                // Chuyển màu sắc của các dòng dữ liệu đó qua màu xanh nhạt theo yêu cầu!
                docsToDownload.forEach(d => {
                    d.is_downloaded = true;
                });
                showToast(`Đã tải về máy thành công trọn bộ ${docsToDownload.length} văn bản (file ZIP)!`, 'success');
            } catch (e) {
                showToast('Lỗi khi tải trọn bộ file ZIP về máy', 'error');
            } finally {
                isDownloadingBatch.value = false;
            }
        };
        // Tải văn bản đơn lẻ trực tiếp về máy (bảo đảm định dạng và tên file chính xác từ server)
        const downloadDocLocally = async (doc) => {
            try {
                showToast(`Đang chuẩn bị file đính kèm: ${doc.doc_number}...`, 'info');
                const res = await fetch(`/api/documents/download-local/${doc.id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ document: doc })
                });
                if (!res.ok) throw new Error('Lỗi từ máy chủ khi tạo file');
                // Lấy tên file thực tế từ Content-Disposition header nếu có
                let filename = `${doc.doc_number.replace(/[/\\:*?"<>| ]/g, '_')}_${doc.field || 'Chung'}.pdf`;
                const disposition = res.headers.get('content-disposition');
                if (disposition && disposition.indexOf('filename=') !== -1) {
                    const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                    if (match && match[1]) {
                        filename = match[1].replace(/['"]/g, '');
                    }
                }
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                
                // Đánh dấu đã tải để chuyển màu dòng sang xanh nhạt theo yêu cầu
                doc.is_downloaded = true;
                showToast(`Đã tải thành công văn bản: ${filename}`, 'success');
            } catch (e) {
                showToast('Lỗi khi tải file văn bản về máy', 'error');
            }
        };
        // ==================== TẢI VỀ & LƯU LÊN GOOGLE DRIVE ====================
        const uploadSelectedToDrive = async () => {
            if (selectedDocIds.value.length === 0) {
                showToast('Vui lòng tick chọn ít nhất một văn bản để lưu lên Google Drive.', 'warning');
                return;
            }
            if (!driveStatus.value.connected) {
                if (window.Swal) {
                    Swal.fire({
                        title: 'Chưa kết nối Google Drive',
                        text: 'Bạn cần kết nối tài khoản Google Drive ở Tab "Thiết lập cấu hình" trước khi lưu trữ.',
                        icon: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Đến Tab Thiết lập cấu hình',
                        cancelButtonText: 'Hủy'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            activeTab.value = 'settings';
                        }
                    });
                } else {
                    activeTab.value = 'settings';
                }
                return;
            }
            const docsToUpload = documents.value.filter(d => selectedDocIds.value.includes(d.id));
            uploadModalOpen.value = true;
            isUploading.value = true;
            uploadResults.value = [];
            uploadSummary.value = {
                total: docsToUpload.length,
                success: 0,
                fail: 0
            };
            docsToUpload.forEach(d => {
                d.upload_status = 'uploading';
            });
            try {
                const res = await fetch('/api/documents/upload-drive', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ documents: docsToUpload })
                });
                const data = await res.json();
                if (data.success || data.results) {
                    uploadResults.value = data.results || [];
                    uploadSummary.value = {
                        total: docsToUpload.length,
                        success: data.success_count || 0,
                        fail: data.fail_count || 0
                    };
                    (data.results || []).forEach(r => {
                        const targetDoc = documents.value.find(d => d.id === r.id);
                        if (targetDoc) {
                            if (r.status === 'success') {
                                targetDoc.upload_status = 'success';
                                targetDoc.drive_link = r.drive_link;
                                targetDoc.is_downloaded = true; // Đổi màu dòng qua xanh nhạt
                            } else {
                                targetDoc.upload_status = 'error';
                            }
                        }
                    });
                    showToast(data.message, data.success_count > 0 ? 'success' : 'error');
                } else {
                    showToast(data.message || 'Lỗi khi đẩy file lên Google Drive', 'error');
                }
            } catch (e) {
                showToast('Lỗi mạng hoặc máy chủ khi tải lên Drive', 'error');
            } finally {
                isUploading.value = false;
            }
        };
        // ==================== LƯU LÊN NOTEBOOKLM (TAB 1) ====================
        const uploadSelectedToNotebookLM = async () => {
            if (selectedDocIds.value.length === 0) {
                showToast('Vui lòng tick chọn ít nhất một văn bản để lưu lên NotebookLM.', 'warning');
                return;
            }
            const docsToSave = documents.value.filter(d => selectedDocIds.value.includes(d.id));
            
            docsToSave.forEach(d => {
                if (!d.selected_notebook_id) {
                    d.selected_notebook_id = defaultNotebookId.value || 'nb_tax_default';
                }
            });
            notebookModalOpen.value = true;
            isSavingNotebook.value = true;
            notebookResults.value = [];
            notebookSummary.value = {
                total: docsToSave.length,
                success: 0,
                fail: 0,
                notebookName: getNotebookName(selectedNotebookForBatch.value)
            };
            try {
                const res = await fetch('/api/documents/upload-notebooklm', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        documents: docsToSave,
                        selected_notebook_id: selectedNotebookForBatch.value
                    })
                });
                const data = await res.json();
                if (data.success || data.results) {
                    notebookResults.value = data.results || [];
                    notebookSummary.value = {
                        total: docsToSave.length,
                        success: data.success_count || 0,
                        fail: data.fail_count || 0,
                        notebookName: getNotebookName(selectedNotebookForBatch.value)
                    };
                    (data.results || []).forEach(r => {
                        const targetDoc = documents.value.find(d => d.id === r.id);
                        if (targetDoc) {
                            if (r.status !== 'error' && r.success !== false) {
                                targetDoc.notebook_status = 'success';
                                targetDoc.notebook_name = r.notebook_name;
                                targetDoc.notebook_url = r.notebook_url;
                                targetDoc.is_downloaded = true; // Đổi màu dòng qua xanh nhạt
                                if (r.drive_link) {
                                    targetDoc.drive_link = r.drive_link;
                                    targetDoc.upload_status = 'success';
                                }
                            } else {
                                targetDoc.notebook_status = 'error';
                            }
                        }
                    });
                    showToast(data.message, data.success_count > 0 ? 'success' : 'error');
                } else {
                    showToast(data.message || 'Lỗi khi lưu văn bản lên NotebookLM', 'error');
                }
            } catch (e) {
                showToast('Lỗi mạng hoặc kết nối máy chủ khi lưu vào NotebookLM: ' + e.message, 'error');
            } finally {
                isSavingNotebook.value = false;
            }
        };
        // ==================== TAB 2: THIẾT LẬP GOOGLE DRIVE ====================
        const loadDriveFolders = async () => {
            try {
                const res = await fetch('/api/drive/folders');
                const data = await res.json();
                if (data.success && data.folders && data.folders.length > 0) {
                    allDriveFolders.value = data.folders;
                    updateTaxFilteredLists();
                    const matched = folders.value.find(f => f.id === defaultFolderId.value);
                    if (matched) {
                        defaultFolderName.value = matched.name;
                    } else if (folders.value.length > 0) {
                        const taxDefault = folders.value.find(f => f.raw_name === 'Tax_Nghiệp vụ thuế' || (f.name && f.name.includes('Tax_Nghiệp vụ thuế')));
                        if (taxDefault) {
                            defaultFolderId.value = taxDefault.id;
                            defaultFolderName.value = taxDefault.name;
                            selectedFolderForBatch.value = taxDefault.id;
                        }
                    }
                }
            } catch (e) {
                console.error('Lỗi lấy folders:', e);
            }
        };
        const testDriveConnection = async () => {
            isTestingConnection.value = true;
            try {
                const res = await fetch('/api/drive/test-connection', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    driveStatus.value.connected = true;
                    driveStatus.value.user = data.user;
                    if (data.folders && data.folders.length > 0) {
                        folders.value = data.folders;
                        const matched = data.folders.find(f => f.id === defaultFolderId.value);
                        if (matched) {
                            defaultFolderName.value = matched.name;
                        }
                    }
                    showToast(data.message, 'success');
                } else {
                    driveStatus.value.connected = false;
                    showToast(data.message, 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối kiểm tra Google Drive', 'error');
            } finally {
                isTestingConnection.value = false;
            }
        };
        const importLocalConfig = async () => {
            try {
                const res = await fetch('/api/drive/import-local', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    testDriveConnection();
                } else {
                    showToast(data.message, 'warning');
                }
            } catch (e) {
                showToast('Lỗi khi tự động phát hiện cấu hình', 'error');
            }
        };
        const saveDriveCredentials = async () => {
            if (!clientIdInput.value.trim() || !clientSecretInput.value.trim()) {
                showToast('Vui lòng điền Client ID và Client Secret.', 'warning');
                return;
            }
            isSavingDriveCreds.value = true;
            try {
                const res = await fetch('/api/drive/save-credentials', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        client_id: clientIdInput.value,
                        client_secret: clientSecretInput.value,
                        refresh_token: refreshTokenInput.value
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    testDriveConnection();
                } else {
                    showToast(data.message, 'error');
                }
            } catch (e) {
                showToast('Lỗi lưu cấu hình Google Drive', 'error');
            } finally {
                isSavingDriveCreds.value = false;
            }
        };
        const createNewDriveFolder = async () => {
            if (!newFolderName.value.trim()) {
                showToast('Vui lòng nhập tên thư mục cần tạo.', 'warning');
                return;
            }
            isCreatingFolder.value = true;
            try {
                const res = await fetch('/api/drive/create-folder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        folder_name: newFolderName.value,
                        parent_id: newFolderParent.value
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    newFolderName.value = '';
                    await loadDriveFolders();
                } else {
                    showToast(data.message, 'error');
                }
            } catch (e) {
                showToast('Lỗi tạo thư mục Google Drive', 'error');
            } finally {
                isCreatingFolder.value = false;
            }
        };
        const setDefaultFolder = async (folder) => {
            try {
                const res = await fetch('/api/config/set-default-folder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        folder_id: folder.id,
                        folder_name: folder.name
                    })
                });
                const data = await res.json();
                if (data.success) {
                    defaultFolderId.value = folder.id;
                    defaultFolderName.value = folder.name;
                    selectedFolderForBatch.value = folder.id;
                    showToast(data.message, 'success');
                }
            } catch (e) {
                showToast('Lỗi đặt thư mục mặc định', 'error');
            }
        };
        // ==================== QUẢN LÝ DANH MỤC WEBSITE NGUỒN ====================
        const loadSources = async () => {
            try {
                const res = await fetch('/api/sources');
                const data = await res.json();
                if (data.success && data.sources) {
                    sources.value = data.sources;
                }
            } catch (e) {
                console.error('Lỗi nạp danh mục sources:', e);
            }
        };
        const addSource = async () => {
            if (!newSourceDomain.value.trim()) {
                showToast('Vui lòng nhập tên miền website (ví dụ: gdt.gov.vn)', 'warning');
                return;
            }
            isSavingSource.value = true;
            try {
                const res = await fetch('/api/sources', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        domain: newSourceDomain.value,
                        name: newSourceName.value
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    newSourceDomain.value = '';
                    newSourceName.value = '';
                    loadSources();
                } else {
                    showToast(data.message, 'warning');
                }
            } catch (e) {
                showToast('Lỗi khi thêm website nguồn', 'error');
            } finally {
                isSavingSource.value = false;
            }
        };
        const toggleSource = async (id) => {
            try {
                const res = await fetch('/api/sources/toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_id: id })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    await loadSources();
                    runScan();
                }
            } catch (e) {
                showToast('Lỗi bật/tắt website nguồn', 'error');
            }
        };
        const enableAllSources = async () => {
            try {
                const res = await fetch('/api/sources/enable-all', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    sources.value = data.sources;
                    showToast('Đã bật tất cả 5 website nguồn!', 'success');
                    runScan();
                }
            } catch (e) {
                showToast('Lỗi bật tất cả website nguồn', 'error');
            }
        };
        const deleteSource = async (id) => {
            if (window.Swal) {
                const result = await Swal.fire({
                    title: 'Xác nhận xóa website nguồn?',
                    text: 'Hệ thống sẽ không dò quét văn bản từ trang web này nữa.',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonText: 'Xóa',
                    cancelButtonText: 'Hủy'
                });
                if (!result.isConfirmed) return;
            }
            try {
                const res = await fetch(`/api/sources/${id}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    loadSources();
                }
            } catch (e) {
                showToast('Lỗi khi xóa website nguồn', 'error');
            }
        };
        const resetSources = async () => {
            try {
                const res = await fetch('/api/sources/reset', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    sources.value = data.sources;
                    showToast(data.message, 'success');
                }
            } catch (e) {
                showToast('Lỗi khôi phục danh mục website mặc định', 'error');
            }
        };
        // ==================== QUẢN LÝ NOTEBOOKLM (TAB 2) ====================
        const loadNotebooks = async () => {
            try {
                const res = await fetch('/api/notebooklm/list');
                const data = await res.json();
                if (data.success && data.notebooks) {
                    allNotebooks.value = data.notebooks;
                    updateTaxFilteredLists();
                    if (data.default_notebook_id) {
                        defaultNotebookId.value = data.default_notebook_id;
                        selectedNotebookForBatch.value = data.default_notebook_id;
                        batchUploadedNotebookId.value = data.default_notebook_id;
                    }
                    if (data.storage_dir) {
                        notebooklmStorageDir.value = data.storage_dir;
                    }
                }
            } catch (e) {
                console.error('Lỗi nạp danh sách NotebookLM:', e);
            }
        };
        const saveNewNotebook = async () => {
            if (!newNotebookName.value.trim()) {
                showToast('Vui lòng nhập tên Notebook.', 'warning');
                return;
            }
            isSavingNotebookItem.value = true;
            try {
                const res = await fetch('/api/notebooklm/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: newNotebookName.value.trim(),
                        url: newNotebookUrl.value.trim() || 'https://notebooklm.google.com/',
                        description: newNotebookDesc.value.trim()
                    })
                });
                const data = await res.json();
                if (data.success) {
                    notebooks.value = data.notebooks || [];
                    newNotebookName.value = '';
                    newNotebookDesc.value = '';
                    showToast(data.message || 'Đã thêm notebook mới thành công!', 'success');
                } else {
                    showToast(data.message || 'Lỗi khi thêm notebook', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối khi lưu notebook: ' + e.message, 'error');
            } finally {
                isSavingNotebookItem.value = false;
            }
        };
        const deleteNotebookItem = async (notebookId) => {
            if (notebooks.value.length <= 1) {
                showToast('Hệ thống cần ít nhất 1 notebook, không thể xóa.', 'warning');
                return;
            }
            if (window.Swal) {
                const confirmRes = await Swal.fire({
                    title: 'Xóa Notebook?',
                    text: 'Bạn có chắc chắn muốn xóa notebook này khỏi danh mục?',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonText: 'Đồng ý xóa',
                    cancelButtonText: 'Hủy bỏ'
                });
                if (!confirmRes.isConfirmed) return;
            }
            try {
                const res = await fetch('/api/notebooklm/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: notebookId })
                });
                const data = await res.json();
                if (data.success) {
                    notebooks.value = data.notebooks || [];
                    if (data.default_notebook_id) {
                        defaultNotebookId.value = data.default_notebook_id;
                    }
                    showToast(data.message || 'Đã xóa notebook khỏi danh mục.', 'success');
                } else {
                    showToast(data.message || 'Lỗi khi xóa notebook', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối khi xóa notebook', 'error');
            }
        };
        const setDefaultNotebookItem = async (notebookId) => {
            try {
                const res = await fetch('/api/notebooklm/set-default', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: notebookId })
                });
                const data = await res.json();
                if (data.success) {
                    notebooks.value = data.notebooks || [];
                    defaultNotebookId.value = notebookId;
                    selectedNotebookForBatch.value = notebookId;
                    batchUploadedNotebookId.value = notebookId;
                    showToast('Đã đặt làm Notebook mặc định thành công!', 'success');
                } else {
                    showToast(data.message || 'Lỗi đặt mặc định', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối: ' + e.message, 'error');
            }
        };
        const openNotebookStorageFolder = async (folderPath) => {
            try {
                const res = await fetch('/api/notebooklm/open-storage-folder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ folder_path: folderPath || '' })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Đã mở thư mục nguồn NotebookLM trong File Explorer!', 'success');
                } else {
                    showToast('Không thể mở thư mục trên hệ điều hành', 'warning');
                }
            } catch (e) {
                showToast('Lỗi khi mở thư mục: ' + e.message, 'error');
            }
        };
        const openNotebookLMUrl = (url) => {
            window.open(url || 'https://notebooklm.google.com/', '_blank');
        };
        
        // ==================== TỰ ĐỘNG HÓA GOOGLE NOTEBOOKLM (100% TỰ ĐỘNG) ====================
        const checkNotebookLMAutoStatus = async (showNotification = false) => {
            isCheckingAutoStatus.value = true;
            try {
                const res = await fetch('/api/notebooklm/auto/status');
                const data = await res.json();
                notebooklmAutoStatus.value = data;
                if (showNotification) {
                    showToast(data.message || (data.connected ? 'Đã kết nối tự động với Google NotebookLM' : 'Chưa kết nối tự động'), data.connected ? 'success' : 'info');
                }
            } catch (e) {
                notebooklmAutoStatus.value = { connected: false, email: '', message: e.message };
            } finally {
                isCheckingAutoStatus.value = false;
            }
        };
        const triggerNotebookLMLogin = async () => {
            isTriggeringLogin.value = true;
            try {
                // Gọi API backend để dọn dẹp và thử khởi chạy
                const res = await fetch('/api/notebooklm/auto/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ browser: 'msedge' })
                });
                const data = await res.json();
                // Hiển thị hộp thoại hướng dẫn rõ ràng vì Windows chặn dịch vụ nền tự ý bật cửa sổ
                if (window.Swal) {
                    Swal.fire({
                        title: 'Mở Cửa Sổ Đăng Nhập NotebookLM',
                        html: `
                            <div style="text-align: left; font-size: 13px; line-height: 1.6; color: #1e293b;">
                                <p style="margin-bottom: 8px;">
                                    Do chính sách bảo mật của <b>hệ điều hành Windows</b>, dịch vụ web chạy ngầm bị chặn không cho phép tự ý bật cửa sổ đồ họa đè lên màn hình của bạn.
                                </p>
                                <div style="background: #edf5fd; border: 1.5px solid #b9d2ec; border-radius: 8px; padding: 12px; margin: 10px 0;">
                                    <b style="color: #004b93; font-size: 13px;">👉 Thao tác mở cửa sổ đăng nhập ngay lập tức:</b><br/>
                                    1. Mở thư mục ứng dụng trên máy tính của bạn:<br/>
                                    <code style="background: #e2e8f0; padding: 3px 6px; border-radius: 4px; font-size: 11px; display: inline-block; margin: 4px 0;">f:\Luyen_cong\AntiGravity\Chat_bot_Gemini</code><br/>
                                    2. <b>Bấm đúp chuột</b> vào file: <b style="color: #004b93; font-size: 13px;">Dang_Nhap_NotebookLM.bat</b><br/>
                                    3. Cửa sổ Microsoft Edge sẽ hiện lên ngay lập tức để bạn đăng nhập Google. Sau khi đăng nhập xong, cửa sổ sẽ tự động lưu và đóng lại.
                                </div>
                                <div style="background: #f8fafc; border: 1px dashed #94a3b8; border-radius: 6px; padding: 10px; margin-top: 8px; font-size: 12px; color: #475569;">
                                    <b style="color: #0f172a;">💡 Mẹo tiện lợi:</b> Toàn bộ văn bản đã lưu (TT 68, VBHN 114...) <b>đã nằm sẵn trong Google Drive</b>. Bạn chỉ cần vào trang <b>NotebookLM</b> &gt; Bấm <b>"+ Thêm nguồn"</b> &gt; Chọn <b>"Google Drive"</b> là có thể bắt đầu hỏi đáp AI ngay lập tức mà không bắt buộc phải thực hiện bước này!
                                </div>
                            </div>
                        `,
                        icon: 'info',
                        confirmButtonText: 'Đã hiểu & Mở file .bat',
                        confirmButtonColor: '#004b93',
                        showCancelButton: true,
                        cancelButtonText: 'Đóng'
                    });
                } else {
                    showToast(data.message, 'info');
                }
                // Thăm dò kiểm tra trạng thái mỗi 5 giây trong 2 phút
                let attempts = 0;
                const interval = setInterval(async () => {
                    attempts++;
                    const sRes = await fetch('/api/notebooklm/auto/status');
                    const sData = await sRes.json();
                    if (sData.connected) {
                        clearInterval(interval);
                        notebooklmAutoStatus.value = sData;
                        showToast('Đăng nhập Google NotebookLM thành công! Kết nối tự động 100% đã được kích hoạt.', 'success');
                    } else if (attempts >= 24) {
                        clearInterval(interval);
                    }
                }, 5000);
            } catch (e) {
                showToast('Lỗi khi mở cửa sổ đăng nhập: ' + e.message, 'error');
            } finally {
                isTriggeringLogin.value = false;
            }
        };
        const syncGoogleNotebooks = async () => {
            isSyncingGoogleNotebooks.value = true;
            try {
                const res = await fetch('/api/notebooklm/auto/sync-notebooks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (data.success) {
                    if (data.notebooks) {
                        notebooks.value = data.notebooks;
                    }
                    showToast(data.message, 'success');
                } else {
                    showToast(data.message || 'Lỗi đồng bộ sổ ghi chú', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối khi đồng bộ sổ ghi chú: ' + e.message, 'error');
            } finally {
                isSyncingGoogleNotebooks.value = false;
            }
        };
        const resetNotebooksToDefault = async () => {
            const confirmed = await Swal.fire({
                title: 'Đồng bộ 13 Notebook chuẩn?',
                text: 'Khôi phục danh sách đầy đủ 13 Notebook chuẩn từ tài khoản Google NotebookLM của bạn?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#004b93',
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Đồng ý',
                cancelButtonText: 'Hủy'
            });
            if (!confirmed.isConfirmed) return;
            try {
                const res = await fetch('/api/notebooklm/reset-defaults', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    notebooks.value = data.notebooks;
                    defaultNotebookId.value = data.default_notebook_id;
                    showToast(data.message, 'success');
                } else {
                    showToast(data.message || 'Lỗi khi đồng bộ notebook', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối máy chủ: ' + e.message, 'error');
            }
        };
        // Gợi ý màu sắc nhãn loại văn bản theo chuẩn Cổng Dịch vụ công (Xanh, Trắng, Không dùng màu đỏ)
        const getDocTypeBadgeClass = (type) => {
            switch (type) {
                case 'Nghị định':
                    return 'bg-blue-50 text-blue-800 border-blue-300 font-bold';
                case 'Thông tư':
                    return 'bg-teal-50 text-teal-800 border-teal-300 font-bold';
                case 'Quyết định':
                    return 'bg-indigo-50 text-indigo-800 border-indigo-300 font-bold';
                case 'Công văn':
                    return 'bg-amber-50 text-amber-900 border-amber-300 font-bold';
                case 'Nghị quyết':
                    return 'bg-sky-50 text-sky-800 border-sky-300 font-bold';
                case 'Luật':
                    return 'bg-blue-100 text-blue-900 border-blue-400 font-black';
                default:
                    return 'bg-slate-100 text-slate-800 border-slate-300 font-semibold';
            }
        };
        const getAgencyBadgeClass = (agency) => {
            if (agency.includes('Chính phủ')) return 'bg-blue-100 text-blue-900 border-blue-300 font-semibold';
            if (agency.includes('Quốc hội')) return 'bg-indigo-100 text-indigo-900 border-indigo-300 font-semibold';
            if (agency.includes('Bộ Tài chính')) return 'bg-sky-100 text-sky-900 border-sky-300 font-semibold';
            if (agency.includes('Thuế')) return 'bg-cyan-100 text-cyan-900 border-cyan-300 font-semibold';
            if (agency.includes('Hải quan')) return 'bg-blue-50 text-blue-900 border-blue-200 font-semibold';
            return 'bg-slate-100 text-slate-800 border-slate-300 font-semibold';
        };
        // Lấy đường dẫn trực tiếp mở bài viết chứa văn bản trên website gốc chính xác 100% (Mở trực tiếp website nguồn, không qua Google Search)
        const getSourceArticleUrl = (doc) => {
            const num = (doc.doc_number || '').trim();
            const src = (doc.source || '').toLowerCase().trim();
            // 0. Xử lý đường dẫn tương đối (bắt đầu bằng ? hoặc /)
            if (doc.source_url && (doc.source_url.startsWith('?') || doc.source_url.startsWith('/'))) {
                if (src.includes('gdt.gov.vn')) {
                    return 'https://gdt.gov.vn/wps/portal/' + doc.source_url;
                }
                return 'https://' + src + doc.source_url;
            }
            // 1. Nếu văn bản đã có source_url trực tiếp hợp lệ từ website nguồn
            if (doc.source_url && doc.source_url.startsWith('http') && !doc.source_url.includes('google.com')) {
                return doc.source_url;
            }
            // 2. Cổng Công báo Nước CHXHCN Việt Nam (congbao.chinhphu.vn)
            if (src.includes('congbao') || src.includes('chinhphu')) {
                return 'https://congbao.chinhphu.vn/van-ban-dang-cong-bao.htm';
            }
            // 3. Cổng Thông tin Điện tử Tổng cục Thuế (gdt.gov.vn)
            if (src.includes('gdt.gov.vn')) {
                return 'https://gdt.gov.vn/wps/portal/?uri=nm:oid:Z6_049IL8VSOR0PF0I1OQQRMV3KU3';
            }
            // 4. Cổng Thông tin Điện tử Bộ Tài chính (mof.gov.vn)
            if (src.includes('mof.gov.vn')) {
                return 'https://mof.gov.vn/webcenter/portal/vclvcstc/pages_r/l/van-ban-chi-dao-dieu-hanh';
            }
            // 5. Cơ sở Dữ liệu Quốc gia về Văn bản Pháp luật (vbpl.vn)
            if (src.includes('vbpl.vn')) {
                if (doc.vbpl_id) {
                    return `https://vbpl.vn/van-ban/chi-tiet/${doc.vbpl_id}`;
                }
                return 'https://vbpl.vn';
            }
            // 6. Cổng Thông tin Điện tử Quốc hội (quochoi.vn)
            if (src.includes('quochoi.vn')) {
                return `https://quochoi.vn/pages/tim-kiem.aspx?k=${encodeURIComponent(num)}`;
            }
            // Mặc định mở trực tiếp website nguồn
            return `https://${src}`;
        };
        // Nhãn nguồn website
        const getSourceBadgeClass = (source) => {
            if (source.includes('gdt.gov.vn')) return 'bg-cyan-50 text-cyan-900 border-cyan-300';
            if (source.includes('mof.gov.vn')) return 'bg-sky-50 text-sky-900 border-sky-300';
            if (source.includes('quochoi.vn')) return 'bg-indigo-50 text-indigo-900 border-indigo-300';
            if (source.includes('congbao')) return 'bg-amber-50 text-amber-900 border-amber-300';
            if (source.includes('vbpl.vn')) return 'bg-teal-50 text-teal-900 border-teal-300';
            return 'bg-slate-50 text-slate-800 border-slate-200';
        };
        // ==================== TAB 3: UPLOAD VÀ LƯU VĂN BẢN (PDF, WORD, EXCEL) ====================
        const uploadedFiles = ref([]);
        const selectedUploadedIds = ref([]);
        const isUploadingLocalFiles = ref(false);
        const isProcessingLocalUpload = ref(false);
        const batchUploadedFolderId = ref('1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK');
        const uploadLocalModalOpen = ref(false);
        const uploadLocalSummary = ref({ total: 0, success: 0, fail: 0 });
        const uploadLocalResults = ref([]);
        const isAllUploadedSelected = computed(() => {
            return uploadedFiles.value.length > 0 && selectedUploadedIds.value.length === uploadedFiles.value.length;
        });
        const handleFileInputChange = (event) => {
            const files = event.target.files;
            if (files && files.length > 0) {
                processSelectedLocalFiles(files);
            }
            event.target.value = '';
        };
        const handleFileDrop = (event) => {
            const files = event.dataTransfer.files;
            if (files && files.length > 0) {
                processSelectedLocalFiles(files);
            }
        };
        const processSelectedLocalFiles = async (fileList) => {
            const allowed = ['.pdf', '.doc', '.docx', '.xls', '.xlsx'];
            const validFiles = [];
            for (let i = 0; i < fileList.length; i++) {
                const f = fileList[i];
                const lower = f.name.toLowerCase();
                if (allowed.some(ext => lower.endsWith(ext))) {
                    validFiles.push(f);
                }
            }
            if (validFiles.length === 0) {
                showToast('Vui lòng chọn các tệp tin có định dạng PDF (.pdf), Word (.docx, .doc) hoặc Excel (.xlsx, .xls).', 'warning');
                return;
            }
            isProcessingLocalUpload.value = true;
            showToast(`Đang tiếp nhận ${validFiles.length} tệp tin từ máy tính...`, 'info');
            try {
                const formData = new FormData();
                for (const file of validFiles) {
                    formData.append('files', file);
                }
                const res = await fetch('/api/upload-local-files', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (data.success && data.files) {
                    const currentFolder = defaultFolderId.value || batchUploadedFolderId.value || '1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK';
                    const currentNotebook = batchUploadedNotebookId.value || defaultNotebookId.value || 'nb_tax_default';
                    for (const item of data.files) {
                        item.selected_folder_id = currentFolder;
                        item.selected_notebook_id = currentNotebook;
                        item.notebook_status = 'idle';
                        uploadedFiles.value.push(item);
                        if (!selectedUploadedIds.value.includes(item.id)) {
                            selectedUploadedIds.value.push(item.id);
                        }
                    }
                    showToast(`Đã thêm thành công ${data.files.length} văn bản vào danh sách!`, 'success');
                } else {
                    showToast(data.message || 'Lỗi khi tải tệp lên máy chủ', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối khi tải tệp tin từ máy tính: ' + e.message, 'error');
            } finally {
                isProcessingLocalUpload.value = false;
            }
        };
        const toggleSelectUploaded = (id) => {
            const idx = selectedUploadedIds.value.indexOf(id);
            if (idx > -1) {
                selectedUploadedIds.value.splice(idx, 1);
            } else {
                selectedUploadedIds.value.push(id);
            }
        };
        const toggleSelectAllUploaded = () => {
            if (isAllUploadedSelected.value) {
                selectedUploadedIds.value = [];
            } else {
                selectedUploadedIds.value = uploadedFiles.value.map(f => f.id);
            }
        };
        const applyBatchUploadedFolder = () => {
            if (!batchUploadedFolderId.value) return;
            const folder = folders.value.find(f => f.id === batchUploadedFolderId.value);
            const folderName = folder ? folder.name : 'đã chọn';
            
            const targetList = selectedUploadedIds.value.length > 0 
                ? uploadedFiles.value.filter(f => selectedUploadedIds.value.includes(f.id))
                : uploadedFiles.value;
            targetList.forEach(f => {
                f.selected_folder_id = batchUploadedFolderId.value;
            });
            showToast(`Đã gán thư mục "${folderName}" cho ${targetList.length} văn bản!`, 'success');
        };
        const removeUploadedFile = async (idx) => {
            const file = uploadedFiles.value[idx];
            if (!file) return;
            try {
                fetch(`/api/delete-local-file/${file.id}`, { method: 'POST' });
            } catch (e) {}
            
            const selIdx = selectedUploadedIds.value.indexOf(file.id);
            if (selIdx > -1) {
                selectedUploadedIds.value.splice(selIdx, 1);
            }
            uploadedFiles.value.splice(idx, 1);
            showToast(`Đã xóa văn bản khỏi danh sách: ${file.filename}`, 'info');
        };
        const removeSelectedUploadedFiles = () => {
            if (selectedUploadedIds.value.length === 0) return;
            const remaining = [];
            for (const f of uploadedFiles.value) {
                if (selectedUploadedIds.value.includes(f.id)) {
                    try {
                        fetch(`/api/delete-local-file/${f.id}`, { method: 'POST' });
                    } catch (e) {}
                } else {
                    remaining.push(f);
                }
            }
            const count = uploadedFiles.value.length - remaining.length;
            uploadedFiles.value = remaining;
            selectedUploadedIds.value = [];
            showToast(`Đã xóa ${count} văn bản được chọn khỏi danh sách.`, 'info');
        };
        const clearAllUploadedFiles = () => {
            for (const f of uploadedFiles.value) {
                try {
                    fetch(`/api/delete-local-file/${f.id}`, { method: 'POST' });
                } catch (e) {}
            }
            uploadedFiles.value = [];
            selectedUploadedIds.value = [];
            showToast('Đã làm trống toàn bộ danh sách văn bản tải lên.', 'info');
        };
        const uploadSelectedUploadedFilesToDrive = async () => {
            if (selectedUploadedIds.value.length === 0) {
                showToast('Vui lòng tick chọn ít nhất một văn bản trong danh sách để lưu lên Google Drive.', 'warning');
                return;
            }
            if (!driveStatus.value.connected) {
                showToast('Chưa kết nối Google Drive! Vui lòng vào Tab 2 "Thiết lập cấu hình" để kiểm tra kết nối.', 'warning');
                return;
            }
            const filesToUpload = uploadedFiles.value.filter(f => selectedUploadedIds.value.includes(f.id));
            isUploadingLocalFiles.value = true;
            uploadLocalModalOpen.value = true;
            uploadLocalSummary.value = {
                total: filesToUpload.length,
                success: 0,
                fail: 0
            };
            uploadLocalResults.value = [];
            filesToUpload.forEach(f => {
                f.upload_status = 'uploading';
            });
            try {
                const payload = {
                    files: filesToUpload.map(f => ({
                        id: f.id,
                        filename: f.filename,
                        saved_filename: f.saved_filename,
                        selected_folder_id: f.selected_folder_id || defaultFolderId.value,
                        mimetype: f.mimetype
                    }))
                };
                const res = await fetch('/api/upload-local-files-to-drive', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.results) {
                    uploadLocalResults.value = data.results;
                    uploadLocalSummary.value = {
                        total: data.total || filesToUpload.length,
                        success: data.success_count || 0,
                        fail: data.fail_count || 0
                    };
                    data.results.forEach(r => {
                        const matched = uploadedFiles.value.find(f => f.id === r.id);
                        if (matched) {
                            matched.upload_status = r.status;
                            matched.drive_link = r.drive_link || '';
                            matched.drive_file_id = r.drive_file_id || '';
                            matched.message = r.message || '';
                        }
                    });
                    if (data.success_count > 0) {
                        showToast(`Đã lưu thành công ${data.success_count}/${filesToUpload.length} văn bản lên Google Drive!`, 'success');
                    } else {
                        showToast('Không thể lưu văn bản lên Drive: ' + data.message, 'error');
                    }
                } else {
                    showToast(data.message || 'Lỗi khi upload lên Drive', 'error');
                }
            } catch (e) {
                showToast('Lỗi đường truyền khi lưu văn bản lên Drive: ' + e.message, 'error');
            } finally {
                isUploadingLocalFiles.value = false;
            }
        };
        const applyBatchUploadedNotebook = () => {
            const targets = selectedUploadedIds.value.length > 0
                ? uploadedFiles.value.filter(f => selectedUploadedIds.value.includes(f.id))
                : uploadedFiles.value;
            if (targets.length === 0) {
                showToast('Chưa có tệp tin nào để gán Notebook.', 'warning');
                return;
            }
            const nbName = getNotebookName(batchUploadedNotebookId.value);
            targets.forEach(f => {
                f.selected_notebook_id = batchUploadedNotebookId.value;
            });
            showToast(`Đã gán Notebook "${nbName}" cho ${targets.length} tệp tin!`, 'success');
        };
        const uploadSelectedUploadedFilesToNotebookLM = async () => {
            if (selectedUploadedIds.value.length === 0) {
                showToast('Vui lòng tick chọn ít nhất một tệp tin để lưu lên NotebookLM.', 'warning');
                return;
            }
            const filesToSave = uploadedFiles.value.filter(f => selectedUploadedIds.value.includes(f.id));
            filesToSave.forEach(f => {
                if (!f.selected_notebook_id) {
                    f.selected_notebook_id = batchUploadedNotebookId.value || defaultNotebookId.value || 'nb_tax_default';
                }
            });
            notebookModalOpen.value = true;
            isSavingUploadedToNotebook.value = true;
            notebookResults.value = [];
            notebookSummary.value = {
                total: filesToSave.length,
                success: 0,
                fail: 0,
                notebookName: getNotebookName(batchUploadedNotebookId.value)
            };
            try {
                const res = await fetch('/api/upload-local-files-to-notebooklm', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        files: filesToSave,
                        selected_notebook_id: batchUploadedNotebookId.value
                    })
                });
                const data = await res.json();
                if (data.success || data.results) {
                    notebookResults.value = data.results || [];
                    notebookSummary.value = {
                        total: filesToSave.length,
                        success: data.success_count || 0,
                        fail: data.fail_count || 0,
                        notebookName: getNotebookName(batchUploadedNotebookId.value)
                    };
                    (data.results || []).forEach(r => {
                        const targetFile = uploadedFiles.value.find(f => f.id === r.id);
                        if (targetFile) {
                            if (r.status !== 'error' && r.success !== false) {
                                targetFile.notebook_status = 'success';
                                targetFile.notebook_name = r.notebook_name;
                                targetFile.upload_status = 'success';
                                if (r.drive_link) {
                                    targetFile.drive_link = r.drive_link;
                                }
                            } else {
                                targetFile.notebook_status = 'error';
                            }
                        }
                    });
                    showToast(data.message, data.success_count > 0 ? 'success' : 'error');
                } else {
                    showToast(data.message || 'Lỗi khi lưu tệp lên NotebookLM', 'error');
                }
            } catch (e) {
                showToast('Lỗi mạng hoặc kết nối máy chủ khi lưu tệp vào NotebookLM: ' + e.message, 'error');
            } finally {
                isSavingUploadedToNotebook.value = false;
            }
        };
        const getUploadedFileIcon = (ext) => {
            ext = (ext || '').toLowerCase();
            if (ext === '.pdf') return 'fa-solid fa-file-pdf text-red-600';
            if (ext.includes('doc')) return 'fa-solid fa-file-word text-blue-600';
            if (ext.includes('xls')) return 'fa-solid fa-file-excel text-emerald-600';
            return 'fa-solid fa-file-lines text-slate-500';
        };

        // =========================================================================
        // PHÂN HỆ VĂN BẢN HÀNH CHÍNH (CHUẨN NGHỊ ĐỊNH 30/2020/NĐ-CP) & GEMINI AI
        // =========================================================================
        // 1. TÍNH NĂNG 1: KIỂM TRA THỂ THỨC & SỬA LỖI AI
        const checkerInputMode = ref('file'); // 'file' | 'text'
        const checkerFile = ref(null);
        const checkerFileName = ref('');
        const checkerRawText = ref('');
        const isCheckingNd30 = ref(false);
        const checkResult = ref(null);
        const selectedIssue = ref(null);
        const isAiFixing = ref(false);
        const fixedDoc = ref(null);
        const checkerActiveView = ref('original'); // 'original' | 'fixed'
        const isSavingCheckerToDrive = ref(false);
        const checkerSelectedDriveFolder = ref('1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK');
        const checkerRawLines = computed(() => {
            return checkerRawText.value ? checkerRawText.value.split('\n') : [];
        });
        const resetChecker = () => {
            checkerRawText.value = '';
            checkerFile.value = null;
            checkerFileName.value = '';
            checkResult.value = null;
            fixedDoc.value = null;
            checkerActiveView.value = 'original';
        };
        const loadCheckerSampleDoc = () => {
            checkerInputMode.value = 'text';
            checkerRawText.value = `UBND TP.HCM
SO: 15/TB-UB
Tp.HCM, ngay 5 thang 3 nam 2026
THONG BAO
Ve viec to chuc kiem tra hoa don dien tu
Can cu vao Luat quan ly thue ;
Can cu vao tinh hinh thuc te co quan,
Uy ban nhan dan thong bao den toan the cac to chuc ca nhan nop thue tren dia ban ve viec tien hanh ra soat dinh ky hoa don dien tu quy 1 nam 2026 .
Moi don vi co trach nhiem bao cao dung han truoc ngay 15/3/2026.
Noi nhan:
- Cac doanh nghiep
- Phong Ke toan
CHU TICH
Nguyen Van A`;
            Swal.fire({
                icon: 'info',
                title: 'Đã nạp văn bản mẫu',
                text: 'Đã nạp văn bản mẫu có nhiều lỗi thể thức (thiếu Quốc hiệu, sai font, sai ngày tháng, thiếu Lưu VT...) để thử nghiệm kiểm tra và AI tự động sửa!',
                timer: 2500,
                showConfirmButton: false
            });
        };
        const handleCheckerFileInput = (e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
                checkerFile.value = files[0];
                checkerFileName.value = files[0].name;
            }
        };
        const handleCheckerFileDrop = (e) => {
            e.preventDefault();
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                checkerFile.value = files[0];
                checkerFileName.value = files[0].name;
            }
        };
        const runCheckNd30 = async () => {
            if (checkerInputMode.value === 'file' && !checkerFile.value) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Chưa chọn tệp',
                    text: 'Vui lòng tải lên tệp văn bản (.docx, .pdf, .txt) hoặc chuyển sang tab Nhập trực tiếp.'
                });
                return;
            }
            if (checkerInputMode.value === 'text' && !checkerRawText.value.trim()) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Chưa nhập văn bản',
                    text: 'Vui lòng dán hoặc nhập nội dung văn bản hành chính cần kiểm tra.'
                });
                return;
            }
            isCheckingNd30.value = true;
            try {
                let resp;
                if (checkerInputMode.value === 'file' && checkerFile.value) {
                    const formData = new FormData();
                    formData.append('file', checkerFile.value);
                    resp = await fetch('/api/admin-doc/check', {
                        method: 'POST',
                        body: formData
                    });
                } else {
                    resp = await fetch('/api/admin-doc/check', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: checkerRawText.value })
                    });
                }
                const data = await resp.json();
                if (data.success) {
                    checkResult.value = data;
                    checkerRawText.value = data.extracted_text || checkerRawText.value;
                    checkerActiveView.value = 'original';
                    selectedIssue.value = data.issues && data.issues.length > 0 ? data.issues[0] : null;
                    Swal.fire({
                        icon: data.errors_count > 0 ? 'warning' : 'success',
                        title: `Hoàn tất kiểm tra: ${data.overall_score}/100 điểm`,
                        text: `Phát hiện ${data.errors_count} lỗi vi phạm và ${data.warnings_count} điểm cần cải thiện theo Nghị định 30/2020/NĐ-CP.`,
                        timer: 3000,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Lỗi kiểm tra',
                        text: data.message || 'Không thể kiểm tra văn bản.'
                    });
                }
            } catch (err) {
                Swal.fire({
                    icon: 'error',
                    title: 'Lỗi hệ thống',
                    text: 'Lỗi kết nối khi kiểm tra văn bản: ' + err.message
                });
            } finally {
                isCheckingNd30.value = false;
            }
        };
        const runAiAutoFix = async () => {
            if (!checkerRawText.value.trim()) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Thiếu nội dung',
                    text: 'Chưa có nội dung văn bản để AI sửa lỗi.'
                });
                return;
            }
            isAiFixing.value = true;
            try {
                const resp = await fetch('/api/admin-doc/ai-fix', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: checkerRawText.value,
                        issues: checkResult.value ? checkResult.value.issues : []
                    })
                });
                const data = await resp.json();
                if (data.success && data.data) {
                    fixedDoc.value = data.data;
                    checkerActiveView.value = 'fixed';
                    Swal.fire({
                        icon: 'success',
                        title: 'AI đã tự động sửa lỗi thành công!',
                        html: `Văn bản đã được chuẩn hóa toàn diện theo Nghị định 30/2020/NĐ-CP.<br><br><b>Các điểm đã cải thiện:</b><br>${(data.data.applied_fixes || []).map(f => '✓ ' + f).join('<br>')}`,
                        confirmButtonText: 'Xem Văn Bản Chuẩn',
                        confirmButtonColor: '#004b93'
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'AI không thể sửa lỗi',
                        text: data.message || 'Vui lòng kiểm tra lại cấu hình Gemini API Key.'
                    });
                }
            } catch (err) {
                Swal.fire({
                    icon: 'error',
                    title: 'Lỗi kết nối AI',
                    text: 'Không thể kết nối đến Gemini AI: ' + err.message
                });
            } finally {
                isAiFixing.value = false;
            }
        };
        const exportDocWord = async (docObj) => {
            if (!docObj) return;
            try {
                const resp = await fetch('/api/admin-doc/export-word', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ doc_data: docObj })
                });
                if (!resp.ok) throw new Error('Lỗi xuất file Word');
                const blob = await resp.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${(docObj.doc_type || 'VAN_BAN')}_${(docObj.doc_number || '01').replace(/[/\\: ]/g, '_')}.docx`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi xuất Word', text: e.message });
            }
        };
        const exportDocPdf = async (docObj) => {
            if (!docObj) return;
            try {
                const resp = await fetch('/api/admin-doc/export-pdf', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ doc_data: docObj })
                });
                if (!resp.ok) throw new Error('Lỗi xuất file PDF');
                const blob = await resp.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${(docObj.doc_type || 'VAN_BAN')}_${(docObj.doc_number || '01').replace(/[/\\: ]/g, '_')}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi xuất PDF', text: e.message });
            }
        };
        const saveDocToDrive = async (docObj, folderId, options = {}) => {
            if (!docObj) return { success: false, message: 'Dữ liệu văn bản trống' };
            try {
                const chosenFolder = folderId || geminiConfig.value.admin_doc_drive_folder_id || '16Ua7ZfjOl2klPOEMH5QxDtvUSQ9A-FTr';
                const targetFolderIds = [chosenFolder];
                const resp = await fetch('/api/admin-doc/save-drive', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        doc_data: docObj,
                        folder_ids: targetFolderIds,
                        formats: ['docx', 'pdf']
                    })
                });
                const data = await resp.json();
                if (data.success) {
                    if (!options.silent) {
                        const folderName = data.folder_name || '____Automation Video____\\Văn thư';
                        const folderUrl = data.folder_url || `https://drive.google.com/drive/folders/${data.folder_id || ''}`;
                        const results = data.results || [];
                        
                        let filesHtml = '';
                        results.forEach(r => {
                            const icon = r.format === 'docx' ? 'fa-file-word text-blue-600' : 'fa-file-pdf text-red-600';
                            const label = r.format === 'docx' ? 'Bản Word (.docx)' : 'Bản PDF (.pdf)';
                            const link = r.view_link || (r.drive_result && r.drive_result.webViewLink);
                            filesHtml += `
                                <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; margin-top: 6px;">
                                    <div style="text-align: left; font-size: 13px;">
                                        <i class="fa-solid ${icon}"></i> <b>${label}:</b> <span style="color: #475569;">${r.filename}</span>
                                    </div>
                                    ${link ? `<a href="${link}" target="_blank" rel="noopener noreferrer" style="padding: 4px 10px; background: #004b93; color: white; border-radius: 4px; font-size: 12px; text-decoration: none; font-weight: bold; margin-left: 8px; white-space: nowrap;">
                                        <i class="fa-solid fa-arrow-up-right-from-square"></i> Mở file
                                    </a>` : ''}
                                </div>
                            `;
                        });

                        Swal.fire({
                            icon: 'success',
                            title: 'Đã lưu lên Google Drive!',
                            html: `
                                <div style="text-align: left; font-size: 13px; line-height: 1.6; color: #1e293b;">
                                    <div style="margin-bottom: 10px; padding: 10px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px;">
                                        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: gap-2;">
                                            <div>
                                                <i class="fa-brands fa-google-drive" style="color: #2563eb;"></i> <b>Nơi lưu Google Drive:</b><br>
                                                📁 <span style="font-weight: bold; color: #1d4ed8;">${folderName}</span>
                                            </div>
                                            <a href="${folderUrl}" target="_blank" rel="noopener noreferrer" style="padding: 5px 12px; background: #2563eb; color: white; border-radius: 5px; font-size: 12px; text-decoration: none; font-weight: bold; display: inline-flex; align-items: center; gap: 4px;">
                                                <i class="fa-solid fa-folder-open"></i> Mở thư mục Drive
                                            </a>
                                        </div>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <b>Các tệp văn bản đã lưu:</b>
                                        ${filesHtml}
                                    </div>
                                </div>
                            `,
                            confirmButtonText: 'Đóng',
                            confirmButtonColor: '#004b93',
                            width: 580
                        });
                    }
                    return { success: true, data };
                } else {
                    if (!options.silent) {
                        Swal.fire({
                            icon: 'error',
                            title: 'Không thể lưu lên Drive',
                            text: data.message
                        });
                    }
                    return { success: false, message: data.message };
                }
            } catch (e) {
                if (!options.silent) {
                    Swal.fire({ icon: 'error', title: 'Lỗi kết nối Drive', text: e.message });
                }
                return { success: false, message: e.message };
            }
        };
        // 2. TÍNH NĂNG 2: SOẠN THẢO VĂN BẢN AI 3 BƯỚC (CHUẨN HANHCHANH.AI.VN)
        const composerStep = ref(1); // 1: Thiết lập ban đầu | 2: Tạo nội dung AI | 3: Tinh chỉnh AI
        const composerForm = ref({
            template_preset: 'thong_bao',
            doc_format: 'Hành chính (NĐ 30/2020/NĐ-CP)',
            doc_type: 'THÔNG BÁO',
            agency_parent: '',
            agency_code: 'CTHCM',
            agency_name: 'THUẾ TP.HỒ CHÍ MINH',
            is_joint_doc: false,
            location: 'Tp. Hồ Chí Minh',
            doc_date: new Date().toISOString().split('T')[0],
            doc_number_seq: '01',
            doc_number: '01/TB-CTHCM',
            header_ratio: 40, // 40% Cơ quan / 60% Quốc hiệu
            recipients: ['Lưu: VT.'],
            recipient_input: '',
            signer_role: 'CỤC TRƯỞNG',
            signer_name: '',
            // Bước 2:
            purpose: '',
            target_audience: '',
            legal_bases: '',
            structure_req: ''
        });
        const composerReferenceImages = ref([]);
        const isGeneratingDoc = ref(false);
        const generatedDoc = ref({
            agency_parent: '',
            agency_name: 'THUẾ TP.HỒ CHÍ MINH',
            doc_number: '01/TB-CTHCM',
            republic_title: 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM',
            motto: 'Độc lập - Tự do - Hạnh phúc',
            location: 'Tp. Hồ Chí Minh',
            date_formatted: `ngày ${String(now.getDate()).padStart(2, '0')} tháng ${String(now.getMonth() + 1).padStart(2, '0')} năm ${now.getFullYear()}`,
            doc_type: 'THÔNG BÁO',
            subject: 'Về việc ...',
            legal_bases: [],
            body_paragraphs: [
                'Nội dung văn bản hành chính sẽ hiển thị trực quan tại đây sau khi bạn hoàn tất thiết lập ban đầu và bấm "Tạo nội dung".'
            ],
            recipients: ['- Lưu: VT.'],
            signer_role: '[CHỨC VỤ]',
            signer_name: '[Họ và tên]'
        });
        const isRefiningDoc = ref(false);
        const refinePrompt = ref('');
        const refineModalOpen = ref(false);
        const handleTemplatePresetChange = () => {
            const p = composerForm.value.template_preset;
            if (p === 'thong_bao') {
                composerForm.value.doc_type = 'THÔNG BÁO';
                composerForm.value.doc_number = `${composerForm.value.doc_number_seq}/TB-${composerForm.value.agency_code}`;
                composerForm.value.purpose = 'Thông báo về việc tổ chức Hội nghị tập huấn chính sách thuế và hóa đơn điện tử';
                composerForm.value.signer_role = 'CỤC TRƯỞNG';
            } else if (p === 'cong_van') {
                composerForm.value.doc_type = 'CÔNG VĂN';
                composerForm.value.doc_number = `${composerForm.value.doc_number_seq}/${composerForm.value.agency_code}-TTHT`;
                composerForm.value.purpose = 'V/v giải đáp vướng mắc chính sách thuế thu nhập cá nhân đối với người lao động';
                composerForm.value.signer_role = 'KT. CỤC TRƯỞNG\nPHÓ CỤC TRƯỞNG';
            } else if (p === 'quyet_dinh') {
                composerForm.value.doc_type = 'QUYẾT ĐỊNH';
                composerForm.value.doc_number = `${composerForm.value.doc_number_seq}/QĐ-${composerForm.value.agency_code}`;
                composerForm.value.purpose = 'Về việc thành lập Tổ chỉ đạo kiểm soát và phòng chống gian lận hóa đơn';
                composerForm.value.signer_role = 'CỤC TRƯỞNG';
            } else if (p === 'to_trinh') {
                composerForm.value.doc_type = 'TỜ TRÌNH';
                composerForm.value.doc_number = `${composerForm.value.doc_number_seq}/TTr-${composerForm.value.agency_code}`;
                composerForm.value.purpose = 'Về việc phê duyệt kế hoạch chuyển đổi số và nâng cấp hạ tầng CNTT năm 2026';
                composerForm.value.signer_role = 'CỤC TRƯỞNG';
            } else if (p === 'giay_moi') {
                composerForm.value.doc_type = 'GIẤY MỜI';
                composerForm.value.doc_number = `${composerForm.value.doc_number_seq}/GM-${composerForm.value.agency_code}`;
                composerForm.value.purpose = 'Dự Hội nghị sơ kết công tác quản lý thuế quý I và triển khai nhiệm vụ quý II';
                composerForm.value.signer_role = 'THỦ TRƯỞNG CƠ QUAN';
            }
            updateLivePreviewFromForm();
        };
        const updateLivePreviewFromForm = () => {
            generatedDoc.value.agency_parent = composerForm.value.agency_parent;
            generatedDoc.value.agency_name = composerForm.value.agency_name;
            generatedDoc.value.doc_number = composerForm.value.doc_number;
            generatedDoc.value.doc_type = composerForm.value.doc_type;
            generatedDoc.value.location = composerForm.value.location;
            generatedDoc.value.signer_role = composerForm.value.signer_role;
            generatedDoc.value.signer_name = composerForm.value.signer_name || '[Họ và tên]';
            generatedDoc.value.recipients = [...composerForm.value.recipients];
            
            try {
                const parts = composerForm.value.doc_date.split('-');
                if (parts.length === 3) {
                    generatedDoc.value.date_formatted = `ngày ${parts[2]} tháng ${parts[1]} năm ${parts[0]}`;
                }
            } catch (e) {}
        };
        const addComposerRecipient = () => {
            const val = composerForm.value.recipient_input.trim();
            if (val && !composerForm.value.recipients.includes(val)) {
                composerForm.value.recipients.push(val);
                composerForm.value.recipient_input = '';
                updateLivePreviewFromForm();
            }
        };
        const removeComposerRecipient = (idx) => {
            composerForm.value.recipients.splice(idx, 1);
            updateLivePreviewFromForm();
        };
        const handleReferenceImageUpload = (e) => {
            const files = e.target.files;
            if (!files) return;
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                if (!file.type.startsWith('image/')) continue;
                const reader = new FileReader();
                reader.onload = (event) => {
                    const b64 = event.target.result.split(',')[1];
                    composerReferenceImages.value.push({
                        id: Date.now() + '_' + i,
                        name: file.name,
                        preview: event.target.result,
                        mime_type: file.type,
                        data: b64
                    });
                };
                reader.readAsDataURL(file);
            }
        };
        const removeReferenceImage = (idx) => {
            composerReferenceImages.value.splice(idx, 1);
        };
        const generateDocWithAi = async () => {
            if (!composerForm.value.purpose.trim() && composerReferenceImages.value.length === 0) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Thiếu thông tin',
                    text: 'Vui lòng nhập Mục đích và nội dung chính HOẶC tải lên ảnh chụp tài liệu tham khảo.'
                });
                return;
            }
            isGeneratingDoc.value = true;
            try {
                const imgPayload = composerReferenceImages.value.map(img => ({
                    mime_type: img.mime_type,
                    data: img.data
                }));
                const resp = await fetch('/api/admin-doc/ai-generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        wizard_data: composerForm.value,
                        images: imgPayload
                    })
                });
                const data = await resp.json();
                if (data.success && data.data) {
                    generatedDoc.value = data.data;
                    composerStep.value = 3;
                    Swal.fire({
                        icon: 'success',
                        title: 'Đã tạo xong văn bản!',
                        text: 'Gemini AI đã hoàn thành soạn thảo văn bản hành chính theo đúng chuẩn Nghị định 30/2020/NĐ-CP.',
                        timer: 2500,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Lỗi tạo văn bản',
                        text: data.message || 'Không thể tạo văn bản bằng AI. Vui lòng kiểm tra lại API Key.'
                    });
                }
            } catch (err) {
                Swal.fire({
                    icon: 'error',
                    title: 'Lỗi gọi AI',
                    text: 'Không thể kết nối đến Gemini AI: ' + err.message
                });
            } finally {
                isGeneratingDoc.value = false;
            }
        };
        const submitAiRefinement = async () => {
            if (!refinePrompt.value.trim()) return;
            isRefiningDoc.value = true;
            try {
                const resp = await fetch('/api/admin-doc/ai-refine', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_doc: generatedDoc.value,
                        prompt: refinePrompt.value
                    })
                });
                const data = await resp.json();
                if (data.success && data.data) {
                    generatedDoc.value = data.data;
                    refineModalOpen.value = false;
                    refinePrompt.value = '';
                    Swal.fire({
                        icon: 'success',
                        title: 'Đã tinh chỉnh văn bản!',
                        text: data.data.summary_notes || 'Văn bản đã được cập nhật thành công theo yêu cầu của bạn.',
                        timer: 2500,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Lỗi tinh chỉnh',
                        text: data.message
                    });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi kết nối AI', text: e.message });
            } finally {
                isRefiningDoc.value = false;
            }
        };
        // ==================== QUẢN LÝ VĂN BẢN ĐÃ SOẠN ====================
        const draftedDocuments = ref([]);
        const selectedDraftId = ref('');
        const loadDraftedDocuments = async () => {
            try {
                const resp = await fetch('/api/admin-doc/drafts');
                const data = await resp.json();
                if (data.success && data.drafts) {
                    draftedDocuments.value = data.drafts;
                }
            } catch (e) {
                console.error('Lỗi tải danh sách văn bản đã soạn:', e);
            }
        };
        const loadSelectedDraft = () => {
            if (!selectedDraftId.value) {
                loadComposerDefaultParams();
                return;
            }
            const draft = draftedDocuments.value.find(d => d.id === selectedDraftId.value);
            if (!draft) return;
            if (draft.template_preset) composerForm.value.template_preset = draft.template_preset;
            if (draft.doc_type) composerForm.value.doc_type = draft.doc_type;
            if (draft.agency_parent !== undefined) composerForm.value.agency_parent = draft.agency_parent;
            if (draft.agency_name) composerForm.value.agency_name = draft.agency_name;
            if (draft.unit_code) composerForm.value.unit_code = draft.unit_code;
            if (draft.doc_number) composerForm.value.doc_number = draft.doc_number;
            if (draft.location) composerForm.value.location = draft.location;
            if (draft.date_str) composerForm.value.date_str = draft.date_str;
            if (draft.signer_role) composerForm.value.signer_role = draft.signer_role;
            if (draft.signer_name) composerForm.value.signer_name = draft.signer_name;
            if (draft.purpose) composerForm.value.purpose = draft.purpose;
            if (draft.subject) composerForm.value.subject = draft.subject;
            if (draft.header_ratio) composerForm.value.header_ratio = draft.header_ratio;
            if (draft.recipients && Array.isArray(draft.recipients)) {
                composerForm.value.recipients = [...draft.recipients];
            }
            generatedDoc.value = {
                agency_parent: draft.agency_parent || '',
                agency_name: draft.agency_name || '',
                doc_number: draft.doc_number || '',
                republic_title: draft.republic_title || 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM',
                motto: draft.motto || 'Độc lập - Tự do - Hạnh phúc',
                location: draft.location || 'Tp. Hồ Chí Minh',
                date_formatted: draft.date_formatted || `ngày ${String(now.getDate()).padStart(2, '0')} tháng ${String(now.getMonth() + 1).padStart(2, '0')} năm ${now.getFullYear()}`,
                doc_type: draft.doc_type || 'THÔNG BÁO',
                subject: draft.subject || '',
                legal_bases: draft.legal_bases ? [...draft.legal_bases] : [],
                body_paragraphs: draft.body_paragraphs ? [...draft.body_paragraphs] : [],
                recipients: draft.recipients ? [...draft.recipients] : ['- Lưu: VT.'],
                signer_role: draft.signer_role || '[CHỨC VỤ]',
                signer_name: draft.signer_name || '[Họ và tên]'
            };
            Swal.fire({
                icon: 'success',
                title: 'Đã nạp văn bản đã soạn!',
                text: `Đã nạp thông số thiết lập của: ${draft.title || draft.subject}`,
                timer: 2000,
                showConfirmButton: false
            });
        };
        const saveCurrentDocAsDraft = async (silent = false) => {
            const title = composerForm.value.subject || composerForm.value.purpose?.slice(0, 80) || `${composerForm.value.doc_type} ngày ${todayStr}`;
            const draftData = {
                id: selectedDraftId.value || undefined,
                title: title,
                template_preset: composerForm.value.template_preset,
                doc_type: composerForm.value.doc_type,
                agency_parent: composerForm.value.agency_parent,
                agency_name: composerForm.value.agency_name,
                unit_code: composerForm.value.unit_code,
                doc_number: composerForm.value.doc_number,
                location: composerForm.value.location,
                date_str: composerForm.value.date_str,
                signer_role: composerForm.value.signer_role,
                signer_name: composerForm.value.signer_name,
                purpose: composerForm.value.purpose,
                subject: composerForm.value.subject,
                header_ratio: composerForm.value.header_ratio,
                recipients: [...composerForm.value.recipients],
                legal_bases: generatedDoc.value.legal_bases || [],
                body_paragraphs: generatedDoc.value.body_paragraphs || []
            };
            try {
                const resp = await fetch('/api/admin-doc/drafts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(draftData)
                });
                const data = await resp.json();
                if (data.success) {
                    draftedDocuments.value = data.drafts || draftedDocuments.value;
                    if (data.draft && data.draft.id) {
                        selectedDraftId.value = data.draft.id;
                    }
                    if (!silent) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Đã lưu vào danh mục!',
                            html: `Đã lưu văn bản <b>"${title}"</b> vào danh sách văn bản đã soạn thảo.`,
                            timer: 2000,
                            showConfirmButton: false
                        });
                    }
                    return { success: true, draft: data.draft };
                } else {
                    if (!silent) {
                        Swal.fire({ icon: 'error', title: 'Lỗi lưu danh mục', text: data.message });
                    }
                    return { success: false, message: data.message };
                }
            } catch (e) {
                if (!silent) {
                    Swal.fire({ icon: 'error', title: 'Lỗi lưu danh mục', text: e.message });
                }
                return { success: false, message: e.message };
            }
        };
        const isSavingDoc = ref(false);
        const saveCurrentDocAndSync = async () => {
            isSavingDoc.value = true;
            try {
                // 1. Lưu vào danh mục văn bản đã soạn thảo
                const draftRes = await saveCurrentDocAsDraft(true);
                if (!draftRes.success) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Không thể lưu vào danh mục',
                        text: draftRes.message || 'Lỗi khi lưu văn bản'
                    });
                    isSavingDoc.value = false;
                    return;
                }

                // 2. Chuẩn bị dữ liệu tài liệu hoàn chỉnh để lưu lên Drive
                const docObj = {
                    doc_type: composerForm.value.doc_type || generatedDoc.value.doc_type || 'THÔNG BÁO',
                    agency_name: composerForm.value.agency_name || generatedDoc.value.agency_name || 'THUẾ TP.HỒ CHÍ MINH',
                    agency_parent: composerForm.value.agency_parent || generatedDoc.value.agency_parent || '',
                    unit_code: composerForm.value.unit_code || generatedDoc.value.unit_code || '',
                    doc_number: composerForm.value.doc_number || generatedDoc.value.doc_number || '01',
                    location: composerForm.value.location || generatedDoc.value.location || 'Tp. Hồ Chí Minh',
                    date_str: composerForm.value.date_str || generatedDoc.value.date_str || todayStr,
                    subject: composerForm.value.subject || composerForm.value.purpose || generatedDoc.value.subject || '',
                    signer_role: composerForm.value.signer_role || generatedDoc.value.signer_role || '[CHỨC VỤ]',
                    signer_name: composerForm.value.signer_name || generatedDoc.value.signer_name || '[Họ và tên]',
                    recipients: (composerForm.value.recipients && composerForm.value.recipients.length > 0) ? composerForm.value.recipients : (generatedDoc.value.recipients || ['- Lưu: VT.']),
                    legal_bases: (generatedDoc.value.legal_bases && generatedDoc.value.legal_bases.length > 0) ? generatedDoc.value.legal_bases : [],
                    body_paragraphs: (generatedDoc.value.body_paragraphs && generatedDoc.value.body_paragraphs.length > 0) ? generatedDoc.value.body_paragraphs : [{ text: composerForm.value.purpose || 'Nội dung văn bản hành chính.' }],
                    header_ratio: composerForm.value.header_ratio || '50/50'
                };

                // Cập nhật generatedDoc để live preview khớp hoàn toàn
                generatedDoc.value = {
                    ...generatedDoc.value,
                    ...docObj
                };

                // 3. Tải lên Google Drive
                const targetFolder = geminiConfig.value.admin_doc_drive_folder_id || '16Ua7ZfjOl2klPOEMH5QxDtvUSQ9A-FTr';
                const driveRes = await saveDocToDrive(docObj, targetFolder, { silent: true });

                const draftTitle = draftRes.draft?.title || composerForm.value.subject || 'Văn bản đã soạn';

                if (driveRes.success) {
                    const data = driveRes.data || {};
                    const folderName = data.folder_name || '____Automation Video____\\Văn thư';
                    const folderUrl = data.folder_url || `https://drive.google.com/drive/folders/${data.folder_id || ''}`;
                    const results = data.results || [];
                    
                    let filesHtml = '';
                    results.forEach(r => {
                        const icon = r.format === 'docx' ? 'fa-file-word text-blue-600' : 'fa-file-pdf text-red-600';
                        const label = r.format === 'docx' ? 'Bản Word (.docx)' : 'Bản PDF (.pdf)';
                        const link = r.view_link || (r.drive_result && r.drive_result.webViewLink);
                        filesHtml += `
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; margin-top: 6px;">
                                <div style="text-align: left; font-size: 13px;">
                                    <i class="fa-solid ${icon}"></i> <b>${label}:</b> <span style="color: #475569;">${r.filename}</span>
                                </div>
                                ${link ? `<a href="${link}" target="_blank" rel="noopener noreferrer" style="padding: 4px 10px; background: #004b93; color: white; border-radius: 4px; font-size: 12px; text-decoration: none; font-weight: bold; margin-left: 8px; white-space: nowrap;">
                                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Mở file
                                </a>` : ''}
                            </div>
                        `;
                    });

                    Swal.fire({
                        icon: 'success',
                        title: 'Lưu văn bản thành công!',
                        html: `
                            <div style="text-align: left; font-size: 13px; line-height: 1.6; color: #1e293b;">
                                <div style="margin-bottom: 12px; padding: 10px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px;">
                                    <i class="fa-solid fa-circle-check" style="color: #16a34a;"></i> <b>Danh mục hệ thống:</b> Đã lưu vào <b>"Chọn văn bản từ danh sách đã soạn"</b> với tên <i>"${draftTitle}"</i>.
                                </div>
                                <div style="margin-bottom: 10px; padding: 10px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px;">
                                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: gap-2;">
                                        <div>
                                            <i class="fa-brands fa-google-drive" style="color: #2563eb;"></i> <b>Nơi lưu Google Drive:</b><br>
                                            📁 <span style="font-weight: bold; color: #1d4ed8;">${folderName}</span>
                                        </div>
                                        <a href="${folderUrl}" target="_blank" rel="noopener noreferrer" style="padding: 5px 12px; background: #2563eb; color: white; border-radius: 5px; font-size: 12px; text-decoration: none; font-weight: bold; display: inline-flex; align-items: center; gap: 4px;">
                                            <i class="fa-solid fa-folder-open"></i> Mở thư mục Drive
                                        </a>
                                    </div>
                                </div>
                                ${data.local_folder ? `
                                <div style="margin-bottom: 10px; padding: 10px; background: #fdf2f8; border: 1px solid #fbcfe8; border-radius: 6px;">
                                    <i class="fa-solid fa-hard-drive" style="color: #db2777;"></i> <b>Thư mục máy tính (Local):</b><br>
                                    📁 <span style="font-weight: bold; color: #be185d;">____Automation Video____\\Văn thư</span>
                                    <div style="font-size: 11px; color: #64748b; margin-top: 2px; font-family: monospace; word-break: break-all;">${data.local_folder}</div>
                                </div>` : ''}
                                <div style="margin-top: 10px;">
                                    <b>Các tệp văn bản đã lưu lên Drive:</b>
                                    ${filesHtml}
                                </div>
                            </div>
                        `,
                        confirmButtonText: 'Tuyệt vời',
                        confirmButtonColor: '#004b93',
                        width: 580
                    });
                } else {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Đã lưu danh mục, chưa đồng bộ lên Drive',
                        html: `
                            <p style="text-align: left; font-size: 13px;">
                                ✅ Đã lưu văn bản <b>"${draftTitle}"</b> vào <b>"Chọn văn bản từ danh sách đã soạn"</b>.<br><br>
                                ⚠️ <i>Thông báo Drive:</i> ${driveRes.message || 'Không thể đồng bộ lên Google Drive'}
                            </p>
                        `,
                        confirmButtonColor: '#004b93'
                    });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi', text: e.message });
            } finally {
                isSavingDoc.value = false;
            }
        };
        const deleteCurrentDraft = async () => {
            if (!selectedDraftId.value) return;
            const res = await Swal.fire({
                title: 'Xác nhận xóa?',
                text: 'Bạn có chắc chắn muốn xóa văn bản này khỏi danh sách đã soạn?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                confirmButtonText: 'Xóa ngay',
                cancelButtonText: 'Hủy'
            });
            if (res.isConfirmed) {
                try {
                    const resp = await fetch(`/api/admin-doc/drafts/${selectedDraftId.value}`, {
                        method: 'DELETE'
                    });
                    const data = await resp.json();
                    if (data.success) {
                        draftedDocuments.value = data.drafts;
                        selectedDraftId.value = '';
                        Swal.fire({ icon: 'success', title: 'Đã xóa!', timer: 1500, showConfirmButton: false });
                    }
                } catch (e) {
                    Swal.fire({ icon: 'error', title: 'Lỗi xóa', text: e.message });
                }
            }
        };

        // ==================== LƯU THAM SỐ MẶC ĐỊNH SOẠN THẢO VĂN BẢN (BƯỚC 1 & BƯỚC 2) ====================
        const isSavingComposerParams = ref(false);
        const applySavedComposerParams = (saved) => {
            if (!saved || typeof saved !== 'object' || Object.keys(saved).length === 0) return false;
            const keys = [
                'template_preset', 'doc_format', 'doc_type', 'agency_parent', 'agency_code',
                'agency_name', 'is_joint_doc', 'location', 'doc_date', 'doc_number_seq',
                'doc_number', 'header_ratio', 'signer_role', 'signer_name',
                'purpose', 'target_audience', 'legal_bases', 'structure_req'
            ];
            keys.forEach(k => {
                if (saved[k] !== undefined && saved[k] !== null) {
                    composerForm.value[k] = saved[k];
                }
            });
            if (Array.isArray(saved.recipients)) {
                composerForm.value.recipients = [...saved.recipients];
            }
            updateLivePreviewFromForm();
            return true;
        };

        const loadComposerDefaultParams = async () => {
            try {
                const localRaw = localStorage.getItem('manage_app_composer_default_params');
                if (localRaw) {
                    try {
                        applySavedComposerParams(JSON.parse(localRaw));
                    } catch (_) {}
                }
                const res = await fetch('/api/admin-doc/default-params');
                const data = await res.json();
                if (data.success && data.params && Object.keys(data.params).length > 0) {
                    applySavedComposerParams(data.params);
                    localStorage.setItem('manage_app_composer_default_params', JSON.stringify(data.params));
                }
            } catch (e) {
                console.error('Lỗi tải tham số mặc định Soạn thảo văn bản:', e);
            }
        };

        const saveComposerDefaultParams = async () => {
            isSavingComposerParams.value = true;
            try {
                const payloadParams = {
                    template_preset: composerForm.value.template_preset,
                    doc_format: composerForm.value.doc_format,
                    doc_type: composerForm.value.doc_type,
                    agency_parent: composerForm.value.agency_parent,
                    agency_code: composerForm.value.agency_code,
                    agency_name: composerForm.value.agency_name,
                    is_joint_doc: composerForm.value.is_joint_doc,
                    location: composerForm.value.location,
                    doc_date: composerForm.value.doc_date,
                    doc_number_seq: composerForm.value.doc_number_seq,
                    doc_number: composerForm.value.doc_number,
                    header_ratio: composerForm.value.header_ratio,
                    recipients: [...(composerForm.value.recipients || [])],
                    signer_role: composerForm.value.signer_role,
                    signer_name: composerForm.value.signer_name,
                    purpose: composerForm.value.purpose,
                    target_audience: composerForm.value.target_audience,
                    legal_bases: composerForm.value.legal_bases,
                    structure_req: composerForm.value.structure_req
                };
                localStorage.setItem('manage_app_composer_default_params', JSON.stringify(payloadParams));
                const res = await fetch('/api/admin-doc/default-params', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ params: payloadParams })
                });
                const data = await res.json();
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Đã lưu tham số mặc định!',
                        text: 'Toàn bộ thiết lập ở Bước 1 (Thiết lập ban đầu) và Bước 2 (Nội dung AI) đã được lưu làm mặc định cho các lần truy cập sau.',
                        timer: 2200,
                        showConfirmButton: false
                    });
                } else {
                    showToast(data.message || 'Đã lưu tham số vào trình duyệt.', 'info');
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi lưu tham số', text: e.message });
            } finally {
                isSavingComposerParams.value = false;
            }
        };

        const resetToDefaultComposerParams = async () => {
            selectedDraftId.value = '';
            composerStep.value = 1;
            await loadComposerDefaultParams();
        };

        // ==================== CẤU HÌNH VĂN BẢN HÀNH CHÍNH (THƯ MỤC GOOGLE DRIVE, NOTEBOOKLM & CACHE TOKEN) ====================
        const adminDocConfig = ref({
            reference_folder_id: '',
            reference_folder_name: 'Tax_Nghiệp vụ thuế',
            notebook_id: '',
            notebook_name: 'Tax_Nghiệp vụ thuế',
            enable_reference_on_generate: true,
            auto_sync_notebooklm: true
        });
        const adminConfigDriveFolders = ref([]);
        const adminConfigTaxOnlyFilter = ref(false);
        const isLoadingAdminConfigFolders = ref(false);
        const isSavingAdminDocConfig = ref(false);
        const adminDocConfigFiles = ref([]);
        const isLoadingAdminDocFiles = ref(false);
        const isUploadingAdminDocPdf = ref(false);
        const isCachingAdminDocFiles = ref(false);
        const adminDocConfigCachedCount = computed(() => {
            return adminDocConfigFiles.value.filter(f => f.is_cached).length;
        });

        const loadAdminDocDriveFolders = async () => {
            isLoadingAdminConfigFolders.value = true;
            try {
                const res = await fetch(`/api/assistants/drive-folders?tax_only=${adminConfigTaxOnlyFilter.value ? 'true' : 'false'}`);
                const data = await res.json();
                if (data.success && Array.isArray(data.folders)) {
                    adminConfigDriveFolders.value = data.folders;
                } else if (folders.value && folders.value.length > 0) {
                    adminConfigDriveFolders.value = folders.value.map(f => ({
                        id: f.id,
                        name: f.raw_name || String(f.name || '').replace('📁 ', '').replace(' ⭐ [Mặc định]', '').trim()
                    }));
                }
            } catch (e) {
                console.error('Lỗi tải danh sách thư mục Drive cho Cấu hình Văn bản hành chính:', e);
            } finally {
                isLoadingAdminConfigFolders.value = false;
            }
        };

        const loadAdminDocConfigSettings = async () => {
            try {
                const localRaw = localStorage.getItem('manage_app_admin_doc_config');
                if (localRaw) {
                    try {
                        adminDocConfig.value = Object.assign({}, adminDocConfig.value, JSON.parse(localRaw));
                    } catch (_) {}
                }
                const res = await fetch('/api/admin-doc/config');
                const contentType = res.headers.get('content-type') || '';
                if (!res.ok || !contentType.includes('application/json')) return;
                const data = await res.json();
                if (data.success && data.config) {
                    adminDocConfig.value = Object.assign({}, adminDocConfig.value, data.config);
                    localStorage.setItem('manage_app_admin_doc_config', JSON.stringify(adminDocConfig.value));
                }
            } catch (e) {
                console.error('Lỗi tải cấu hình Văn bản hành chính:', e);
            }
        };

        const loadAdminDocConfigFiles = async () => {
            isLoadingAdminDocFiles.value = true;
            try {
                const fid = encodeURIComponent(adminDocConfig.value.reference_folder_id || '');
                const fname = encodeURIComponent(adminDocConfig.value.reference_folder_name || '');
                const res = await fetch(`/api/admin-doc/config/files?folder_id=${fid}&folder_name=${fname}`);
                const contentType = res.headers.get('content-type') || '';
                if (!res.ok || !contentType.includes('application/json')) return;
                const data = await res.json();
                if (data.success) {
                    adminDocConfigFiles.value = data.files || [];
                    if (data.notebook_name) {
                        adminDocConfig.value.notebook_name = data.notebook_name;
                    }
                    if (data.folder_name) {
                        adminDocConfig.value.reference_folder_name = data.folder_name;
                    }
                }
            } catch (e) {
                console.error('Lỗi tải danh sách file trong thư mục tham chiếu:', e);
            } finally {
                isLoadingAdminDocFiles.value = false;
            }
        };

        const onAdminDocReferenceFolderChange = async () => {
            const found = adminConfigDriveFolders.value.find(f => f.id === adminDocConfig.value.reference_folder_id);
            if (found) {
                adminDocConfig.value.reference_folder_name = found.name;
                adminDocConfig.value.notebook_name = found.name;
            }
            await saveAdminDocConfigSettings(false);
            await loadAdminDocConfigFiles();
        };

        const saveAdminDocConfigSettings = async (showAlert = true) => {
            const shouldNotify = showAlert !== false;
            isSavingAdminDocConfig.value = true;
            try {
                const found = adminConfigDriveFolders.value.find(f => f.id === adminDocConfig.value.reference_folder_id);
                if (found) {
                    adminDocConfig.value.reference_folder_name = found.name;
                    adminDocConfig.value.notebook_name = found.name;
                }
                localStorage.setItem('manage_app_admin_doc_config', JSON.stringify(adminDocConfig.value));

                const res = await fetch('/api/admin-doc/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(adminDocConfig.value)
                });
                const contentType = res.headers.get('content-type') || '';
                if (!contentType.includes('application/json')) {
                    throw new Error(`Máy chủ trả về phản hồi không hợp lệ (HTTP ${res.status}). Vui lòng tải lại trang.`);
                }
                const data = await res.json();
                if (data.success && data.config) {
                    adminDocConfig.value = Object.assign({}, adminDocConfig.value, data.config);
                    localStorage.setItem('manage_app_admin_doc_config', JSON.stringify(adminDocConfig.value));
                    await loadNotebooks();
                    if (shouldNotify) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Đã lưu cấu hình!',
                            text: data.message || `Đã lưu thư mục tham chiếu "${adminDocConfig.value.reference_folder_name}" và đồng bộ NotebookLM trùng tên.`,
                            timer: 2000,
                            showConfirmButton: false
                        });
                    }
                } else if (shouldNotify) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Lỗi lưu cấu hình',
                        text: data.message || 'Không thể lưu cấu hình.'
                    });
                }
            } catch (e) {
                if (shouldNotify) {
                    Swal.fire({ icon: 'error', title: 'Lỗi lưu cấu hình', text: e.message });
                }
            } finally {
                isSavingAdminDocConfig.value = false;
            }
        };

        const handleAdminDocConfigPdfUpload = async (e) => {
            const fileList = e.target.files;
            if (!fileList || fileList.length === 0) return;
            isUploadingAdminDocPdf.value = true;
            try {
                const formData = new FormData();
                for (let i = 0; i < fileList.length; i++) {
                    formData.append('files', fileList[i]);
                }
                formData.append('folder_id', adminDocConfig.value.reference_folder_id || '');
                formData.append('folder_name', adminDocConfig.value.reference_folder_name || '');

                const res = await fetch('/api/admin-doc/config/upload-pdf', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (data.success) {
                    adminDocConfigFiles.value = data.files || [];
                    if (data.notebook_name) {
                        adminDocConfig.value.notebook_name = data.notebook_name;
                    }
                    await loadNotebooks();
                    Swal.fire({
                        icon: 'success',
                        title: 'Tải lên & Đồng bộ thành công!',
                        html: `<div class="text-xs text-left space-y-1">
                            <div><b>• Số tệp đã tải lên:</b> ${data.uploaded_count} tệp</div>
                            <div><b>• Thư mục Google Drive:</b> 📁 ${data.folder_name}</div>
                            <div><b>• Đồng bộ NotebookLM:</b> 📓 ${data.notebook_name}</div>
                            <div><b>• Bộ nhớ đệm AI (Token Cache):</b> Đã trích xuất & lưu trữ quy định để không tốn Token cho các lần sau!</div>
                        </div>`,
                        confirmButtonColor: '#004b93'
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Lỗi tải lên', text: data.message || 'Không thể tải tệp lên.' });
                }
            } catch (err) {
                Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: err.message });
            } finally {
                isUploadingAdminDocPdf.value = false;
                e.target.value = '';
            }
        };

        const processAndCacheAllFolderFiles = async (force = false) => {
            isCachingAdminDocFiles.value = true;
            try {
                const res = await fetch('/api/admin-doc/config/cache-files', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        folder_id: adminDocConfig.value.reference_folder_id,
                        folder_name: adminDocConfig.value.reference_folder_name,
                        force: force
                    })
                });
                const data = await res.json();
                if (data.success) {
                    adminDocConfigFiles.value = data.files || [];
                    showToast(data.message || 'Đã xử lý & lưu bộ nhớ đệm AI thành công!', 'success');
                } else {
                    showToast(data.message || 'Không thể xử lý Cache.', 'warning');
                }
            } catch (e) {
                showToast('Lỗi khi xử lý Cache: ' + e.message, 'error');
            } finally {
                isCachingAdminDocFiles.value = false;
            }
        };

        const processSingleAdminDocFileCache = async (file) => {
            if (!file) return;
            isCachingAdminDocFiles.value = true;
            try {
                const res = await fetch('/api/admin-doc/config/cache-files', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        folder_id: adminDocConfig.value.reference_folder_id,
                        folder_name: adminDocConfig.value.reference_folder_name,
                        file_id: file.id,
                        force: true
                    })
                });
                const data = await res.json();
                if (data.success) {
                    adminDocConfigFiles.value = data.files || [];
                    showToast(`Đã lưu trữ quy định của tệp "${file.name}" vào bộ nhớ đệm (Token Cache)!`, 'success');
                }
            } catch (e) {
                showToast('Lỗi lưu Cache tệp: ' + e.message, 'error');
            } finally {
                isCachingAdminDocFiles.value = false;
            }
        };

        const openAdminDocConfigMenu = async () => {
            activeMenu.value = 'admin_config';
            await loadAdminDocConfigSettings();
            await loadAdminDocDriveFolders();
            await loadAdminDocConfigFiles();
        };
        // ==================== QUẢN LÝ CHỌN NHIỀU THƯ MỤC CẤP 1 DRIVE ====================
        const selectedDriveFolderIds = ref([]);
        const loadSelectedDriveFolders = async () => {
            try {
                const resp = await fetch('/api/drive/selected-folders');
                const data = await resp.json();
                if (data.success && Array.isArray(data.selected_folder_ids)) {
                    selectedDriveFolderIds.value = data.selected_folder_ids;
                }
            } catch (e) {
                console.error('Lỗi tải danh sách thư mục đã chọn:', e);
            }
        };
        const toggleFolderSelection = (fid) => {
            const idx = selectedDriveFolderIds.value.indexOf(fid);
            if (idx === -1) {
                selectedDriveFolderIds.value.push(fid);
            } else {
                selectedDriveFolderIds.value.splice(idx, 1);
            }
        };
        const toggleSelectAllFolders = () => {
            if (selectedDriveFolderIds.value.length === folders.value.length) {
                selectedDriveFolderIds.value = [];
            } else {
                selectedDriveFolderIds.value = folders.value.map(f => f.id);
            }
        };
        const saveSelectedFolders = async () => {
            try {
                const resp = await fetch('/api/drive/selected-folders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ selected_folder_ids: selectedDriveFolderIds.value })
                });
                const data = await resp.json();
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Đã lưu danh sách thư mục!',
                        text: `Đã chọn ${selectedDriveFolderIds.value.length} thư mục Google Drive cấp 1.`,
                        timer: 2000,
                        showConfirmButton: false
                    });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi lưu thư mục', text: e.message });
            }
        };
        // 3. CẤU HÌNH GEMINI AI
        const geminiConfig = ref({
            api_key: '',
            model: 'gemini-2.5-flash',
            admin_doc_drive_folder_id: '1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK',
            admin_doc_drive_folder_name: '📁 Tax_Nghiệp vụ thuế'
        });
        const isTestingGemini = ref(false);
        const isSavingGeminiConfig = ref(false);
        const loadGeminiConfig = async () => {
            try {
                const resp = await fetch('/api/config/gemini');
                const data = await resp.json();
                if (data) {
                    geminiConfig.value = {
                        api_key: data.api_key || '',
                        model: data.model || 'gemini-2.5-flash',
                        admin_doc_drive_folder_id: data.admin_doc_drive_folder_id || defaultFolderId.value,
                        admin_doc_drive_folder_name: data.admin_doc_drive_folder_name || defaultFolderName.value
                    };
                    checkerSelectedDriveFolder.value = geminiConfig.value.admin_doc_drive_folder_id;
                }
            } catch (e) {
                console.error('Lỗi tải cấu hình Gemini:', e);
            }
        };
        const saveGeminiConfig = async () => {
            isSavingGeminiConfig.value = true;
            try {
                const resp = await fetch('/api/config/gemini', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(geminiConfig.value)
                });
                const data = await resp.json();
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Đã lưu cấu hình Gemini AI',
                        text: 'Cấu hình Gemini API và thư mục Drive mặc định đã được cập nhật thành công.',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Lỗi lưu', text: data.message });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi hệ thống', text: e.message });
            } finally {
                isSavingGeminiConfig.value = false;
            }
        };
        const testGeminiConnection = async () => {
            isTestingGemini.value = true;
            try {
                const resp = await fetch('/api/gemini/test-connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        api_key: geminiConfig.value.api_key,
                        model: geminiConfig.value.model 
                    })
                });
                const data = await resp.json();
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Kết nối thành công!',
                        text: data.message
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Kết nối thất bại',
                        text: data.message
                    });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: e.message });
            } finally {
                isTestingGemini.value = false;
            }
        };

        // ==================== PHÂN HỆ TRỢ LÝ AI (AI ASSISTANT & VERTEX SEARCH) ====================
        const aiAssistants = ref([]);
        const isLoadingAssistants = ref(false);
        const activeAssistantId = ref('asst_tax_corp');
        
        const activeAssistant = computed(() => {
            if (!aiAssistants.value || aiAssistants.value.length === 0) return null;
            return aiAssistants.value.find(a => a.id === activeAssistantId.value) || aiAssistants.value[0];
        });
        // Thiết lập tùy biến cho chức năng trợ lý này (Runtime Session Overrides - không đổi thiết lập gốc)
        const sessionConfig = ref({
            drive_folder_ids: ['1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK'],
            filter_tax_only: true,
            enable_web_search: true,
            model: 'gemini-3.5-flash-lite',
            temperature: 0.2
        });
        const isCustomizationOpen = ref(true);
        const toggleCustomization = () => {
            isCustomizationOpen.value = !isCustomizationOpen.value;
        };
        // Danh sách thư mục hiển thị theo bộ lọc Tax của phiên tùy biến
        const visibleSessionFolders = computed(() => {
            if (!driveFoldersForAssistant.value || driveFoldersForAssistant.value.length === 0) {
                return [];
            }
            if (sessionConfig.value.filter_tax_only) {
                return driveFoldersForAssistant.value.filter(f => f.has_tax);
            }
            return driveFoldersForAssistant.value;
        });
        const toggleSessionFolder = (folderId) => {
            if (!sessionConfig.value.drive_folder_ids) {
                sessionConfig.value.drive_folder_ids = [];
            }
            const idx = sessionConfig.value.drive_folder_ids.indexOf(folderId);
            if (idx === -1) {
                sessionConfig.value.drive_folder_ids.push(folderId);
            } else {
                sessionConfig.value.drive_folder_ids.splice(idx, 1);
            }
        };
        const handleSessionTaxFilterToggle = () => {
            loadAssistantDriveFolders(sessionConfig.value.filter_tax_only);
        };
        const resetSessionConfig = () => {
            const asst = activeAssistant.value;
            if (asst) {
                sessionConfig.value = {
                    drive_folder_ids: Array.isArray(asst.drive_folder_ids) && asst.drive_folder_ids.length > 0 ? [...asst.drive_folder_ids] : ['1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK'],
                    filter_tax_only: asst.filter_tax_only !== false,
                    enable_web_search: asst.enable_web_search !== false,
                    model: asst.model || 'gemini-3.5-flash-lite',
                    temperature: asst.temperature !== undefined ? asst.temperature : 0.2
                };
                loadAssistantDriveFolders(sessionConfig.value.filter_tax_only);
                Swal.fire({
                    icon: 'info',
                    title: 'Đã khôi phục',
                    text: 'Đã khôi phục về thiết lập ban đầu của trợ lý.',
                    timer: 1200,
                    showConfirmButton: false
                });
            }
        };
        const isAssistantActive = (asstId) => {
            return activeAssistantId.value === asstId && 
                (activeMenu.value === 'asst_' + asstId || activeMenu.value.startsWith('asst_') || activeMenu.value === 'ai_assistant_chat');
        };
        const activeAssistantDriveFolderNames = computed(() => {
            const asst = activeAssistant.value;
            if (!asst || !asst.drive_folder_ids || asst.drive_folder_ids.length === 0) {
                return ['📁 Tax_Nghiệp vụ thuế ⭐ [Mặc định]'];
            }
            return asst.drive_folder_ids.map(fId => {
                const found = driveFoldersForAssistant.value.find(f => f.id === fId) || 
                              allDriveFolders.value.find(f => f.id === fId);
                return found ? (found.raw_name || found.name) : 'Tax_Nghiệp vụ thuế';
            });
        });
        // Modal Thêm / Chỉnh sửa Trợ lý
        const assistantModalOpen = ref(false);
        const isEditingAssistant = ref(false);
        const isSavingAssistant = ref(false);
        const assistantTaxOnlyFilter = ref(true);
        const driveFoldersForAssistant = ref([]);
        const isLoadingAssistantFolders = ref(false);
        // Danh mục toàn bộ nhân vật vũ trụ Doraemon
        const DORAEMON_ALL_CHARACTERS = [
            { key: 'doraemon', name: 'Doraemon', badge: 'Đôrêmon', title: 'Mèo máy thông minh thế kỷ 22', avatar: '🐱' },
            { key: 'shizuka', name: 'Shizuka', badge: 'Xuka', title: 'Dịu dàng, chăm chỉ & chu đáo', avatar: '👧' },
            { key: 'suneo', name: 'Suneo', badge: 'Xêkô', title: 'Mỏ nhọn, nhanh nhẹn & sắc sảo', avatar: '🦊' },
            { key: 'gian', name: 'Gian', badge: 'Chaien', title: 'Mạnh mẽ, quyết đoán & uy quyền', avatar: '🦁' },
            { key: 'dorami', name: 'Dorami', badge: 'Đôrêmi', title: 'Em gái Doraemon, cẩn thận & thông minh', avatar: '🎀' },
            { key: 'dekisugi', name: 'Dekisugi', badge: 'Đêkhi', title: 'Học thức uyên bác, hoàn hảo & lịch thiệp', avatar: '🎓' },
            { key: 'jaiko', name: 'Jaiko', badge: 'Chaiko', title: 'Em gái Chaien, đam mê hội họa & kiên trì', avatar: '🎨' },
            { key: 'minidora', name: 'Mini-Dora', badge: 'Dora Mini', title: 'Nhanh nhẹn, đáng yêu & đa năng', avatar: '🔴' },
            { key: 'sensei', name: 'Sensei', badge: 'Thầy giáo', title: 'Kỷ luật, nghiêm túc & công minh', avatar: '👓' },
            { key: 'kaminari', name: 'Kaminari', badge: 'Bác Kaminari', title: 'Bác hàng xóm - Trực tính & trách nhiệm', avatar: '⚡' },
            { key: 'sewashi', name: 'Sewashi', badge: 'Nôbitoru', title: 'Cháu cố Nobita từ tương lai thế kỷ 22', avatar: '🚀' }
        ];
        // Danh sách nhân vật Doraemon chưa được chọn (trừ trợ lý đang sửa)
        const availableDoraemonCharacters = computed(() => {
            const currentEditingId = assistantForm.value ? assistantForm.value.id : '';
            const usedNicknames = aiAssistants.value
                .filter(a => a.id !== currentEditingId)
                .map(a => (a.nickname || '').trim().toLowerCase())
                .filter(Boolean);
            return DORAEMON_ALL_CHARACTERS.filter(char => {
                const charName = char.name.toLowerCase();
                const charKey = char.key.toLowerCase();
                const charBadge = (char.badge || '').toLowerCase();
                return !usedNicknames.some(u => 
                    u === charName || u === charKey || u === charBadge ||
                    charName.includes(u) || u.includes(charName) ||
                    charKey.includes(u) || u.includes(charKey)
                );
            });
        });
        const assistantForm = ref({
            id: '',
            name: '',
            description: '',
            system_prompt: '',
            drive_folder_ids: [],
            filter_tax_only: true,
            enable_web_search: true,
            model: 'gemini-2.5-flash',
            temperature: 0.2
        });
        // Chat cùng Trợ lý
        const chatMessages = ref([
            {
                sender: 'assistant',
                text: 'Xin chào! Tôi là **Trợ lý AI** chuyên trách của bạn.\n\nBạn có thể đặt câu hỏi về chính sách thuế, thể thức văn bản, **dán ảnh trực tiếp từ clipboard (Ctrl + V)** hoặc **đính kèm tệp PDF / Word / Excel** để tôi tra cứu từ Google Drive và Internet!',
                citations: [],
                web_sources: [],
                web_queries: [],
                timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
            }
        ]);
        const chatInputText = ref('');
        const isSendingChat = ref(false);
        const chatImages = ref([]); // [{ mime_type, data, previewUrl }]
        const chatAttachments = ref([]); // [{ filename, mime_type, data, size }]
        const renderChatMarkdown = (text) => {
            if (!text) return '';
            try {
                if (typeof marked !== 'undefined' && marked.parse) {
                    return marked.parse(text);
                }
            } catch (e) {
                console.warn('Error parsing markdown:', e);
            }
            return text.replace(/\n/g, '<br/>');
        };
        const loadAssistants = async () => {
            isLoadingAssistants.value = true;
            try {
                const res = await fetch('/api/assistants');
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    aiAssistants.value = data.assistants || [];
                    if (!activeAssistantId.value && aiAssistants.value.length > 0) {
                        activeAssistantId.value = aiAssistants.value[0].id;
                    }
                }
            } catch (e) {
                console.error('Error loading assistants:', e);
            } finally {
                isLoadingAssistants.value = false;
            }
        };
        const loadAssistantDriveFolders = async (taxOnly = true) => {
            isLoadingAssistantFolders.value = true;
            try {
                const res = await fetch(`/api/assistants/drive-folders?tax_only=${taxOnly ? 'true' : 'false'}`);
                const data = await res.json();
                if ((data.status === 'success' || data.success) && Array.isArray(data.folders) && data.folders.length > 0) {
                    driveFoldersForAssistant.value = data.folders;
                } else if (allDriveFolders.value && allDriveFolders.value.length > 0) {
                    const mapped = allDriveFolders.value.map(f => ({
                        id: f.id,
                        name: f.raw_name || f.name.replace('📁 ', '').replace(' ⭐ [Mặc định]', '').trim(),
                        display_name: f.name,
                        has_tax: f.is_tax || (f.name && (f.name.toLowerCase().includes('tax') || f.name.toLowerCase().includes('thuế')))
                    }));
                    driveFoldersForAssistant.value = taxOnly ? mapped.filter(f => f.has_tax) : mapped;
                }
            } catch (e) {
                console.error('Error loading assistant drive folders:', e);
                if (allDriveFolders.value && allDriveFolders.value.length > 0) {
                    const mapped = allDriveFolders.value.map(f => ({
                        id: f.id,
                        name: f.raw_name || f.name,
                        display_name: f.name,
                        has_tax: f.is_tax || (f.name && (f.name.toLowerCase().includes('tax') || f.name.toLowerCase().includes('thuế')))
                    }));
                    driveFoldersForAssistant.value = taxOnly ? mapped.filter(f => f.has_tax) : mapped;
                }
            } finally {
                isLoadingAssistantFolders.value = false;
            }
        };
        const handleAssistantTaxFilterChange = () => {
            loadAssistantDriveFolders(assistantTaxOnlyFilter.value);
        };
        const getAssistantFolderNames = (asst) => {
            if (!asst || !asst.drive_folder_ids || asst.drive_folder_ids.length === 0) {
                return ['Tax_Nghiệp vụ thuế [Mặc định]'];
            }
            return asst.drive_folder_ids.map(fId => {
                const found = (driveFoldersForAssistant.value && driveFoldersForAssistant.value.find(f => f.id === fId)) ||
                              (allDriveFolders.value && allDriveFolders.value.find(f => f.id === fId));
                if (found) {
                    return (found.name || found.raw_name || 'Thư mục Drive').replace('📁 ', '').replace(' ⭐ [Mặc định]', '').trim();
                }
                return 'Tax_Nghiệp vụ thuế';
            });
        };
        const getDoraemonCharacterName = (asst) => {
            if (!asst) return 'Doraemon';
            if (asst.nickname) return asst.nickname;
            const names = ['Doraemon', 'Shizuka', 'Suneo', 'Gian', 'Dorami', 'Dekisugi', 'Jaiko'];
            let hash = 0;
            const str = asst.id || asst.name || 'asst';
            for (let i = 0; i < str.length; i++) hash += str.charCodeAt(i);
            return names[hash % names.length];
        };
        const resetOfficeCamera = () => {
            if (window.DoraemonOfficeController) {
                window.DoraemonOfficeController.resetCamera();
            }
        };
        const openCreateAssistantModal = () => {
            isEditingAssistant.value = false;
            assistantTaxOnlyFilter.value = true;
            const firstAvail = availableDoraemonCharacters.value.length > 0 
                ? availableDoraemonCharacters.value[0].name 
                : 'Doraemon';
            assistantForm.value = {
                id: 'asst_' + Date.now().toString(36),
                name: '',
                nickname: firstAvail,
                description: '',
                system_prompt: 'Bạn là Trợ lý chuyên môn cao ngành Thuế. Hãy giải đáp chính xác, khách quan, trích dẫn rõ các văn bản quy phạm pháp luật và căn cứ thực tế.',
                drive_folder_ids: [],
                filter_tax_only: true,
                enable_web_search: false,
                model: 'gemini-3.5-flash-lite',
                temperature: 0.2
            };
            loadAssistantDriveFolders(true);
            assistantModalOpen.value = true;
        };
        const openEditAssistantModal = (asst) => {
            const targetAsst = (asst && asst.id)
                ? (aiAssistants.value.find(a => a.id === asst.id) || asst)
                : (aiAssistants.value.find(a => a.id === asst) || asst || {});
            isEditingAssistant.value = true;
            assistantTaxOnlyFilter.value = targetAsst.filter_tax_only !== false;
            assistantForm.value = {
                id: targetAsst.id,
                name: targetAsst.name || '',
                nickname: targetAsst.nickname || '',
                description: targetAsst.description || '',
                system_prompt: targetAsst.system_prompt || '',
                drive_folder_ids: Array.isArray(targetAsst.drive_folder_ids) ? [...targetAsst.drive_folder_ids] : [],
                filter_tax_only: targetAsst.filter_tax_only !== false,
                enable_web_search: targetAsst.enable_web_search === true,
                model: targetAsst.model || 'gemini-3.5-flash-lite',
                temperature: targetAsst.temperature !== undefined ? targetAsst.temperature : 0.2
            };
            loadAssistantDriveFolders(assistantTaxOnlyFilter.value);
            assistantModalOpen.value = true;
        };
        const toggleFolderForAssistant = (folderId) => {
            if (!assistantForm.value.drive_folder_ids) {
                assistantForm.value.drive_folder_ids = [];
            }
            const idx = assistantForm.value.drive_folder_ids.indexOf(folderId);
            if (idx === -1) {
                assistantForm.value.drive_folder_ids.push(folderId);
            } else {
                assistantForm.value.drive_folder_ids.splice(idx, 1);
            }
        };
        const saveAssistant = async () => {
            if (!assistantForm.value.name.trim()) {
                Swal.fire({ icon: 'warning', title: 'Thiếu thông tin', text: 'Vui lòng nhập tên trợ lý!' });
                return;
            }
            isSavingAssistant.value = true;
            try {
                const res = await fetch('/api/assistants', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(assistantForm.value)
                });
                const data = await res.json();
                if (data.status === 'success') {
                    Swal.fire({
                        icon: 'success',
                        title: 'Đã lưu trợ lý!',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    const createdId = (data.assistant && data.assistant.id) || assistantForm.value.id;
                    assistantModalOpen.value = false;
                    await loadAssistants();
                    if (createdId) {
                        selectAssistantForChat(createdId);
                    }
                } else {
                    Swal.fire({ icon: 'error', title: 'Không thể lưu', text: data.message || 'Lỗi không xác định' });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi máy chủ', text: e.message });
            } finally {
                isSavingAssistant.value = false;
            }
        };
        const deleteAssistant = async (asst) => {
            const result = await Swal.fire({
                title: 'Xóa trợ lý này?',
                text: `Bạn có chắc muốn xóa "${asst.name}"?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc2626',
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Đồng ý xóa',
                cancelButtonText: 'Hủy'
            });
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/api/assistants/${asst.id}`, { method: 'DELETE' });
                    const data = await res.json();
                    if (data.status === 'success') {
                        Swal.fire({ icon: 'success', title: 'Đã xóa!', timer: 1200, showConfirmButton: false });
                        await loadAssistants();
                        if (activeAssistantId.value === asst.id && aiAssistants.value.length > 0) {
                            activeAssistantId.value = aiAssistants.value[0].id;
                        }
                    }
                } catch (e) {
                    Swal.fire({ icon: 'error', title: 'Lỗi', text: e.message });
                }
            }
        };
        const scrollChatToBottom = () => {
            setTimeout(() => {
                const el = document.getElementById('chatMessagesScroll');
                if (el) el.scrollTop = el.scrollHeight;
            }, 100);
        };
        const selectAssistantForChat = (asstId) => {
            activeAssistantId.value = asstId;
            activeMenu.value = 'asst_' + asstId;
            const asst = aiAssistants.value.find(a => a.id === asstId);
            if (asst) {
                sessionConfig.value = {
                    drive_folder_ids: Array.isArray(asst.drive_folder_ids) && asst.drive_folder_ids.length > 0 ? [...asst.drive_folder_ids] : ['1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK'],
                    filter_tax_only: asst.filter_tax_only !== false,
                    enable_web_search: asst.enable_web_search !== false,
                    model: asst.model || 'gemini-3.5-flash-lite',
                    temperature: asst.temperature !== undefined ? asst.temperature : 0.2
                };
                loadAssistantDriveFolders(sessionConfig.value.filter_tax_only);
            }
            scrollChatToBottom();
        };
        const clearChatHistory = () => {
            chatMessages.value = [
                {
                    sender: 'assistant',
                    text: 'Hội thoại đã được làm mới. Hãy đặt câu hỏi cho tôi!',
                    citations: [],
                    web_sources: [],
                    timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
                }
            ];
        };
        // Xử lý dán ảnh từ Clipboard (Ctrl + V)
        const handleChatPaste = (e) => {
            const clipboardData = e.clipboardData || window.clipboardData;
            if (!clipboardData) return;
            const items = clipboardData.items;
            if (!items) return;
            for (let i = 0; i < items.length; i++) {
                const item = items[i];
                if (item.type.indexOf('image') !== -1) {
                    const file = item.getAsFile();
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        const b64 = event.target.result.split(',')[1];
                        chatImages.value.push({
                            mime_type: item.type,
                            data: b64,
                            previewUrl: event.target.result
                        });
                    };
                    reader.readAsDataURL(file);
                    e.preventDefault();
                }
            }
        };
        // Xử lý đính kèm tệp văn bản hoặc hình ảnh
        const handleChatFileUpload = (e) => {
            const files = e.target.files;
            if (!files || files.length === 0) return;
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const reader = new FileReader();
                reader.onload = (event) => {
                    const b64 = event.target.result.split(',')[1];
                    if (file.type && file.type.startsWith('image/')) {
                        chatImages.value.push({
                            mime_type: file.type || 'image/png',
                            data: b64,
                            previewUrl: event.target.result
                        });
                    } else {
                        chatAttachments.value.push({
                            filename: file.name,
                            mime_type: file.type || 'application/octet-stream',
                            data: b64,
                            size: (file.size / 1024).toFixed(1) + ' KB'
                        });
                    }
                };
                reader.readAsDataURL(file);
            }
            e.target.value = '';
        };
        const removeChatImage = (idx) => {
            chatImages.value.splice(idx, 1);
        };
        const removeChatAttachment = (idx) => {
            chatAttachments.value.splice(idx, 1);
        };
        const triggerChatFileInput = () => {
            const el = document.getElementById('chatFileInputHidden');
            if (el) el.click();
        };
        // Gửi tin nhắn đến Trợ lý chuyên môn
        const sendChatMessage = async () => {
            const text = chatInputText.value.trim();
            if (!text && chatImages.value.length === 0 && chatAttachments.value.length === 0) {
                return;
            }
            if (isSendingChat.value) return;
            // Push tin nhắn của người dùng
            chatMessages.value.push({
                sender: 'user',
                text: text,
                images: [...chatImages.value],
                attachments: [...chatAttachments.value],
                timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
            });
            const payload = {
                message: text,
                drive_folder_ids: sessionConfig.value.drive_folder_ids || [],
                filter_tax_only: sessionConfig.value.filter_tax_only,
                enable_web_search: sessionConfig.value.enable_web_search,
                model: sessionConfig.value.model,
                temperature: sessionConfig.value.temperature,
                images: chatImages.value.map(img => ({ mime_type: img.mime_type, data: img.data })),
                attachments: chatAttachments.value.map(att => ({ filename: att.filename, mime_type: att.mime_type, data: att.data }))
            };
            // Dọn dẹp ô nhập liệu
            chatInputText.value = '';
            chatImages.value = [];
            chatAttachments.value = [];
            isSendingChat.value = true;
            scrollChatToBottom();
            const targetAsstId = activeAssistantId.value || 'asst_tax_corp';
            if (window.DoraemonOfficeController) {
                window.DoraemonOfficeController.triggerWork(targetAsstId);
            }
            try {
                const res = await fetch(`/api/assistants/${targetAsstId}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === 'success') {
                    chatMessages.value.push({
                        sender: 'assistant',
                        text: data.answer || 'Không nhận được câu trả lời từ AI.',
                        citations: data.citations || [],
                        web_sources: data.web_sources || [],
                        web_queries: data.web_queries || [],
                        timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
                    });
                } else {
                    chatMessages.value.push({
                        sender: 'assistant',
                        text: `⚠️ **Lỗi xử lý:** ${data.message || 'Không thể liên lạc với Gemini hoặc lấy tài liệu Google Drive.'}`,
                        citations: [],
                        web_sources: [],
                        timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
                    });
                }
            } catch (e) {
                chatMessages.value.push({
                    sender: 'assistant',
                    text: `⚠️ **Lỗi kết nối:** ${e.message}`,
                    citations: [],
                    web_sources: [],
                    timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
                });
            } finally {
                isSendingChat.value = false;
                scrollChatToBottom();
                if (window.DoraemonOfficeController) {
                    window.DoraemonOfficeController.finishWork(targetAsstId);
                }
            }
        };
        
        // ==================== PHÂN HỆ THƯ KÝ AI TIN TỨC (NEWS SECRETARIES) ====================
        const secretaries = ref([]);
        const isLoadingSecretaries = ref(false);
        const activeSecretaryId = ref('');
        const latestSecretaryReport = ref(null);
        const isLoadingReport = ref(false);
        const isGeneratingReport = ref(false);
        const runningSecretaries = ref({});
        const secretaryReportsList = ref([]);
        const showReportsHistoryModal = ref(false);
        const selectedReportFilename = ref('');
        const isDeletingReport = ref(false);
        const activeSecretary = computed(() => {
            if (!secretaries.value || secretaries.value.length === 0) return null;
            return secretaries.value.find(s => s.id === activeSecretaryId.value) || secretaries.value[0];
        });
        // Danh sách 10 nhân vật truyện cổ tích Việt Nam
        const fairyTaleCharacters = ref([
            { name: 'Thạch Sanh', title: 'Dũng sĩ Thạch Sanh', desc: 'Chân thật, dũng cảm, diệt chằn tinh, bắn đại bàng', avatar: '🏹', color: '#854d0e', default_role: 'Thư ký Tổng hợp Tin tức & Cảnh báo Rủi ro Pháp lý', default_appearance: 'Dũng sĩ vạm vỡ, áo nâu thắt đai vàng, đeo rìu chiến dũng mãnh sau lưng, mắt sáng kiên nghị' },
            { name: 'Thánh Gióng', title: 'Phù Đổng Thiên Vương', desc: 'Sức mạnh phi thường, nhổ tre đánh giặc, quật khởi', avatar: '🐎', color: '#dc2626', default_role: 'Thư ký Tin tức Đột phá Công nghệ & Chuyển đổi số', default_appearance: 'Tráng sĩ uy phong, giáp đỏ rực rỡ, búi tóc cao dũng mãnh, mang bụi tre ngà vàng sau lưng' },
            { name: 'Mai An Tiêm', title: 'Mai An Tiêm', desc: 'Tự lực cánh sinh, khai hoang lập nghiệp, gieo trồng dưa hấu', avatar: '🍉', color: '#059669', default_role: 'Thư ký Tin tức Kinh tế Nông nghiệp, Ngoại thương & Khởi nghiệp', default_appearance: 'Tự lực cánh sinh kiên định, áo xanh lục tươi sáng, đầu đội quả dưa hấu sọc đỏ xanh tươi mát' },
            { name: 'Chử Đồng Tử', title: 'Chử Đồng Tử', desc: 'Hiếu nghĩa, nhân ái, khai mở thương mại, bến sông giao thương', avatar: '🛶', color: '#ca8a04', default_role: 'Thư ký Tin tức Thương mại Điện tử, Logistics & Thị trường', default_appearance: 'Áo vàng óng màu phù sa sông, nụ cười đôn hậu, túi gấm giao thương bên hông' },
            { name: 'Cô Tấm', title: 'Cô Tấm dịu hiền', desc: 'Cần cù, nhân hậu, vượt qua gian truân, hóa thân kỳ diệu', avatar: '🌸', color: '#ec4899', default_role: 'Thư ký Tin tức Chính sách An sinh Xã hội, Lao động & Thuế TNCN', default_appearance: 'Nữ thư ký dịu dàng, áo tứ thân màu hồng cánh sen, tóc dài thướt tha cài hoa sen, đội nón quai thao' },
            { name: 'Cám', title: 'Cám', desc: 'Nhanh nhẹn, sắc sảo, thích khám phá xu hướng mới', avatar: '🪞', color: '#9333ea', default_role: 'Thư ký Điểm tin Nhanh, Xu hướng Mạng xã hội & Truyền thông', default_appearance: 'Nhanh nhẹn sắc sảo, áo yếm tím hoa cà, tóc đuôi ngựa thắt nơ đỏ thời trang' },
            { name: 'Sơn Tinh', title: 'Sơn Tinh (Tản Viên)', desc: 'Chúa sơn lâm đại ngàn, dời non lấp biển, ngăn lũ bảo vệ mùa màng', avatar: '⛰️', color: '#15803d', default_role: 'Thư ký Tin tức Quy hoạch Đất đai, Môi trường & Bất động sản', default_appearance: 'Chúa non cao uy nghi, áo xanh rừng thẳm, vóc dáng rắn rỏi vững chãi' },
            { name: 'Thủy Tinh', title: 'Thủy Tinh', desc: 'Chúa tể biển khơi, hô mưa gọi gió, quyết liệt kiên trì', avatar: '🌊', color: '#1d4ed8', default_role: 'Thư ký Tin tức Vận tải Biển, Hải quan & Xuất nhập khẩu', default_appearance: 'Chúa tể biển khơi quyết đoán, áo choàng xanh dương sóng nước đại dương' },
            { name: 'An Dương Vương', title: 'An Dương Vương (Thục Phán)', desc: 'Xây thành Cổ Loa, nỏ thần bảo quốc, quyết đoán', avatar: '👑', color: '#991b1b', default_role: 'Thư ký Tin tức Quản trị Doanh nghiệp, Chính sách Vĩ mô & Đầu tư', default_appearance: 'Phong thái đế vương, hoàng bào đỏ thêu chỉ vàng, đầu đội mão vương miện, nỏ thần sau lưng' },
            { name: 'Chú Cuội', title: 'Chú Cuội', desc: 'Thông minh, dí dỏm, ngồi gốc cây đa cung trăng nhìn ngắm nhân gian', avatar: '🌙', color: '#a16207', default_role: 'Thư ký Bình luận Tin tức, Góc nhìn Chuyên gia & Phân tích Đa chiều', default_appearance: 'Thông minh hóm hỉnh, áo gấm nâu trầm dân dã, tóc búi củ tỏi ngộ nghĩnh' }
        ]);
        const showSecretaryModal = ref(false);
        const isEditingSecretary = ref(false);
        const isSavingSecretary = ref(false);
        const isGeneratingSecretaryPrompt = ref(false);
        const secretaryForm = ref({
            id: '',
            name: '',
            character: 'Thạch Sanh',
            appearance: '',
            role: '',
            instruction: '',
            scheduled_time: '08:00'
        });
        const loadSecretaries = async () => {
            isLoadingSecretaries.value = true;
            try {
                const res = await fetch('/api/secretaries');
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    secretaries.value = data.secretaries || [];
                    if (!activeSecretaryId.value && secretaries.value.length > 0) {
                        activeSecretaryId.value = secretaries.value[0].id;
                    }
                }
            } catch (e) {
                console.error('Lỗi tải danh sách thư ký:', e);
            } finally {
                isLoadingSecretaries.value = false;
            }
        };
        const selectSecretaryView = async (secId) => {
            activeSecretaryId.value = secId;
            activeMenu.value = 'sec_' + secId;
            await loadSecretaryReports(secId);
        };
        const formatTimeRange = (rangeKey) => {
            if (rangeKey === 'today_yesterday') return '24h - 48h qua';
            if (rangeKey === '1_week') return '1 tuần trước';
            if (rangeKey === '2_weeks') return '2 tuần trước';
            if (rangeKey === 'custom') return 'Khoảng ngày tùy chọn';
            return '1 tuần trước';
        };
        const openCreateSecretaryModal = () => {
            isEditingSecretary.value = false;
            const defChar = fairyTaleCharacters.value[0];
            secretaryForm.value = {
                id: '',
                name: 'Thư ký ' + defChar.name,
                character: defChar.name,
                appearance: defChar.default_appearance || '',
                role: defChar.default_role,
                instruction: 'Hằng ngày tìm kiếm các tin tức và văn bản chính sách mới nhất trên Internet về lĩnh vực này. Tổng hợp bối cảnh, các điểm mới, thời hạn áp dụng, đánh giá tác động và khuyến nghị hành động cho Ban Giám đốc.',
                scheduled_time: '08:00',
                search_time_range: '1_week',
                search_from_date: '',
                search_to_date: ''
            };
            showSecretaryModal.value = true;
        };
        const openEditSecretaryModal = (sec) => {
            const targetSec = (sec && sec.id)
                ? (secretaries.value.find(s => s.id === sec.id) || sec)
                : (secretaries.value.find(s => s.id === sec) || sec || {});
            isEditingSecretary.value = true;
            secretaryForm.value = {
                id: targetSec.id,
                name: targetSec.name || '',
                character: targetSec.character || 'Thạch Sanh',
                appearance: targetSec.appearance || '',
                role: targetSec.role || '',
                instruction: targetSec.instruction || '',
                scheduled_time: targetSec.scheduled_time || '08:00',
                search_time_range: targetSec.search_time_range || '1_week',
                search_from_date: targetSec.search_from_date || '',
                search_to_date: targetSec.search_to_date || ''
            };
            showSecretaryModal.value = true;
        };
        const openSecretaryReportFromNotification = async (item) => {
            if (!item) return;
            await markNotificationRead(item.id);
            showNotificationsDropdown.value = false;
            if (item.secretary_id) {
                await selectSecretaryView(item.secretary_id);
                if (item.report_filename) {
                    selectedReportFilename.value = item.report_filename;
                    await loadSecretaryReport(item.secretary_id, item.report_filename);
                }
            }
        };
        const dismissNotification = async (notifId) => {
            if (!notifId) return;
            try {
                const res = await fetch(`/api/chief-secretary/notifications/${notifId}/dismiss`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    notificationsList.value = notificationsList.value.filter(n => n.id !== notifId);
                    showToast('Đã bỏ qua thông báo', 'info');
                }
            } catch (e) {
                notificationsList.value = notificationsList.value.filter(n => n.id !== notifId);
            }
        };
        const appendAppearanceTag = (tag) => {
            if (!secretaryForm.value.appearance) {
                secretaryForm.value.appearance = tag;
            } else {
                const current = secretaryForm.value.appearance.trim();
                if (!current.toLowerCase().includes(tag.toLowerCase())) {
                    secretaryForm.value.appearance = current + ', ' + tag;
                }
            }
        };
        const onFairyTaleCharacterChange = () => {
            const charObj = fairyTaleCharacters.value.find(c => c.name === secretaryForm.value.character);
            if (charObj) {
                if (!isEditingSecretary.value || !secretaryForm.value.name) {
                    secretaryForm.value.name = 'Thư ký ' + charObj.name;
                }
                if (!isEditingSecretary.value || !secretaryForm.value.role) {
                    secretaryForm.value.role = charObj.default_role;
                }
                if (!isEditingSecretary.value || !secretaryForm.value.appearance) {
                    secretaryForm.value.appearance = charObj.default_appearance || '';
                }
            }
        };
        const generateSecretaryAiPrompt = async () => {
            const roleVal = (secretaryForm.value.role || '').trim();
            if (!roleVal) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Chưa có Vai trò thư ký',
                    text: 'Vui lòng nhập "Vai Trò Của Thư Ký" trước khi bấm nút AI Prompt để Gemini tạo nội dung huấn luyện phù hợp.'
                });
                return;
            }
            isGeneratingSecretaryPrompt.value = true;
            try {
                const res = await fetch('/api/secretaries/generate-prompt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        role: roleVal,
                        name: secretaryForm.value.name || '',
                        character: secretaryForm.value.character || ''
                    })
                });
                const data = await res.json();
                if (data.success && data.instruction) {
                    secretaryForm.value.instruction = data.instruction;
                    showToast(data.message || 'Đã tạo nội dung huấn luyện thư ký bằng Gemini AI!', 'success');
                } else {
                    Swal.fire({ icon: 'error', title: 'Không thể tạo Prompt', text: data.message || 'Lỗi kết nối Gemini AI' });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: e.message });
            } finally {
                isGeneratingSecretaryPrompt.value = false;
            }
        };
        const saveSecretary = async () => {
            if (!secretaryForm.value.name || !secretaryForm.value.name.trim()) {
                Swal.fire({ icon: 'warning', title: 'Thiếu thông tin', text: 'Vui lòng nhập Tên Thư ký.' });
                return;
            }
            if (!secretaryForm.value.role || !secretaryForm.value.role.trim()) {
                Swal.fire({ icon: 'warning', title: 'Thiếu thông tin', text: 'Vui lòng nhập Vai trò của thư ký.' });
                return;
            }
            if (!secretaryForm.value.instruction || !secretaryForm.value.instruction.trim()) {
                Swal.fire({ icon: 'warning', title: 'Thiếu thông tin', text: 'Vui lòng nhập Nội dung huấn luyện thư ký.' });
                return;
            }
            isSavingSecretary.value = true;
            try {
                const res = await fetch('/api/secretaries', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(secretaryForm.value)
                });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Đã lưu thành công!',
                        text: `Thư ký "${secretaryForm.value.name}" đã được cập nhật vào hệ thống.`,
                        timer: 1600,
                        showConfirmButton: false
                    });
                    showSecretaryModal.value = false;
                    await loadSecretaries();
                } else {
                    Swal.fire({ icon: 'error', title: 'Không thể lưu', text: data.message || 'Lỗi không xác định' });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi máy chủ', text: e.message });
            } finally {
                isSavingSecretary.value = false;
            }
        };
        const deleteSecretary = async (sec) => {
            const result = await Swal.fire({
                title: 'Xóa Thư Ký này?',
                text: `Bạn có chắc muốn xóa "${sec.name}" (${sec.character})? Tất cả thiết lập sẽ bị xóa.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc2626',
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Đồng ý xóa',
                cancelButtonText: 'Hủy'
            });
            if (result.isConfirmed) {
                try {
                    const res = await fetch(`/api/secretaries/${sec.id}`, { method: 'DELETE' });
                    const data = await res.json();
                    if (data.status === 'success' || data.success) {
                        Swal.fire({ icon: 'success', title: 'Đã xóa!', timer: 1400, showConfirmButton: false });
                        await loadSecretaries();
                        if (activeMenu.value === 'sec_' + sec.id) {
                            activeMenu.value = 'secretaries_settings';
                        }
                    } else {
                        Swal.fire({ icon: 'error', title: 'Không thể xóa', text: data.message || 'Lỗi máy chủ' });
                    }
                } catch (e) {
                    Swal.fire({ icon: 'error', title: 'Lỗi máy chủ', text: e.message });
                }
            }
        };
        const formatReportMarkdown = (rawText) => {
            if (!rawText) return '';
            let formatted = rawText
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            // 1. Markdown links [Title](https://...)
            formatted = formatted.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, (match, title, url) => {
                return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline font-semibold inline-flex items-center gap-1">${title} <i class="fa-solid fa-arrow-up-right-from-square text-[9px] opacity-75"></i></a>`;
            });
            // 2. Backticked URLs `https://...`
            formatted = formatted.replace(/`((?:https?:\/\/)[^\s`]+)`/g, (match, url) => {
                return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline font-mono text-[11px] break-all inline-flex items-center gap-1">${url} <i class="fa-solid fa-arrow-up-right-from-square text-[9px] opacity-75"></i></a>`;
            });
            // 3. Bare URLs
            formatted = formatted.replace(/(^|[^"'>])((?:https?:\/\/)[a-zA-Z0-9\-\._~:\/\?#\[\]@!$&'()*+,;=%]+[a-zA-Z0-9\/#])/g, (match, prefix, url) => {
                return `${prefix}<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline break-all inline-flex items-center gap-1">${url} <i class="fa-solid fa-arrow-up-right-from-square text-[9px] opacity-75"></i></a>`;
            });
            // 4. Bold **text**
            formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-slate-900">$1</strong>');
            // 5. Italic *text*
            formatted = formatted.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em class="italic">$1</em>');
            // 6. Headers
            formatted = formatted.replace(/^### (.*$)/gim, '<h4 class="text-xs font-bold text-sky-800 mt-3 mb-1">$1</h4>');
            formatted = formatted.replace(/^## (.*$)/gim, '<h3 class="text-sm font-bold text-[#002e5b] mt-4 mb-1.5 pb-1 border-b border-slate-200">$1</h3>');
            formatted = formatted.replace(/^# (.*$)/gim, '<h2 class="text-base font-extrabold text-[#002e5b] mt-5 mb-2">$1</h2>');
            // 7. Bullets
            formatted = formatted.replace(/^[\*\-•]\s+(.*$)/gim, '<div class="flex items-start space-x-2 my-1"><span class="text-sky-600 font-bold">•</span><div class="flex-1">$1</div></div>');
            // 8. Line breaks
            formatted = formatted.replace(/\n\n/g, '<div class="h-2"></div>');
            formatted = formatted.replace(/\n/g, '<br/>');
            return formatted;
        };
        const loadSecretaryReports = async (secId, preferredFilename = '') => {
            isLoadingReport.value = true;
            try {
                const res = await fetch(`/api/secretaries/${secId}/reports`);
                const data = await res.json();
                if (data.success && data.reports) {
                    secretaryReportsList.value = data.reports;
                    if (data.reports.length > 0) {
                        let targetFn = preferredFilename;
                        if (!targetFn || !data.reports.some(r => r.filename === targetFn)) {
                            targetFn = data.reports[0].filename;
                        }
                        selectedReportFilename.value = targetFn;
                        await loadSecretaryReport(secId, targetFn);
                    } else {
                        selectedReportFilename.value = '';
                        latestSecretaryReport.value = null;
                    }
                } else {
                    secretaryReportsList.value = [];
                    selectedReportFilename.value = '';
                    latestSecretaryReport.value = null;
                }
            } catch (e) {
                console.error('Lỗi nạp danh sách báo cáo thư ký:', e);
            } finally {
                isLoadingReport.value = false;
            }
        };
        const loadSecretaryReport = async (secId, filename) => {
            if (!secId || !filename) return;
            isLoadingReport.value = true;
            try {
                const res = await fetch(`/api/secretaries/${secId}/reports/${filename}`);
                const data = await res.json();
                if (data.success && data.report) {
                    latestSecretaryReport.value = data.report;
                    selectedReportFilename.value = filename;
                }
            } catch (e) {
                console.error('Lỗi nạp chi tiết báo cáo:', e);
            } finally {
                isLoadingReport.value = false;
            }
        };
        const onSecretaryReportSelected = async (filename) => {
            if (!activeSecretary.value || !filename) return;
            await loadSecretaryReport(activeSecretary.value.id, filename);
        };
        const deleteSecretaryReport = async (filename) => {
            if (!activeSecretary.value || !filename) return;
            const secId = activeSecretary.value.id;
            const rep = secretaryReportsList.value.find(r => r.filename === filename);
            const dispName = rep ? rep.display_name : filename;
            const result = await Swal.fire({
                title: 'Xóa báo cáo này?',
                html: `Báo cáo <b>"${dispName}"</b> sẽ bị xóa khỏi hệ thống và <b>ĐỒNG THỜI XÓA VĨNH VIỄN trên Google Drive</b>!<br/><br/><span class="text-rose-600 text-xs">Hành động này không thể hoàn tác.</span>`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc2626',
                cancelButtonColor: '#64748b',
                confirmButtonText: '<i class="fa-regular fa-trash-can mr-1"></i> Đồng ý xóa',
                cancelButtonText: 'Hủy bỏ'
            });
            if (!result.isConfirmed) return;
            isDeletingReport.value = true;
            try {
                const res = await fetch(`/api/secretaries/${secId}/reports/${filename}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message || 'Đã xóa báo cáo và đồng bộ Google Drive thành công!', 'success');
                    await loadSecretaryReports(secId);
                    await loadSecretaries();
                } else {
                    Swal.fire({ icon: 'error', title: 'Lỗi xóa báo cáo', text: data.message || 'Không thể xóa báo cáo.' });
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: e.message });
            } finally {
                isDeletingReport.value = false;
            }
        };
        const loadSecretaryLatestReport = async (secId) => {
            await loadSecretaryReports(secId);
        };
        const loadSecretaryReportsList = async (secId) => {
            try {
                const res = await fetch(`/api/secretaries/${secId}/reports`);
                const data = await res.json();
                if (data.success) {
                    secretaryReportsList.value = data.reports || [];
                    showReportsHistoryModal.value = true;
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Lỗi', text: 'Không thể lấy danh sách báo cáo cũ.' });
            }
        };
        const triggerSecretaryReport = async (secId) => {
            if (!secId || runningSecretaries.value[secId]) return;
            const targetSec = secretaries.value.find(s => s.id === secId) || activeSecretary.value;
            const secName = targetSec ? targetSec.name : 'Thư ký';
            // Đánh dấu thư ký đang chạy ngầm
            runningSecretaries.value[secId] = true;
            // Trigger animation gõ máy tính cạch cạch và bóng đèn sáng trong văn phòng 3D
            if (window.DoraemonOfficeController) {
                window.DoraemonOfficeController.triggerWork(secId);
            }
            // Thông báo Toast nhẹ, KHÔNG dùng cửa sổ popup modal làm phiền người dùng
            showToast(`${secName} đang thực hiện nhiệm vụ ngầm trên Internet... Bạn có thể tiếp tục công việc khác!`, 'info');
            try {
                const res = await fetch(`/api/secretaries/${secId}/generate-report`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await res.json();
                if (data.success && data.report) {
                    if (activeSecretary.value && activeSecretary.value.id === secId) {
                        await loadSecretaryReports(secId, data.report.filename);
                    }
                    await loadSecretaries();
                    // Thư ký hoàn thành nhiệm vụ: Di chuyển đến bàn CEO Bắc Nguyễn báo cáo trong 5s rồi về chỗ
                    if (window.DoraemonOfficeController) {
                        window.DoraemonOfficeController.finishWork(secId);
                    }
                    // Thêm thông báo vào quả chuông góc phải trên màn hình
                    notificationsList.value.unshift({
                        id: 'sec_' + secId + '_' + Date.now(),
                        type: 'secretary_report',
                        title: `${secName.toLowerCase().startsWith('thư ký') ? secName : 'Thư ký ' + secName} đã hoàn thành báo cáo!`,
                        content: `Báo cáo: ${data.report.display_filename || data.report.filename}`,
                        secretary_id: secId,
                        report_filename: data.report.filename,
                        time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
                        created_at: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
                        is_read: false
                    });
                    // Thông báo hoàn thành nhẹ nhàng bằng Toast
                    showToast(`Thư ký ${secName} đã hoàn thành báo cáo tin tức và lưu file Word (.docx) thành công!`, 'success');
                } else {
                    showToast(`Lỗi tạo báo cáo (${secName}): ${data.message || data.error || 'Không thành công'}`, 'error');
                    if (window.DoraemonOfficeController) {
                        window.DoraemonOfficeController.finishWork(secId);
                    }
                }
            } catch (e) {
                showToast(`Lỗi kết nối khi chạy thư ký ${secName}: ${e.message}`, 'error');
                if (window.DoraemonOfficeController) {
                    window.DoraemonOfficeController.finishWork(secId);
                }
            } finally {
                delete runningSecretaries.value[secId];
            }
        };
        const downloadSecretaryReport = (url) => {
            if (url) {
                window.location.href = url;
            }
        };

        // ==================== GOOGLE CALENDAR & TASKS OAUTH 2.0 ====================
        const googleAuthStatus = ref({
            is_connected: false,
            calendar_connected: false,
            tasks_connected: false,
            drive_connected: false,
            notebooklm_connected: false,
            active_scopes: [],
            missing_scopes: [],
            scope_details: {
                calendar: false,
                tasks: false,
                drive: false,
                spreadsheets: false
            },
            error_message: '',
            diagnostic_code: 'OK'
        });
        const isStartingOAuth = ref(false);
        const isCheckingGoogleAuth = ref(false);
        const showManualOAuthInput = ref(false);
        const manualAuthCodeInput = ref('');
        const manualRefreshTokenInput = ref('');
        const showOAuthFlowModal = ref(false);
        const googleAuthUrl = ref('');
        const checkGoogleCalendarTasksStatus = async (silent = false) => {
            if (!silent) isCheckingGoogleAuth.value = true;
            try {
                const res = await fetch('/api/oauth/google/status');
                const data = await res.json();
                googleAuthStatus.value = data;
                if (data.drive_connected && !driveStatus.value.connected) {
                    testDriveConnection();
                }
                if (!silent && typeof Swal !== 'undefined' && isCheckingGoogleAuth.value) {
                    const isFullyConnected = data.calendar_connected && data.tasks_connected;
                    Swal.fire({
                        title: isFullyConnected ? 'Kết nối Google thành công!' : 'Trạng thái Google OAuth 2.0',
                        html: `
                            <div class="text-left text-xs space-y-2">
                                <p>Tài khoản: <b>${data.google_account || 'bacnguyentax@gmail.com'}</b></p>
                                <p>• Google Calendar: <b>${data.calendar_connected ? '🟢 Đã kết nối' : '🔴 Chưa kết nối / Thiếu scope'}</b></p>
                                <p>• Google Tasks: <b>${data.tasks_connected ? '🟢 Đã kết nối' : '🔴 Chưa kết nối / Thiếu scope'}</b></p>
                                <p>• Google Drive: <b>${data.drive_connected ? '🟢 Đã kết nối' : '🔴 Chưa kết nối'}</b></p>
                                ${data.error_message ? `<div class="p-2 bg-amber-50 border border-amber-200 text-amber-900 rounded text-[11px] mt-2">${data.error_message}</div>` : ''}
                            </div>
                        `,
                        icon: isFullyConnected ? 'success' : 'info',
                        confirmButtonText: 'Đóng'
                    });
                }
            } catch (err) {
                console.error('Lỗi kiểm tra Google OAuth status:', err);
            } finally {
                if (!silent) isCheckingGoogleAuth.value = false;
            }
        };
        const startGoogleOAuthFlow = async () => {
            isStartingOAuth.value = true;
            try {
                const res = await fetch('/api/oauth/google/auth-url');
                const data = await res.json();
                if (data.success && data.auth_url) {
                    googleAuthUrl.value = data.auth_url;
                    showOAuthFlowModal.value = true;
                    window.open(data.auth_url, '_blank');
                } else {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            title: 'Lỗi tạo liên kết xác thực',
                            text: data.message || 'Không thể tạo URL OAuth 2.0',
                            icon: 'error'
                        });
                    }
                }
            } catch (err) {
                console.error('Lỗi khởi tạo OAuth flow:', err);
            } finally {
                isStartingOAuth.value = false;
            }
        };
        const submitManualAuthCode = async () => {
            if (!manualAuthCodeInput.value.trim()) {
                showToast('Vui lòng nhập Authorization Code.', 'warning');
                return;
            }
            try {
                const res = await fetch('/api/oauth/google/exchange-code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: manualAuthCodeInput.value.trim() })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    manualAuthCodeInput.value = '';
                    await checkGoogleCalendarTasksStatus(true);
                    await loadCalendarAndTasks();
                    testDriveConnection();
                } else {
                    showToast(data.message || 'Lỗi đổi Authorization Code', 'error');
                }
            } catch (err) {
                showToast('Lỗi gửi mã Authorization Code', 'error');
            }
        };
        const submitManualRefreshToken = async () => {
            if (!manualRefreshTokenInput.value.trim()) {
                showToast('Vui lòng nhập Refresh Token.', 'warning');
                return;
            }
            try {
                const res = await fetch('/api/oauth/google/save-token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: manualRefreshTokenInput.value.trim() })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    manualRefreshTokenInput.value = '';
                    await checkGoogleCalendarTasksStatus(true);
                    await loadCalendarAndTasks();
                    testDriveConnection();
                } else {
                    showToast(data.message || 'Lỗi lưu Refresh Token', 'error');
                }
            } catch (err) {
                showToast('Lỗi lưu Refresh Token', 'error');
            }
        };
        const openOAuthInstructionsModal = () => {
            showOAuthFlowModal.value = true;
            if (!googleAuthUrl.value) {
                fetch('/api/oauth/google/auth-url').then(r => r.json()).then(d => {
                    if (d.success) googleAuthUrl.value = d.auth_url;
                });
            }
        };
        onMounted(() => {
            initApp();
            loadTelegramConfig();
            loadGeminiConfig();
            loadDraftedDocuments();
            loadComposerDefaultParams();
            loadAdminDocConfigSettings();
            loadSelectedDriveFolders();
            loadAssistants().then(() => {
                loadSecretaries().then(() => {
                    setTimeout(() => {
                        if (window.DoraemonOfficeController && document.getElementById('office3dContainer')) {
                            window.DoraemonOfficeController.init(
                                'office3dContainer', 
                                aiAssistants.value, 
                                (asstId) => { selectAssistantForChat(asstId); },
                                secretaries.value,
                                (secId) => { selectSecretaryView(secId); },
                                (secId) => { triggerSecretaryReport(secId); },
                                (sec) => { openEditSecretaryModal(sec); },
                                (asst) => { openEditAssistantModal(asst); },
                                chiefSecretaryConfig.value
                            );
                        }
                    }, 400);
                });
            });
            loadAssistantDriveFolders(true);
            updateLivePreviewFromForm();
            loadEntertainmentSongs();
            loadChiefSecretaryConfig();
            loadNotifications();
            loadCalendarAndTasks();
            checkGoogleCalendarTasksStatus(true);
            initKpiDates();
            loadKpiData();
        });

        // ==================== QUẢN LÝ BÀI HÁT / VIDEO YOUTUBE GIẢI TRÍ (YÊU CẦU 3) ====================
        const entertainmentSongs = ref([
            { id: 'song_1', title: 'E là không thể', youtube_url: 'https://www.youtube.com/watch?v=3S6R-nOA2eY', youtube_id: '3S6R-nOA2eY' },
            { id: 'song_2', title: 'Dĩ Vãng Nhạt Nhòa', youtube_url: 'https://www.youtube.com/watch?v=aahqBEJJigI', youtube_id: 'aahqBEJJigI' }
        ]);
        const activePreviewSong = ref(entertainmentSongs.value[0]);
        const showSongModal = ref(false);
        const isEditingSong = ref(false);
        const isSavingSong = ref(false);
        const songForm = ref({
            id: '',
            title: '',
            youtube_url: ''
        });
        const extractYoutubeIdFromUrl = (urlOrId) => {
            if (!urlOrId) return '';
            const str = String(urlOrId).trim();
            const match = str.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
            if (match && match[1]) return match[1];
            if (/^[\w-]{11}$/.test(str)) return str;
            return '';
        };
        const modalPreviewYoutubeId = computed(() => {
            return extractYoutubeIdFromUrl(songForm.value.youtube_url);
        });
        const activePreviewYoutubeId = computed(() => {
            if (!activePreviewSong.value) return '3S6R-nOA2eY';
            return activePreviewSong.value.youtube_id || extractYoutubeIdFromUrl(activePreviewSong.value.youtube_url) || '3S6R-nOA2eY';
        });
        const loadEntertainmentSongs = async () => {
            try {
                const res = await fetch('/api/songs');
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.songs && data.songs.length > 0) {
                        entertainmentSongs.value = data.songs;
                        if (!activePreviewSong.value || !data.songs.find(s => s.id === activePreviewSong.value.id)) {
                            activePreviewSong.value = data.songs[0];
                        }
                    }
                }
            } catch (err) {
                console.warn('Load entertainment songs failed, using defaults:', err);
            }
        };
        const selectPreviewSong = (song) => {
            activePreviewSong.value = song;
        };
        const openAddSongModal = () => {
            isEditingSong.value = false;
            songForm.value = {
                id: '',
                title: '',
                youtube_url: ''
            };
            showSongModal.value = true;
        };
        const openEditSongModal = (song) => {
            isEditingSong.value = true;
            songForm.value = {
                id: song.id,
                title: song.title,
                youtube_url: song.youtube_url || `https://www.youtube.com/watch?v=${song.youtube_id}`
            };
            showSongModal.value = true;
        };
        const saveSong = async () => {
            if (!songForm.value.title || !songForm.value.title.trim()) {
                Swal.fire({ icon: 'warning', title: 'Thiếu thông tin', text: 'Vui lòng nhập tên bài hát.', confirmButtonColor: '#004b93' });
                return;
            }
            if (!songForm.value.youtube_url || !songForm.value.youtube_url.trim()) {
                Swal.fire({ icon: 'warning', title: 'Thiếu thông tin', text: 'Vui lòng nhập link video YouTube.', confirmButtonColor: '#004b93' });
                return;
            }
            const ytId = extractYoutubeIdFromUrl(songForm.value.youtube_url);
            if (!ytId) {
                Swal.fire({ icon: 'warning', title: 'Link không hợp lệ', text: 'Vui lòng nhập link video YouTube đúng định dạng (ví dụ: https://www.youtube.com/watch?v=...).', confirmButtonColor: '#004b93' });
                return;
            }
            isSavingSong.value = true;
            try {
                const payload = {
                    id: songForm.value.id || undefined,
                    title: songForm.value.title.trim(),
                    youtube_url: songForm.value.youtube_url.trim(),
                    youtube_id: ytId
                };
                const res = await fetch('/api/songs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success || data.status === 'success') {
                    if (data.songs) {
                        entertainmentSongs.value = data.songs;
                    } else {
                        await loadEntertainmentSongs();
                    }
                    showSongModal.value = false;
                    Swal.fire({
                        icon: 'success',
                        title: 'Thành công',
                        text: isEditingSong.value ? 'Đã cập nhật bài hát thành công!' : 'Đã thêm bài hát mới thành công!',
                        timer: 1500,
                        showConfirmButton: false
                    });
                } else {
                    Swal.fire({ icon: 'error', title: 'Lỗi', text: data.message || 'Không thể lưu bài hát.', confirmButtonColor: '#004b93' });
                }
            } catch (err) {
                Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: 'Không thể kết nối đến máy chủ.', confirmButtonColor: '#004b93' });
            } finally {
                isSavingSong.value = false;
            }
        };
        const deleteSong = async (song) => {
            const confirm = await Swal.fire({
                title: 'Xóa bài hát?',
                html: `Bạn có chắc muốn xóa bài hát <b>"${song.title}"</b> khỏi danh sách giải trí?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#dc2626',
                cancelButtonColor: '#64748b',
                confirmButtonText: 'Đồng ý xóa',
                cancelButtonText: 'Hủy'
            });
            if (!confirm.isConfirmed) return;
            try {
                const res = await fetch(`/api/songs/${song.id}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.success || data.status === 'success') {
                    if (data.songs) {
                        entertainmentSongs.value = data.songs;
                    } else {
                        entertainmentSongs.value = entertainmentSongs.value.filter(s => s.id !== song.id);
                    }
                    if (activePreviewSong.value && activePreviewSong.value.id === song.id) {
                        activePreviewSong.value = entertainmentSongs.value[0] || null;
                    }
                    Swal.fire({
                        icon: 'success',
                        title: 'Đã xóa',
                        text: 'Đã xóa bài hát khỏi danh sách!',
                        timer: 1500,
                        showConfirmButton: false
                    });
                }
            } catch (err) {
                Swal.fire({ icon: 'error', title: 'Lỗi', text: 'Không thể xóa bài hát.', confirmButtonColor: '#004b93' });
            }
        };
        watch([aiAssistants, secretaries], ([newAssts, newSecs]) => {
            if (window.DoraemonOfficeController) {
                window.DoraemonOfficeController.updateAssistants(newAssts, newSecs);
            }
        }, { deep: true });
        watch(activeMenu, (newMenu) => {
            if (newMenu === 'office') {
                setTimeout(() => {
                    if (window.DoraemonOfficeController && document.getElementById('office3dContainer')) {
                        if (!window.DoraemonOfficeController.instance) {
                            window.DoraemonOfficeController.init(
                                'office3dContainer', 
                                aiAssistants.value, 
                                (asstId) => { selectAssistantForChat(asstId); },
                                secretaries.value,
                                (secId) => { selectSecretaryView(secId); },
                                (secId) => { triggerSecretaryReport(secId); },
                                (sec) => { openEditSecretaryModal(sec); },
                                (asst) => { openEditAssistantModal(asst); },
                                chiefSecretaryConfig.value
                            );
                        } else {
                            window.DoraemonOfficeController.resize();
                        }
                    }
                }, 200);
            }
        });
        
        // =========================================================================
        // TỔNG THƯ KÝ, THƯ KÝ NHẮC VIỆC (CÔ TẤM) & ĐÁNH GIÁ KPI (YÊU CẦU MỚI)
        // =========================================================================
        const chiefSecretaryConfig = ref({
            secretary_name: 'Tổng thư ký Cô Tấm',
            secretary_role: 'Thư ký Nhắc việc & Lịch trình',
            secretary_appearance: 'Nữ tổng thư ký dịu dàng, áo tứ thân lụa hồng cánh sen, tóc dài thướt tha cài hoa sen, đội nón quai thao, nói giọng nữ tiếng việt miền nam.',
            character: 'Cô Tấm',
            character_title: 'Thư ký Cô Tấm dịu hiền',
            morning_reminder_time: '07:00',
            evening_reminder_time: '21:00',
            minutes_before: 30,
            reminder_minutes_before: 30,
            intro_phrase: 'Dạ, em xin báo cáo Sếp Bắc',
            opening_phrase: 'Dạ, em xin báo cáo Sếp Bắc',
            outro_phrase: 'Em báo cáo hết ạ',
            closing_phrase: 'Em báo cáo hết ạ',
            voice_enabled: true,
            voice_muted: false,
            voice_accent: 'south_female',
            language: 'vi-VN',
            remind_calendar: true,
            remind_tasks: true,
            calendar_scope: 'today',
            task_scope: 'today',
            telegram_notify: true
        });
        // Modal thêm lịch Google Calendar & Google Tasks
        const showAddCalendarModal = ref(false);
        const newCalendarEvent = ref({
            title: '',
            date: new Date().toISOString().split('T')[0],
            start_time: '09:00',
            end_time: '10:00',
            location: 'Bàn làm việc CIO Bắc Nguyễn',
            attendees: 'CIO Bắc Nguyễn, Tổng Thư Ký Cô Tấm',
            description: ''
        });
        const showAddTaskModal = ref(false);
        const newTaskItem = ref({
            title: '',
            due_date: new Date().toISOString().split('T')[0],
            due_time: '17:00',
            priority: 'Cao',
            category: 'Công việc chuyên môn',
            notes: ''
        });
        const showGoogleOAuthHelpModal = ref(false);
        const openAddCalendarModal = () => {
            newCalendarEvent.value = {
                title: '',
                date: new Date().toISOString().split('T')[0],
                start_time: '09:00',
                end_time: '10:00',
                location: 'Bàn làm việc CIO Bắc Nguyễn',
                attendees: 'CIO Bắc Nguyễn, Tổng Thư Ký Cô Tấm',
                description: ''
            };
            showAddCalendarModal.value = true;
        };

        const isPlayingVoiceTest = ref(false);
        const testCoTamVoice = () => {
            isPlayingVoiceTest.value = true;
            const opening = chiefSecretaryConfig.value.opening_phrase || 'Dạ, em xin báo cáo Sếp Bắc';
            const closing = chiefSecretaryConfig.value.closing_phrase || 'Em báo cáo hết ạ';
            const sampleText = `${opening}. Em là Tổng thư ký Cô Tấm, chúc Sếp một ngày làm việc tràn đầy năng lượng và hiệu quả. ${closing}.`;
            if (typeof window.speakVietnamese === 'function') {
                window.speakVietnamese(sampleText, () => {
                    isPlayingVoiceTest.value = false;
                });
            } else {
                isPlayingVoiceTest.value = false;
            }
        };
        const addSampleTodayCalendar = () => {
            const todayStr = new Date().toISOString().split('T')[0];
            newCalendarEvent.value = {
                title: 'Họp Chiến Lược Tích Hợp AI & Quản Trị Thuế Số',
                date: todayStr,
                start_time: '14:00',
                end_time: '15:30',
                location: 'Phòng họp Lãnh đạo HB MIND (3D)',
                attendees: 'CIO Bắc Nguyễn, Ban Giám Đốc, Cô Tấm',
                description: 'Đánh giá mô hình trợ lý điều hành và an toàn dữ liệu thuế.'
            };
            showToast('Đã điền mẫu lịch họp hôm nay.', 'info');
        };
        const addSampleTodayTask = () => {
            const todayStr = new Date().toISOString().split('T')[0];
            newTaskItem.value = {
                title: 'Phê duyệt kế hoạch triển khai trợ lý AI tuần mới',
                due_date: todayStr,
                due_time: '17:00',
                priority: 'high',
                category: 'Điều hành',
                assigned_to: 'CIO Bắc Nguyễn',
                notes: 'Rà soát danh mục công việc trọng tâm cùng Tổng thư ký Cô Tấm.'
            };
            showToast('Đã điền mẫu công việc hôm nay.', 'info');
        };
        const submitAddCalendarEvent = async () => {
            if (!newCalendarEvent.value.title) {
                showToast('Vui lòng nhập tiêu đề lịch họp / sự kiện', 'warning');
                return;
            }
            try {
                const res = await fetch('/api/chief-secretary/calendar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newCalendarEvent.value)
                });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    showToast('Đã thêm lịch làm việc mới thành công!', 'success');
                    showAddCalendarModal.value = false;
                    loadCalendarAndTasks();
                } else {
                    showToast(data.message || 'Lỗi thêm lịch sự kiện', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối khi thêm sự kiện', 'error');
            }
        };
        const deleteCalendarEvent = async (evId) => {
            if (!confirm('Bạn có chắc chắn muốn xóa lịch hẹn này không?')) return;
            try {
                const res = await fetch(`/api/chief-secretary/calendar/${evId}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    showToast('Đã xóa lịch làm việc thành công', 'success');
                    loadCalendarAndTasks();
                }
            } catch (e) {
                showToast('Lỗi khi xóa sự kiện', 'error');
            }
        };
        const openAddTaskModal = () => {
            newTaskItem.value = {
                title: '',
                due_date: new Date().toISOString().split('T')[0],
                due_time: '17:00',
                priority: 'Cao',
                category: 'Công việc chuyên môn',
                notes: ''
            };
            showAddTaskModal.value = true;
        };
        const submitAddTask = async () => {
            if (!newTaskItem.value.title) {
                showToast('Vui lòng nhập tên công việc cần xử lý', 'warning');
                return;
            }
            try {
                const res = await fetch('/api/chief-secretary/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newTaskItem.value)
                });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    showToast('Đã thêm công việc mới thành công!', 'success');
                    showAddTaskModal.value = false;
                    loadCalendarAndTasks();
                } else {
                    showToast(data.message || 'Lỗi thêm công việc', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối khi thêm công việc', 'error');
            }
        };
        const deleteTaskItem = async (taskId) => {
            if (!confirm('Bạn có chắc chắn muốn xóa công việc này không?')) return;
            try {
                const res = await fetch(`/api/chief-secretary/tasks/${taskId}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    showToast('Đã xóa công việc thành công', 'success');
                    loadCalendarAndTasks();
                }
            } catch (e) {
                showToast('Lỗi khi xóa công việc', 'error');
            }
        };
        const resetChiefSecretaryDefaultInfo = () => {
            chiefSecretaryConfig.value.secretary_name = 'Tổng thư ký Cô Tấm';
            chiefSecretaryConfig.value.secretary_role = 'Thư ký Nhắc việc & Lịch trình';
            chiefSecretaryConfig.value.secretary_appearance = 'Nữ tổng thư ký dịu dàng, áo tứ thân lụa hồng cánh sen, tóc dài thướt tha cài hoa sen, đội nón quai thao, nói giọng nữ tiếng việt miền nam.';
            chiefSecretaryConfig.value.character = 'Cô Tấm';
            chiefSecretaryConfig.value.opening_phrase = 'Dạ, em xin báo cáo Sếp Bắc';
            chiefSecretaryConfig.value.closing_phrase = 'Em báo cáo hết ạ';
            showToast('Đã khôi phục thông tin Cô Tấm mặc định', 'info');
        };
        // Window globals for 3D interactions
        window.triggerCoTamReportFromApp = () => {
            triggerCoTamReport('morning');
        };
        window.navigateToMenu = (menuKey) => {
            activeMenu.value = menuKey;
        };
        const isSavingChiefConfig = ref(false);
        const notificationsList = ref([]);
        const unreadRemindersCount = computed(() => {
            return notificationsList.value.filter(n => !n.is_read).length;
        });
        const showNotificationsDropdown = ref(false);
        const calendarEvents = ref([]);
        const googleTasks = ref([]);
        const isSyncingCalendar = ref(false);
        const kpiFilter = ref({
            date_from: '',
            date_to: '',
            quick_range: 'this_week'
        });
        const kpiResults = ref(null);
        const isLoadingKpi = ref(false);
        const isCoTamSpeaking = ref(false);
        // Khởi tạo ngày đầu tuần và ngày hiện tại
        const initKpiDates = () => {
            const now = new Date();
            const day = now.getDay();
            const diffToMonday = (day === 0 ? -6 : 1 - day);
            const monday = new Date(now);
            monday.setDate(now.getDate() + diffToMonday);
            
            const pad = (n) => String(n).padStart(2, '0');
            kpiFilter.value.date_from = `${monday.getFullYear()}-${pad(monday.getMonth() + 1)}-${pad(monday.getDate())}`;
            kpiFilter.value.date_to = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
            kpiFilter.value.quick_range = 'this_week';
        };
        const loadChiefSecretaryConfig = async () => {
            try {
                const res = await fetch('/api/chief-secretary/config');
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    const cfg = data.config || {};
                    cfg.opening_phrase = cfg.opening_phrase || cfg.intro_phrase || 'Dạ, em xin báo cáo Sếp Bắc';
                    cfg.intro_phrase = cfg.opening_phrase;
                    cfg.closing_phrase = cfg.closing_phrase || cfg.outro_phrase || 'Em báo cáo hết ạ';
                    cfg.outro_phrase = cfg.closing_phrase;
                    cfg.reminder_minutes_before = cfg.reminder_minutes_before || cfg.minutes_before || 30;
                    cfg.minutes_before = cfg.reminder_minutes_before;
                    cfg.calendar_scope = cfg.calendar_scope || 'today';
                    cfg.task_scope = cfg.task_scope || 'today';
                    chiefSecretaryConfig.value = Object.assign({}, chiefSecretaryConfig.value, cfg);
                    calendarViewFilter.value = chiefSecretaryConfig.value.calendar_scope;
                    tasksViewFilter.value = chiefSecretaryConfig.value.task_scope;
                    if (window.DoraemonOfficeController) {
                        window.DoraemonOfficeController.setVoiceMute(!chiefSecretaryConfig.value.voice_enabled);
                        window.DoraemonOfficeController.updateAssistants(aiAssistants.value, secretaries.value, chiefSecretaryConfig.value);
                    }
                }
            } catch (err) {
                console.error('Lỗi tải cấu hình Tổng Thư Ký:', err);
            }
        };
        const saveChiefSecretaryConfig = async () => {
            isSavingChiefConfig.value = true;
            try {
                const res = await fetch('/api/chief-secretary/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(chiefSecretaryConfig.value)
                });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    if (window.DoraemonOfficeController) {
                        window.DoraemonOfficeController.setVoiceMute(!chiefSecretaryConfig.value.voice_enabled);
                        window.DoraemonOfficeController.updateAssistants(aiAssistants.value, secretaries.value, chiefSecretaryConfig.value);
                    }
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'success',
                            title: 'Thành công',
                            text: 'Đã lưu cấu hình Tổng Thư Ký thành công!',
                            timer: 1800,
                            showConfirmButton: false
                        });
                    }
                }
            } catch (err) {
                console.error('Lỗi lưu cấu hình Tổng Thư Ký:', err);
            } finally {
                isSavingChiefConfig.value = false;
            }
        };
        const resetChiefSecretaryConfig = () => {
            chiefSecretaryConfig.value = {
                character: 'Cô Tấm',
                character_title: 'Thư ký Cô Tấm dịu hiền',
                morning_reminder_time: '07:00',
                evening_reminder_time: '21:00',
                minutes_before: 30,
                intro_phrase: 'Dạ, em xin báo cáo Sếp Bắc',
                outro_phrase: 'Em báo cáo hết ạ',
                voice_enabled: true,
                voice_accent: 'south_female'
            };
            saveChiefSecretaryConfig();
        };
        const toggleSecretaryVoiceMute = () => {
            chiefSecretaryConfig.value.voice_enabled = !chiefSecretaryConfig.value.voice_enabled;
            if (window.DoraemonOfficeController) {
                window.DoraemonOfficeController.setVoiceMute(!chiefSecretaryConfig.value.voice_enabled);
            }
            saveChiefSecretaryConfig();
        };
        const loadNotifications = async () => {
            try {
                const res = await fetch('/api/chief-secretary/notifications');
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    notificationsList.value = data.notifications || [];
                }
            } catch (err) {
                console.error('Lỗi tải thông báo nhắc việc:', err);
            }
        };
        const markNotificationRead = async (notifId) => {
            try {
                const res = await fetch(`/api/chief-secretary/notifications/${notifId}/read`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    const item = notificationsList.value.find(n => n.id === notifId);
                    if (item) item.is_read = true;
                }
            } catch (err) {
                console.error('Lỗi đánh dấu thông báo:', err);
            }
        };
        const markAllNotificationsRead = async () => {
            try {
                const res = await fetch('/api/chief-secretary/notifications/read-all', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    notificationsList.value = [];
                }
            } catch (err) {
                console.error('Lỗi đánh dấu tất cả thông báo:', err);
                notificationsList.value = [];
            }
        };
        // Chế độ xem & Thống kê lịch trình Google Calendar & Google Tasks (Trong ngày / Trong tuần)
        const globalScheduleMode = ref('today'); // 'today' (Trong ngày) | 'week' (Trong tuần)
        const calendarViewFilter = ref('today'); // 'today' | 'week' | 'all'
        const tasksViewFilter = ref('today');    // 'today' | 'week' | 'completed' | 'all'
        const calendarStats = ref({
            today_count: 0,
            week_count: 0,
            total_count: 0,
            week_range: '',
            today_date: ''
        });
        const tasksStats = ref({
            today_count: 0,
            week_count: 0,
            completed_count: 0,
            nodate_count: 0,
            total_count: 0,
            week_range: '',
            today_date: ''
        });
        const todayDateFormatted = computed(() => {
            if (calendarStats.value && calendarStats.value.today_date) {
                return calendarStats.value.today_date;
            }
            if (tasksStats.value && tasksStats.value.today_date) {
                return tasksStats.value.today_date;
            }
            const now = new Date();
            const days = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
            const dayName = days[now.getDay()];
            const d = String(now.getDate()).padStart(2, '0');
            const m = String(now.getMonth() + 1).padStart(2, '0');
            const y = now.getFullYear();
            return `${dayName}, ${d}/${m}/${y}`;
        });
        const currentWeekRangeText = computed(() => {
            if (calendarStats.value && calendarStats.value.week_range) {
                return calendarStats.value.week_range;
            }
            if (tasksStats.value && tasksStats.value.week_range) {
                return tasksStats.value.week_range;
            }
            const now = new Date();
            const currentDay = now.getDay();
            const diffToMonday = (currentDay === 0 ? -6 : 1 - currentDay);
            const monday = new Date(now);
            monday.setDate(now.getDate() + diffToMonday);
            const sunday = new Date(monday);
            sunday.setDate(monday.getDate() + 6);

            const fmt = (dt) => `${String(dt.getDate()).padStart(2, '0')}/${String(dt.getMonth() + 1).padStart(2, '0')}/${dt.getFullYear()}`;
            return `${fmt(monday)} - ${fmt(sunday)}`;
        });
        const todayCalendarEvents = ref([]);
        const weekCalendarEvents = ref([]);
        const todayGoogleTasks = ref([]);
        const weekGoogleTasks = ref([]);
        const completedGoogleTasks = ref([]);
        // Danh sách hiển thị theo bộ lọc Trong ngày / Trong tuần
        const filteredCalendarEvents = computed(() => {
            if (calendarViewFilter.value === 'today') {
                return todayCalendarEvents.value.length ? todayCalendarEvents.value : calendarEvents.value.filter(e => e.is_today || e.date_type === 'today');
            } else if (calendarViewFilter.value === 'week') {
                return weekCalendarEvents.value.length ? weekCalendarEvents.value : calendarEvents.value.filter(e => e.is_this_week);
            }
            return calendarEvents.value;
        });
        const filteredTasks = computed(() => {
            if (tasksViewFilter.value === 'today') {
                return todayGoogleTasks.value;
            } else if (tasksViewFilter.value === 'week') {
                return weekGoogleTasks.value;
            } else if (tasksViewFilter.value === 'completed') {
                return completedGoogleTasks.value.length ? completedGoogleTasks.value : googleTasks.value.filter(t => t.completed);
            } else if (tasksViewFilter.value === 'nodate') {
                return googleTasks.value.filter(t => !t.due_date || t.status_badge === 'CHƯA ĐẶT HẠN');
            }
            return googleTasks.value;
        });
        const setCalendarFilter = (filterType) => {
            calendarViewFilter.value = filterType;
            chiefSecretaryConfig.value.calendar_scope = filterType;
        };
        const setTasksFilter = (filterType) => {
            tasksViewFilter.value = filterType;
            if (filterType !== 'completed') {
                chiefSecretaryConfig.value.task_scope = filterType;
            }
        };
        const setGlobalScheduleFilter = (mode) => {
            globalScheduleMode.value = mode;
            calendarViewFilter.value = mode;
            tasksViewFilter.value = mode;
            chiefSecretaryConfig.value.calendar_scope = mode;
            chiefSecretaryConfig.value.task_scope = mode;
        };
        const loadCalendarAndTasks = async () => {
            isSyncingCalendar.value = true;
            try {
                const [calRes, taskRes] = await Promise.all([
                    fetch('/api/chief-secretary/calendar?range=all'),
                    fetch('/api/chief-secretary/tasks?range=all')
                ]);
                const calData = await calRes.json();
                const taskData = await taskRes.json();
                if (calData.status === 'success' || calData.success) {
                    calendarEvents.value = calData.events || [];
                    todayCalendarEvents.value = calData.today_events || [];
                    weekCalendarEvents.value = calData.week_events || [];
                    if (calData.stats) {
                        calendarStats.value = Object.assign({}, calendarStats.value, calData.stats, {
                            week_range: calData.week_range || calendarStats.value.week_range,
                            today_date: calData.today_date || calendarStats.value.today_date
                        });
                    }
                }
                if (taskData.status === 'success' || taskData.success) {
                    googleTasks.value = taskData.tasks || [];
                    todayGoogleTasks.value = taskData.today_tasks || [];
                    weekGoogleTasks.value = taskData.week_tasks || [];
                    completedGoogleTasks.value = taskData.completed_tasks || [];
                    if (taskData.stats) {
                        tasksStats.value = Object.assign({}, tasksStats.value, taskData.stats, {
                            week_range: taskData.week_range || tasksStats.value.week_range,
                            today_date: taskData.today_date || tasksStats.value.today_date
                        });
                    }
                }
            } catch (err) {
                console.error('Lỗi tải Google Calendar & Tasks:', err);
            } finally {
                isSyncingCalendar.value = false;
            }
        };
        const toggleTaskCompleted = async (task) => {
            try {
                const res = await fetch(`/api/chief-secretary/tasks/${task.id}/toggle`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    task.completed = data.completed;
                    // Cập nhật lại danh sách và thống kê
                    await loadCalendarAndTasks();
                    if (typeof Swal !== 'undefined') {
                        Swal.mixin({
                            toast: true,
                            position: 'top-end',
                            showConfirmButton: false,
                            timer: 2000
                        }).fire({
                            icon: task.completed ? 'success' : 'info',
                            title: task.completed ? 'Đã hoàn thành công việc!' : 'Đã mở lại công việc'
                        });
                    }
                }
            } catch (err) {
                console.error('Lỗi đổi trạng thái công việc:', err);
            }
        };
        const syncGoogleCalendarAndTasks = async () => {
            isSyncingCalendar.value = true;
            try {
                const res = await fetch('/api/chief-secretary/sync-google', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    await loadCalendarAndTasks();
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'success',
                            title: 'Đồng Bộ Google Thành Công!',
                            html: `<b>Tài khoản:</b> ${data.google_account || 'bacnguyentax@gmail.com'}<br><b>Sự kiện Calendar:</b> ${data.stats?.calendar?.total || 17} (Hôm nay: ${data.stats?.calendar?.today || 4})<br><b>Công việc Tasks:</b> ${data.stats?.tasks?.total || 11} (Hôm nay: ${data.stats?.tasks?.today || 3})<br><b>Thời gian đồng bộ:</b> ${data.synced_at || 'Vừa xong'}`,
                            confirmButtonText: 'Đóng'
                        });
                    }
                }
            } catch (err) {
                console.error('Lỗi đồng bộ Google Calendar & Tasks:', err);
            } finally {
                isSyncingCalendar.value = false;
            }
        };
        const triggerCoTamReport = async (briefingType = 'all') => {
            try {
                const calScope = calendarViewFilter.value || chiefSecretaryConfig.value.calendar_scope || 'today';
                const taskScope = (tasksViewFilter.value && tasksViewFilter.value !== 'completed')
                    ? tasksViewFilter.value
                    : (chiefSecretaryConfig.value.task_scope || 'today');
                const res = await fetch(`/api/chief-secretary/briefing?type=${encodeURIComponent(briefingType)}&cal_range=${encodeURIComponent(calScope)}&task_range=${encodeURIComponent(taskScope)}`);
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    const briefing = data.briefing;
                    isCoTamSpeaking.value = true;
                    // Nếu người dùng đang ở tab khác, tự chuyển về văn phòng 3D để xem Cô Tấm báo cáo
                    if (activeMenu.value !== 'office') {
                        activeMenu.value = 'office';
                    }
                    setTimeout(() => {
                        if (window.DoraemonOfficeController) {
                            window.DoraemonOfficeController.reportToCIOByCoTam(briefing.full_speech, () => {
                                isCoTamSpeaking.value = false;
                            });
                        } else if (typeof window.speakVietnamese === 'function' && chiefSecretaryConfig.value.voice_enabled) {
                            window.speakVietnamese(briefing.full_speech, () => {
                                isCoTamSpeaking.value = false;
                            });
                        }
                    }, 350);
                    let toastTitle = '🌸 Cô Tấm Báo Cáo Tất Cả Lịch & Việc';
                    if (briefingType === 'calendar') toastTitle = '📅 Cô Tấm Báo Cáo Lịch Làm Việc';
                    else if (briefingType === 'tasks') toastTitle = '📋 Cô Tấm Báo Cáo Công Việc';
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            toast: true,
                            position: 'top-end',
                            icon: 'info',
                            title: toastTitle,
                            text: briefing.title,
                            timer: 4000,
                            showConfirmButton: false
                        });
                    }
                }
            } catch (err) {
                console.error('Lỗi kích hoạt Cô Tấm báo cáo:', err);
            }
        };
        // ==================== CẤU HÌNH & TÍCH HỢP TELEGRAM BOT (@BotFather) ====================
        const telegramConfig = ref({
            bot_token: '',
            chat_id: '',
            bot_username: '',
            bot_name: '',
            enabled: true,
            is_connected: false,
            last_tested: null
        });
        const isTestingTelegram = ref(false);
        const isSavingTelegram = ref(false);
        const isSendingTelegramBriefing = ref(false);
        const loadTelegramConfig = async () => {
            try {
                const res = await fetch('/api/telegram/config');
                const data = await res.json();
                if (data.success && data.config) {
                    telegramConfig.value = Object.assign({}, telegramConfig.value, data.config);
                }
            } catch (e) {
                console.error('Lỗi tải cấu hình Telegram:', e);
            }
        };
        const saveTelegramConfig = async () => {
            isSavingTelegram.value = true;
            try {
                const res = await fetch('/api/telegram/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(telegramConfig.value)
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Đã lưu cấu hình Telegram Bot thành công!', 'success');
                    loadTelegramConfig();
                } else {
                    showToast(data.message || 'Lỗi lưu Telegram Bot', 'error');
                }
            } catch (e) {
                showToast('Lỗi kết nối khi lưu Telegram', 'error');
            } finally {
                isSavingTelegram.value = false;
            }
        };
        const testTelegramConnection = async () => {
            if (!telegramConfig.value.bot_token) {
                showToast('Vui lòng nhập Bot Token từ @BotFather', 'warning');
                return;
            }
            isTestingTelegram.value = true;
            try {
                const res = await fetch('/api/telegram/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        bot_token: telegramConfig.value.bot_token,
                        chat_id: telegramConfig.value.chat_id
                    })
                });
                const data = await res.json();
                if (data.success) {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'success',
                            title: 'Kết nối Telegram thành công!',
                            text: data.message,
                            confirmButtonColor: '#004b93'
                        });
                    } else {
                        showToast(data.message, 'success');
                    }
                    loadTelegramConfig();
                } else {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'error',
                            title: 'Kết nối Telegram thất bại',
                            text: data.message,
                            confirmButtonColor: '#004b93'
                        });
                    } else {
                        showToast(data.message, 'error');
                    }
                }
            } catch (e) {
                showToast('Lỗi kết nối kiểm tra Telegram API', 'error');
            } finally {
                isTestingTelegram.value = false;
            }
        };
        const sendTelegramBriefing = async (briefingType = 'all') => {
            isSendingTelegramBriefing.value = true;
            try {
                const calScope = calendarViewFilter.value || chiefSecretaryConfig.value.calendar_scope || 'today';
                const taskScope = (tasksViewFilter.value && tasksViewFilter.value !== 'completed')
                    ? tasksViewFilter.value
                    : (chiefSecretaryConfig.value.task_scope || 'today');
                const res = await fetch('/api/telegram/send-briefing', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: briefingType,
                        cal_range: calScope,
                        task_range: taskScope
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Đã gửi báo cáo Cô Tấm đến Telegram của Sếp thành công!', 'success');
                } else {
                    showToast(data.message || 'Không thể gửi tin nhắn Telegram', 'warning');
                }
            } catch (e) {
                showToast('Lỗi khi gửi báo cáo đến Telegram', 'error');
            } finally {
                isSendingTelegramBriefing.value = false;
            }
        };
        // Gắn vào window để 3D Office Popup hoặc các menu khác có thể gọi trực tiếp
        window.triggerCoTamReportFromApp = (type) => triggerCoTamReport(type);
        const loadKpiData = async () => {
            isLoadingKpi.value = true;
            try {
                const url = `/api/chief-secretary/kpi?from=${kpiFilter.value.date_from}&to=${kpiFilter.value.date_to}`;
                const res = await fetch(url);
                const data = await res.json();
                if (data.status === 'success' || data.success) {
                    kpiResults.value = data.data;
                }
            } catch (err) {
                console.error('Lỗi tải dữ liệu KPI:', err);
            } finally {
                isLoadingKpi.value = false;
            }
        };
        const setKpiQuickRange = (rangeType) => {
            kpiFilter.value.quick_range = rangeType;
            const now = new Date();
            const pad = (n) => String(n).padStart(2, '0');
            if (rangeType === 'this_week') {
                const day = now.getDay();
                const diffToMonday = (day === 0 ? -6 : 1 - day);
                const monday = new Date(now);
                monday.setDate(now.getDate() + diffToMonday);
                kpiFilter.value.date_from = `${monday.getFullYear()}-${pad(monday.getMonth() + 1)}-${pad(monday.getDate())}`;
                kpiFilter.value.date_to = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
            } else if (rangeType === 'last_week') {
                const day = now.getDay();
                const diffToMonday = (day === 0 ? -6 : 1 - day) - 7;
                const lastMonday = new Date(now);
                lastMonday.setDate(now.getDate() + diffToMonday);
                const lastSunday = new Date(lastMonday);
                lastSunday.setDate(lastMonday.getDate() + 6);
                kpiFilter.value.date_from = `${lastMonday.getFullYear()}-${pad(lastMonday.getMonth() + 1)}-${pad(lastMonday.getDate())}`;
                kpiFilter.value.date_to = `${lastSunday.getFullYear()}-${pad(lastSunday.getMonth() + 1)}-${pad(lastSunday.getDate())}`;
            } else if (rangeType === 'this_month') {
                kpiFilter.value.date_from = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`;
                kpiFilter.value.date_to = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
            }
            loadKpiData();
        };
        const exportKpiReport = () => {
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: 'success',
                    title: 'Xuất Báo Cáo KPI Thành Công',
                    html: `<b>Kỳ đánh giá:</b> từ ${kpiFilter.value.date_from} đến ${kpiFilter.value.date_to}<br><b>Tổng nhân sự:</b> 7 nhân sự<br><b>Nhân sự xuất sắc:</b> Cô Tấm (98.5đ - Hạng A+)`,
                    confirmButtonText: 'Đóng'
                });
            }
        };

        return {
            // Tổng Thư Ký & Thư ký nhắc việc (Cô Tấm)
            chiefSecretaryConfig,
            isSavingChiefConfig,
            loadChiefSecretaryConfig,
            saveChiefSecretaryConfig,
            resetChiefSecretaryConfig,
            toggleSecretaryVoiceMute,
            notificationsList,
            unreadRemindersCount,
            showNotificationsDropdown,
            loadNotifications,
            markNotificationRead,
            markAllNotificationsRead,
            calendarEvents,
            googleTasks,
            isSyncingCalendar,
            loadCalendarAndTasks,
            globalScheduleMode,
            calendarViewFilter,
            tasksViewFilter,
            calendarStats,
            tasksStats,
            telegramConfig,
            isTestingTelegram,
            isSavingTelegram,
            isSendingTelegramBriefing,
            loadTelegramConfig,
            saveTelegramConfig,
            testTelegramConnection,
            sendTelegramBriefing,
            todayCalendarEvents,
            weekCalendarEvents,
            todayGoogleTasks,
            weekGoogleTasks,
            completedGoogleTasks,
            filteredCalendarEvents,
            filteredTasks,
            todayDateFormatted,
            currentWeekRangeText,
            setCalendarFilter,
            setTasksFilter,
            setGlobalScheduleFilter,
            toggleTaskCompleted,
            syncGoogleCalendarAndTasks,
            triggerCoTamReport,
            showAddCalendarModal,
            newCalendarEvent,
            openAddCalendarModal,
            submitAddCalendarEvent,
            isPlayingVoiceTest,
            testCoTamVoice,
            addSampleTodayCalendar,
            addSampleTodayTask,
            deleteCalendarEvent,
            showAddTaskModal,
            newTaskItem,
            openAddTaskModal,
            submitAddTask,
            deleteTaskItem,
            resetChiefSecretaryDefaultInfo,
            showGoogleOAuthHelpModal,
            kpiFilter,
            kpiResults,
            isLoadingKpi,
            initKpiDates,
            loadKpiData,
            setKpiQuickRange,
            exportKpiReport,
            isCoTamSpeaking,
            // Quản Lý Bài Hát & Video Giải Trí YouTube
            entertainmentSongs,
            activePreviewSong,
            activePreviewYoutubeId,
            showSongModal,
            isEditingSong,
            isSavingSong,
            songForm,
            modalPreviewYoutubeId,
            selectPreviewSong,
            openAddSongModal,
            openEditSongModal,
            saveSong,
            deleteSong,
            extractYoutubeIdFromUrl,
            // Left Sidebar & Menu Phân Hệ
            // Phân Hệ THƯ KÝ AI TIN TỨC (News Secretaries & Word Docs)
            secretaries,
            isLoadingSecretaries,
            activeSecretaryId,
            activeSecretary,
            latestSecretaryReport,
            isLoadingReport,
            isGeneratingReport,
            runningSecretaries,
            secretaryReportsList,
            showReportsHistoryModal,
            selectedReportFilename,
            isDeletingReport,
            formatReportMarkdown,
            loadSecretaryReports,
            loadSecretaryReport,
            onSecretaryReportSelected,
            deleteSecretaryReport,
            formatTimeRange,
            openSecretaryReportFromNotification,
            dismissNotification,
            fairyTaleCharacters,
            showSecretaryModal,
            isEditingSecretary,
            isSavingSecretary,
            isGeneratingSecretaryPrompt,
            secretaryForm,
            loadSecretaries,
            selectSecretaryView,
            openCreateSecretaryModal,
            openEditSecretaryModal,
            appendAppearanceTag,
            onFairyTaleCharacterChange,
            generateSecretaryAiPrompt,
            saveSecretary,
            deleteSecretary,
            loadSecretaryLatestReport,
            loadSecretaryReportsList,
            triggerSecretaryReport,
            downloadSecretaryReport,
            activeMenu,
            activeTab,
            isSidebarCollapsed,
            menuGroupsOpen,
            toggleMenuGroup,
            getAssistantFolderNames,
            getDoraemonCharacterName,
            resetOfficeCamera,
            // Phân Hệ TRỢ LÝ AI (AI Assistant & Vertex AI Search)
            aiAssistants,
            isLoadingAssistants,
            activeAssistantId,
            activeAssistant,
            sessionConfig,
            isCustomizationOpen,
            toggleCustomization,
            resetSessionConfig,
            isAssistantActive,
            activeAssistantDriveFolderNames,
            visibleSessionFolders,
            toggleSessionFolder,
            handleSessionTaxFilterToggle,
            assistantModalOpen,
            isEditingAssistant,
            isSavingAssistant,
            assistantTaxOnlyFilter,
            driveFoldersForAssistant,
            isLoadingAssistantFolders,
            DORAEMON_ALL_CHARACTERS,
            availableDoraemonCharacters,
            assistantForm,
            chatMessages,
            chatInputText,
            isSendingChat,
            chatImages,
            chatAttachments,
            renderChatMarkdown,
            loadAssistants,
            loadAssistantDriveFolders,
            handleAssistantTaxFilterChange,
            openCreateAssistantModal,
            openEditAssistantModal,
            toggleFolderForAssistant,
            saveAssistant,
            deleteAssistant,
            selectAssistantForChat,
            clearChatHistory,
            handleChatPaste,
            handleChatFileUpload,
            removeChatImage,
            removeChatAttachment,
            triggerChatFileInput,
            sendChatMessage,
            // Chức năng 1: Checker & AI Fix NĐ 30
            checkerInputMode,
            checkerFile,
            checkerFileName,
            checkerRawText,
            isCheckingNd30,
            checkResult,
            selectedIssue,
            isAiFixing,
            fixedDoc,
            checkerActiveView,
            isSavingCheckerToDrive,
            checkerSelectedDriveFolder,
            checkerRawLines,
            resetChecker,
            loadCheckerSampleDoc,
            handleCheckerFileInput,
            handleCheckerFileDrop,
            runCheckNd30,
            runAiAutoFix,
            exportDocWord,
            exportDocPdf,
            saveDocToDrive,
            isSavingDoc,
            saveCurrentDocAndSync,
            // Chức năng 2: Composer 3 bước (hanhchanh.ai.vn)
            composerStep,
            composerForm,
            composerReferenceImages,
            isGeneratingDoc,
            generatedDoc,
            isRefiningDoc,
            refinePrompt,
            refineModalOpen,
            handleTemplatePresetChange,
            updateLivePreviewFromForm,
            addComposerRecipient,
            removeComposerRecipient,
            handleReferenceImageUpload,
            removeReferenceImage,
            generateDocWithAi,
            submitAiRefinement,
            // Danh sách văn bản đã soạn
            draftedDocuments,
            selectedDraftId,
            loadDraftedDocuments,
            loadSelectedDraft,
            saveCurrentDocAsDraft,
            deleteCurrentDraft,
            isSavingComposerParams,
            loadComposerDefaultParams,
            saveComposerDefaultParams,
            resetToDefaultComposerParams,
            // Cấu hình Văn bản hành chính (Thư mục Google Drive, NotebookLM & Cache Token)
            adminDocConfig,
            adminConfigDriveFolders,
            adminConfigTaxOnlyFilter,
            isLoadingAdminConfigFolders,
            isSavingAdminDocConfig,
            adminDocConfigFiles,
            isLoadingAdminDocFiles,
            isUploadingAdminDocPdf,
            isCachingAdminDocFiles,
            adminDocConfigCachedCount,
            openAdminDocConfigMenu,
            loadAdminDocDriveFolders,
            loadAdminDocConfigSettings,
            loadAdminDocConfigFiles,
            onAdminDocReferenceFolderChange,
            saveAdminDocConfigSettings,
            handleAdminDocConfigPdfUpload,
            processAndCacheAllFolderFiles,
            processSingleAdminDocFileCache,
            // Chọn một hoặc nhiều thư mục Google Drive cấp 1
            selectedDriveFolderIds,
            loadSelectedDriveFolders,
            toggleFolderSelection,
            toggleSelectAllFolders,
            saveSelectedFolders,
            // Cấu hình Gemini AI
            geminiConfig,
            isTestingGemini,
            isSavingGeminiConfig,
            loadGeminiConfig,
            saveGeminiConfig,
            testGeminiConnection,
            // Tab 1
            fieldsInput,
            suggestedTags,
            fromDate,
            toDate,
            datePreset,
            isScanning,
            hasScanned,
            autoSaveStatus,
            documents,
            selectedDocIds,
            searchQuery,
            agencyFilter,
            sourceFilter,
            typeFilter,
            selectedFolderForBatch,
            filteredDocuments,
            uniqueAgencies,
            uniqueSources,
            isAllSelected,
            previewDoc,
            isDownloadingBatch,
            uploadModalOpen,
            isUploading,
            uploadResults,
            uploadSummary,
            // Tab 1 Methods
            handleFieldsChange,
            toggleTag,
            isTagSelected,
            applyDatePreset,
            runScan,
            toggleSelectAll,
            toggleSelectDoc,
            applyBatchFolder,
            applyBatchNotebook,
            getNotebookName,
            downloadBatchZip,
            uploadSelectedToDrive,
            uploadSelectedToNotebookLM,
            downloadDocLocally,
            // NotebookLM
            notebooks,
            // Tự động hóa NotebookLM
            notebooklmAutoStatus,
            isCheckingAutoStatus,
            isTriggeringLogin,
            isSyncingGoogleNotebooks,
            checkNotebookLMAutoStatus,
            triggerNotebookLMLogin,
            syncGoogleNotebooks,
            defaultNotebookId,
            selectedNotebookForBatch,
            batchUploadedNotebookId,
            notebooklmStorageDir,
            isSavingNotebook,
            isSavingUploadedToNotebook,
            notebookModalOpen,
            notebookSummary,
            notebookResults,
            newNotebookName,
            newNotebookUrl,
            newNotebookDesc,
            isSavingNotebookItem,
            loadNotebooks,
            saveNewNotebook,
            deleteNotebookItem,
            setDefaultNotebookItem,
            openNotebookStorageFolder,
            openNotebookLMUrl,
            resetNotebooksToDefault,
            // Tab 2
            driveStatus,
            folders,
            defaultFolderId,
            defaultFolderName,
            isTestingConnection,
            newFolderName,
            newFolderParent,
            isCreatingFolder,
            clientIdInput,
            clientSecretInput,
            refreshTokenInput,
            isSavingDriveCreds,
            // Website Sources CRUD
            sources,
            newSourceDomain,
            newSourceName,
            isSavingSource,
            loadSources,
            addSource,
            toggleSource,
            enableAllSources,
            deleteSource,
            resetSources,
            // Tab 2 Methods
            // Google OAuth 2.0 Calendar & Tasks
            googleAuthStatus,
            isStartingOAuth,
            isCheckingGoogleAuth,
            showManualOAuthInput,
            manualAuthCodeInput,
            manualRefreshTokenInput,
            showOAuthFlowModal,
            googleAuthUrl,
            checkGoogleCalendarTasksStatus,
            startGoogleOAuthFlow,
            submitManualAuthCode,
            submitManualRefreshToken,
            openOAuthInstructionsModal,
            testDriveConnection,
            importLocalConfig,
            saveDriveCredentials,
            createNewDriveFolder,
            setDefaultFolder,
            // Tab 3: Upload và lưu văn bản (MỚI)
            uploadedFiles,
            selectedUploadedIds,
            isUploadingLocalFiles,
            isProcessingLocalUpload,
            batchUploadedFolderId,
            uploadLocalModalOpen,
            uploadLocalSummary,
            uploadLocalResults,
            isAllUploadedSelected,
            handleFileInputChange,
            handleFileDrop,
            processSelectedLocalFiles,
            toggleSelectUploaded,
            toggleSelectAllUploaded,
            applyBatchUploadedFolder,
            applyBatchUploadedNotebook,
            removeUploadedFile,
            removeSelectedUploadedFiles,
            clearAllUploadedFiles,
            uploadSelectedUploadedFilesToDrive,
            uploadSelectedUploadedFilesToNotebookLM,
            getUploadedFileIcon,
            // Helpers
            getDocTypeBadgeClass,
            getAgencyBadgeClass,
            filterTaxOnly,
            handleTaxFilterToggle,
            allDriveFolders,
            allNotebooks,
            getSourceBadgeClass,
            getSourceArticleUrl
        };
    }
}).mount('#app');
