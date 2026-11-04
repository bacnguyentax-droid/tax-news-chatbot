import os

# 1. Update manage_app/drive_service.py
with open("manage_app/drive_service.py", "r", encoding="utf-8") as f:
    ds_text = f.read()

ds_old = '''    def list_folders(self) -> List[Dict[str, Any]]:
        """Lấy danh sách các thư mục phù hợp trên Google Drive, CHỈ hiển thị các thư mục có chứa ký tự 'Tax' trong tên"""
        if not self.service:'''

ds_new = '''    def list_folders(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Lấy danh sách các thư mục phù hợp trên Google Drive, CHỈ hiển thị các thư mục có chứa ký tự 'Tax' trong tên"""
        if self.folders_cache and not force_refresh:
            return self.folders_cache
        if not self.service:'''

if ds_old in ds_text:
    ds_text = ds_text.replace(ds_old, ds_new, 1)
    print("drive_service list_folders signature patched")
else:
    print("drive_service list_folders signature NOT found")

with open("manage_app/drive_service.py", "w", encoding="utf-8") as f:
    f.write(ds_text)


# 2. Update manage_app/app.py
with open("manage_app/app.py", "r", encoding="utf-8") as f:
    app_text = f.read()

app_config_old = '''    sources = ConfigManager.get_sources()
    
    return jsonify({
        "success": True,
        "last_fields": ConfigManager.get_last_fields(),
        "date_filter": config.get("date_filter", {}),
        "drive_connected": is_connected,
        "drive_user": user_info,
        "default_folder_id": config.get("google_drive", {}).get("default_folder_id", "root"),
        "default_folder_name": config.get("google_drive", {}).get("default_folder_name", "📁 My Drive (Thư mục gốc)"),'''

app_config_new = '''    sources = ConfigManager.get_sources()
    drive_folders = drive_service.list_folders() if is_connected else []
    
    return jsonify({
        "success": True,
        "last_fields": ConfigManager.get_last_fields(),
        "date_filter": config.get("date_filter", {}),
        "drive_connected": is_connected,
        "drive_user": user_info,
        "default_folder_id": config.get("google_drive", {}).get("default_folder_id", "1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK"),
        "default_folder_name": config.get("google_drive", {}).get("default_folder_name", "📁 Tax_Nghiệp vụ thuế"),
        "folders": drive_folders,'''

if app_config_old in app_text:
    app_text = app_text.replace(app_config_old, app_config_new, 1)
    print("app.py get_system_config patched")
else:
    print("app.py get_system_config NOT found")

app_dfolders_old = '''@app.route("/api/drive/folders", methods=["GET"])
def get_drive_folders():
    """Lấy danh sách các thư mục có trên Google Drive"""
    folders = drive_service.list_folders()
    return jsonify({"success": True, "folders": folders})'''

app_dfolders_new = '''@app.route("/api/drive/folders", methods=["GET"])
def get_drive_folders():
    """Lấy danh sách các thư mục có trên Google Drive"""
    force = request.args.get("refresh") == "1"
    folders = drive_service.list_folders(force_refresh=force)
    return jsonify({"success": True, "folders": folders})'''

if app_dfolders_old in app_text:
    app_text = app_text.replace(app_dfolders_old, app_dfolders_new, 1)
    print("app.py get_drive_folders patched")
else:
    print("app.py get_drive_folders NOT found")

with open("manage_app/app.py", "w", encoding="utf-8") as f:
    f.write(app_text)


# 3. Update manage_app/static/js/app.js
with open("manage_app/static/js/app.js", "r", encoding="utf-8") as f:
    js_text = f.read()

# Update folders initial ref and updateTaxFilteredLists
old_js_folders = '''        const allDriveFolders = ref([]);
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
        ]);'''

new_js_folders = '''        const allDriveFolders = ref([]);
        const filterTaxOnly = ref(localStorage.getItem('filterTaxOnly') !== 'false');
        const allNotebooks = ref([]);
        const folders = ref([
            { id: '1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK', name: 'Tax_Nghiệp vụ thuế', raw_name: 'Tax_Nghiệp vụ thuế', clean_name: 'Tax_Nghiệp vụ thuế', is_tax: true }
        ]);
        const getFolderName = (id) => {
            const f = folders.value.find(item => item.id === id);
            return f ? (f.raw_name || f.clean_name || f.name) : 'Tax_Nghiệp vụ thuế';
        };
        const updateTaxFilteredLists = () => {
            if (filterTaxOnly.value) {
                if (allDriveFolders.value && allDriveFolders.value.length > 0) {
                    folders.value = allDriveFolders.value.filter(f => f.is_tax || (f.name && f.name.toLowerCase().includes('tax')) || (f.raw_name && f.raw_name.toLowerCase().includes('tax')));
                }
                if (allNotebooks.value && allNotebooks.value.length > 0) {
                    notebooks.value = allNotebooks.value.filter(n => n.is_tax || (n.name && n.name.toLowerCase().includes('tax')));
                }
            } else {
                if (allDriveFolders.value && allDriveFolders.value.length > 0) {
                    folders.value = [...allDriveFolders.value];
                }
                if (allNotebooks.value && allNotebooks.value.length > 0) {
                    notebooks.value = [...allNotebooks.value];
                }
            }
            if (folders.value.length > 0) {
                const currentMatch = folders.value.find(f => f.id === defaultFolderId.value);
                if (!currentMatch) {
                    const taxDefault = folders.value.find(f => (f.raw_name && f.raw_name.includes('Nghiệp vụ thuế')) || (f.name && f.name.includes('Nghiệp vụ thuế')));
                    if (taxDefault) {
                        defaultFolderId.value = taxDefault.id;
                        defaultFolderName.value = taxDefault.raw_name || taxDefault.clean_name || taxDefault.name;
                    }
                }
            }
        };
        const handleTaxFilterToggle = () => {
            localStorage.setItem('filterTaxOnly', filterTaxOnly.value ? 'true' : 'false');
            updateTaxFilteredLists();
        };'''

if old_js_folders in js_text:
    js_text = js_text.replace(old_js_folders, new_js_folders, 1)
    print("app.js folders & getFolderName patched")
else:
    print("app.js folders & getFolderName NOT found")

# Update loadConfig to receive folders from /api/config
old_load_cfg_folders = '''                    if (data.default_folder_id) {
                        defaultFolderId.value = data.default_folder_id;
                        defaultFolderName.value = data.default_folder_name || '📁 My Drive (Thư mục gốc)';
                        selectedFolderForBatch.value = data.default_folder_id;
                    }'''

new_load_cfg_folders = '''                    if (data.folders && data.folders.length > 0) {
                        allDriveFolders.value = data.folders;
                        updateTaxFilteredLists();
                    }
                    if (data.default_folder_id) {
                        defaultFolderId.value = data.default_folder_id;
                        defaultFolderName.value = data.default_folder_name || 'Tax_Nghiệp vụ thuế';
                        selectedFolderForBatch.value = data.default_folder_id;
                    }'''

if old_load_cfg_folders in js_text:
    js_text = js_text.replace(old_load_cfg_folders, new_load_cfg_folders, 1)
    print("app.js loadConfig folders patched")
else:
    print("app.js loadConfig folders NOT found")

# Update runScan to guarantee valid selected_folder_id
old_runscan_map = '''                    documents.value = data.documents.map(d => ({
                        ...d,
                        selected_folder_id: d.selected_folder_id || defaultFolderId.value || 'root',
                        selected_notebook_id: d.selected_notebook_id || selectedNotebookForBatch.value || defaultNotebookId.value || 'nb_tax_default',
                        upload_status: 'idle',
                        notebook_status: 'idle',
                        is_downloaded: false,
                        drive_link: ''
                    }));'''

new_runscan_map = '''                    documents.value = data.documents.map(d => {
                        const targetFid = (d.selected_folder_id && folders.value.some(f => f.id === d.selected_folder_id))
                            ? d.selected_folder_id
                            : (defaultFolderId.value || '1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK');
                        const targetNbid = (d.selected_notebook_id && notebooks.value.some(n => n.id === d.selected_notebook_id))
                            ? d.selected_notebook_id
                            : (selectedNotebookForBatch.value || defaultNotebookId.value || 'nb_tax_nghiep_vu_thue');
                        return {
                            ...d,
                            selected_folder_id: targetFid,
                            selected_notebook_id: targetNbid,
                            upload_status: 'idle',
                            notebook_status: 'idle',
                            is_downloaded: false,
                            drive_link: ''
                        };
                    });'''

if old_runscan_map in js_text:
    js_text = js_text.replace(old_runscan_map, new_runscan_map, 1)
    print("app.js runScan mapping patched")
else:
    print("app.js runScan mapping NOT found")

# Update loadDriveFolders to auto-fix documents folder id
old_load_drive_folders = '''        const loadDriveFolders = async () => {
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
        };'''

new_load_drive_folders = '''        const loadDriveFolders = async () => {
            try {
                const res = await fetch('/api/drive/folders');
                const data = await res.json();
                if (data.success && data.folders && data.folders.length > 0) {
                    allDriveFolders.value = data.folders;
                    updateTaxFilteredLists();
                    if (documents.value && documents.value.length > 0) {
                        documents.value.forEach(doc => {
                            if (!doc.selected_folder_id || !folders.value.some(f => f.id === doc.selected_folder_id)) {
                                doc.selected_folder_id = defaultFolderId.value || '1Wuza1Z1SW5dx2EDq4t8T3vW2NRi99qkK';
                            }
                        });
                    }
                    const matched = folders.value.find(f => f.id === defaultFolderId.value);
                    if (matched) {
                        defaultFolderName.value = matched.raw_name || matched.clean_name || matched.name;
                    } else if (folders.value.length > 0) {
                        const taxDefault = folders.value.find(f => f.raw_name === 'Tax_Nghiệp vụ thuế' || (f.name && f.name.includes('Tax_Nghiệp vụ thuế')));
                        if (taxDefault) {
                            defaultFolderId.value = taxDefault.id;
                            defaultFolderName.value = taxDefault.raw_name || taxDefault.clean_name || taxDefault.name;
                            selectedFolderForBatch.value = taxDefault.id;
                        }
                    }
                }
            } catch (e) {
                console.error('Lỗi lấy folders:', e);
            }
        };'''

if old_load_drive_folders in js_text:
    js_text = js_text.replace(old_load_drive_folders, new_load_drive_folders, 1)
    print("app.js loadDriveFolders patched")
else:
    print("app.js loadDriveFolders NOT found")

# Export getFolderName in Vue setup return
old_return = '''            getNotebookName,
            applyBatchNotebook,'''

new_return = '''            getFolderName,
            getNotebookName,
            applyBatchNotebook,'''

if old_return in js_text:
    js_text = js_text.replace(old_return, new_return, 1)
    print("app.js getFolderName exported in setup return")
else:
    print("app.js getFolderName export NOT found")

with open("manage_app/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(js_text)


# 4. Update manage_app/templates/index.html
with open("manage_app/templates/index.html", "r", encoding="utf-8") as f:
    html_text = f.read()

# Batch folder option text
old_batch_opt = '''<select 
                                    v-model="selectedFolderForBatch"
                                    class="bg-[#f8f9fa] border border-[#b9d2ec] text-slate-800 text-xs rounded px-2 py-0.5 max-w-[170px] truncate focus:outline-none">
                                    <option v-for="f in folders" :key="f.id" :value="f.id">{{ f.name }}</option>
                                </select>'''

new_batch_opt = '''<select 
                                    v-model="selectedFolderForBatch"
                                    class="bg-[#f8f9fa] border border-[#b9d2ec] text-slate-800 text-xs rounded px-2 py-0.5 max-w-[170px] truncate focus:outline-none">
                                    <option v-for="f in folders" :key="f.id" :value="f.id">{{ f.raw_name || f.clean_name || f.name }}</option>
                                </select>'''

if old_batch_opt in html_text:
    html_text = html_text.replace(old_batch_opt, new_batch_opt, 1)
    print("index.html batch folder option patched")
else:
    print("index.html batch folder option NOT found")

# Table column for each row
old_col_folder = '''                                    <!-- CỘT CHỌN THƯ MỤC GOOGLE DRIVE CHO TỪNG DÒNG (CHỈ HIỂN THỊ THƯ MỤC THẬT) -->
                                    <td>
                                        <div class="space-y-1">
                                            <select 
                                                v-model="doc.selected_folder_id"
                                                class="w-full bg-white border border-[#b9d2ec] text-slate-800 text-xs rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#004b93]">
                                                <option v-for="f in folders" :key="f.id" :value="f.id">
                                                    {{ f.name }}
                                                </option>
                                            </select>
                                            <span class="text-[10px] text-slate-500 block truncate">
                                                Nơi lưu: {{ folders.find(f => f.id === doc.selected_folder_id)?.name || 'Mặc định' }}
                                            </span>
                                        </div>
                                    </td>'''

new_col_folder = '''                                    <!-- CỘT CHỌN THƯ MỤC GOOGLE DRIVE CHO TỪNG DÒNG (CHỈ HIỂN THỊ THƯ MỤC THẬT) -->
                                    <td>
                                        <div class="space-y-1">
                                            <select 
                                                v-model="doc.selected_folder_id"
                                                class="w-full bg-white border border-[#b9d2ec] text-slate-800 text-xs rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#004b93]">
                                                <option v-for="f in folders" :key="f.id" :value="f.id">
                                                    {{ f.raw_name || f.clean_name || f.name }}
                                                </option>
                                            </select>
                                            <div class="flex items-center justify-between text-[10px] text-slate-500">
                                                <span class="truncate" :title="getFolderName(doc.selected_folder_id)">
                                                    <i class="fa-brands fa-google-drive text-[#005baa] mr-1 text-[9px]"></i>Nơi lưu: {{ getFolderName(doc.selected_folder_id) }}
                                                </span>
                                            </div>
                                        </div>
                                    </td>'''

if old_col_folder in html_text:
    html_text = html_text.replace(old_col_folder, new_col_folder, 1)
    print("index.html table column folder patched")
else:
    print("index.html table column folder NOT found")

# Upload manual file column
old_manual_col = '''                                            <select 
                                                 v-model="file.selected_folder_id"
                                                 class="w-full bg-white border border-[#b9d2ec] text-slate-800 text-xs rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#004b93]">
                                                 <option v-for="f in folders" :key="f.id" :value="f.id">
                                                     {{ f.name }}
                                                 </option>
                                             </select>
                                             <span class="text-[10px] text-slate-500 block truncate">
                                                 Lưu tại: {{ folders.find(f => f.id === file.selected_folder_id)?.name || 'Mặc định' }}
                                             </span>'''

new_manual_col = '''                                            <select 
                                                 v-model="file.selected_folder_id"
                                                 class="w-full bg-white border border-[#b9d2ec] text-slate-800 text-xs rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#004b93]">
                                                 <option v-for="f in folders" :key="f.id" :value="f.id">
                                                     {{ f.raw_name || f.clean_name || f.name }}
                                                 </option>
                                             </select>
                                             <div class="flex items-center justify-between text-[10px] text-slate-500">
                                                 <span class="truncate" :title="getFolderName(file.selected_folder_id)">
                                                     <i class="fa-brands fa-google-drive text-[#005baa] mr-1 text-[9px]"></i>Lưu tại: {{ getFolderName(file.selected_folder_id) }}
                                                 </span>
                                             </div>'''

if old_manual_col in html_text:
    html_text = html_text.replace(old_manual_col, new_manual_col, 1)
    print("index.html manual file column patched")
else:
    print("index.html manual file column NOT found")

# Bump script version in index.html to 16.0
if 'app.js?v=15.0' in html_text:
    html_text = html_text.replace('app.js?v=15.0', 'app.js?v=16.0')
    print("index.html version bumped to v=16.0")

with open("manage_app/templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_text)

print("ALL PATCHES APPLIED SUCCESSFULLY!")
