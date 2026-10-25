"""
Document Processing Module for VPDT Portal
Automates the document assignment (phân công / luân chuyển) workflow.
Supports processing multiple document categories ('CV Cảnh báo rủi ro', 'CV kiểm tra, xử lý hóa đơn', etc.)
with interactive/automated login detection and browser control.
"""

import sys
import time
from typing import Dict, Any, Optional, List
from playwright.sync_api import sync_playwright, Page, BrowserContext

from vpdt_manager.config import (
    BASE_URL,
    LOGIN_URL,
    SESSION_FILE,
    SCREENSHOT_PATH,
    load_config
)


class VPDTDocumentProcessor:
    """Automates processing of incoming documents (Văn bản đến)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()

    def _is_logged_in(self, page: Page) -> bool:
        """Checks if current page is logged into the portal."""
        try:
            # If login username input is visible, not logged in
            if page.locator("#_58_login, input[name='_58_login']").count() > 0:
                if page.locator("#_58_login, input[name='_58_login']").first.is_visible():
                    return False
            if "/web/guest/login" in page.url:
                return False
            if page.locator("body.signed-in").count() > 0:
                return True
            if "/group/kv" in page.url or "/group/" in page.url:
                return True
            if page.locator("text='Văn bản đến'").count() > 0:
                return True
            return False
        except Exception:
            return False

    def wait_for_user_login(
        self,
        page: Page,
        username: str = "",
        password: str = "",
        log=None,
        timeout_sec: int = 180,
        stop_event=None
    ) -> bool:
        """
        Navigates to login if needed, auto-fills credentials if provided,
        and waits until login is confirmed (by user or system).
        """
        def _log(msg: str):
            if log:
                log(msg)
            else:
                print(f"[VPDT Login] {msg}")

        # Check if already logged in
        if self._is_logged_in(page):
            _log("🎉 Phiên làm việc đã đăng nhập sẵn!")
            return True

        _log("🔑 Hệ thống đang ở trang đăng nhập...")

        # If username and password provided, attempt auto-fill
        user = username or self.config.get("username", "")
        pwd = password or self.config.get("password", "")

        if user and pwd:
            try:
                user_input = page.locator("#_58_login, input[name='_58_login']").first
                pass_input = page.locator("#_58_password, input[name='_58_password']").first

                user_input.wait_for(state="visible", timeout=10000)
                user_input.fill(user)
                time.sleep(0.3)
                pass_input.fill(pwd)
                time.sleep(0.5)

                # Fix Liferay Tomcat jsessionid bug
                page.evaluate("""() => {
                    const fm = document.getElementById('_58_fm');
                    if (fm && fm.action.includes(';jsessionid=')) {
                        fm.action = fm.action.replace(/;jsessionid=[^?&]+/, '');
                    }
                }""")

                submit_btn = page.locator("input[type='submit'][value*='Đăng nhập'], #_58_fm input[type='submit']").first
                if submit_btn.is_visible():
                    _log(f"   Đang tự động đăng nhập với tài khoản: {user}...")
                    submit_btn.click()
                else:
                    pass_input.press("Enter")
            except Exception as e:
                _log(f"   (Lưu ý điền tự động: {e})")

        _log("⏳ Đang chờ xác nhận đăng nhập thành công vào hệ thống (bạn có thể thao tác trực tiếp trên trình duyệt nếu cần)...")
        start_t = time.time()
        while time.time() - start_t < timeout_sec:
            if stop_event and stop_event.is_set():
                _log("🛑 Đã nhận lệnh dừng từ người dùng.")
                return False

            if self._is_logged_in(page):
                _log("🎉 ĐÃ ĐĂNG NHẬP THÀNH CÔNG VÀO HỆ THỐNG VPDT!")
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=6000)
                except Exception:
                    pass
                time.sleep(2.0)
                try:
                    page.context.storage_state(path=str(SESSION_FILE))
                except Exception:
                    pass
                return True
            time.sleep(1)

        _log("⚠️ Hết thời gian chờ đăng nhập (180 giây).")
        return False

    def _safe_goto(
        self,
        page: Page,
        url: str,
        log,
        wait_until: str = "commit",
        max_retries: int = 3
    ) -> bool:
        """
        Navigates to URL safely with retry logic and fallback,
        handling net::ERR_ABORTED, net::ERR_TOO_MANY_REDIRECTS, and transient network errors.
        """
        for attempt in range(1, max_retries + 1):
            try:
                # Settle previous navigation / ajax
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=3000)
                except Exception:
                    pass
                time.sleep(1.0)

                # 1. If already on the target URL (or /vbdxl if targeting vbdxl), check if loaded
                if ("/group/kv/vbdxl" in url or "/group/kv/vbd" in url) and ("/group/kv/vbd" in page.url):
                    if page.locator("th:has-text('Loại văn bản')").count() > 0:
                        return True

                # 2. Prefer clicking menu item if available on the page (avoids net::ERR_ABORTED)
                if "/group/kv/vbd" in url or "/group/kv/vbdxl" in url:
                    try:
                        vbd_nav = page.locator("#navigation a:has-text('Văn bản đến'), a:has-text('Văn bản đến'), a[href*='/group/kv/vbd']").first
                        if vbd_nav.count() > 0 and vbd_nav.is_visible():
                            log("👉 Bấm vào menu 'Văn bản đến' trên thanh điều hướng...")
                            vbd_nav.click()
                            for _ in range(8):
                                time.sleep(1)
                                if "/group/kv/vbd" in page.url or page.locator("th:has-text('Loại văn bản')").count() > 0:
                                    time.sleep(1)
                                    return True
                    except Exception as ex_nav:
                        log(f"   (Thử bấm menu: {ex_nav})")

                # 3. Direct navigation using wait_until='commit' to prevent net::ERR_ABORTED
                try:
                    page.goto(url, wait_until="commit", timeout=25000)
                except Exception as e_goto:
                    if "net::ERR_ABORTED" in str(e_goto):
                        log("   (Chuyển hướng trang đang hoàn tất...)")
                    else:
                        raise e_goto

                # Settle DOM
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                except Exception:
                    pass
                time.sleep(2.0)

                # If targeting vbdxl, wait for redirect or table
                if "/group/kv/vbd" in url:
                    for _ in range(6):
                        if "/group/kv/vbd" in page.url or page.locator("th:has-text('Loại văn bản')").count() > 0:
                            return True
                        time.sleep(1)

                return True

            except Exception as e:
                err_str = str(e)
                log(f"   ⚠️ Lần {attempt}/{max_retries} mở trang '{url}': {err_str[:80]}...")
                time.sleep(2.0 * attempt)

                # Fallback: try navigating to /group/kv first if on base
                if "/group/kv/vbdxl" in url and "/group/kv" not in page.url:
                    try:
                        page.goto(f"{BASE_URL}/group/kv", wait_until="commit", timeout=20000)
                        time.sleep(2.0)
                    except Exception:
                        pass

                if attempt == max_retries:
                    raise e

        return False

    def _ensure_authenticated(self, page: Page, log) -> bool:
        """Ensures session is still active during page transitions."""
        if self._is_logged_in(page):
            return True
        log("🔑 Phiên làm việc cần đăng nhập lại...")
        return self.wait_for_user_login(page, log=log, timeout_sec=60)

    def _apply_filter(self, page: Page, doc_type: str, log) -> bool:
        """Filters the table to show specified document type."""
        try:
            self._ensure_authenticated(page, log)

            # Trường hợp đặc biệt: 'Quyết định đính chính quyết định XPHC' không có trong dropdown
            # Lọc danh sách 'Tất cả' để bộ duyệt trực tiếp tìm các dòng tương ứng
            if "đính chính" in doc_type.lower():
                log(f"Loại văn bản '{doc_type}' sẽ được duyệt từ danh sách chung (Tất cả)...")
                filter_target = "Tất cả"
            elif "xử phạt" in doc_type.lower():
                filter_target = "Quyết định xử phạt vi phạm hành chinh"
            else:
                filter_target = doc_type

            log(f"Đang lọc Loại văn bản: '{filter_target}'...")
            header_th = page.locator("th:has-text('Loại văn bản')").first
            header_th.wait_for(state="visible", timeout=15000)
            dropdown = header_th.locator(".ui-selectonemenu, div[role='combobox']").first
            dropdown.click()
            time.sleep(1)

            opt = page.locator(
                f".ui-selectonemenu-panel:visible li:has-text('{filter_target}'), "
                f"li.ui-selectonemenu-item:visible:has-text('{filter_target}')"
            ).first
            if opt.count() > 0:
                opt.click()
            else:
                opt_any = page.locator(f"li.ui-selectonemenu-item:has-text('{filter_target}')").last
                opt_any.click(force=True)

            log("Đang chờ bảng dữ liệu cập nhật...")
            time.sleep(4)
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            try:
                page.wait_for_selector(".ui-blockui", state="hidden", timeout=5000)
            except Exception:
                pass

            log(f"✅ Đã lọc xong danh sách '{filter_target}'.")
            return True
        except Exception as e:
            log(f"⚠️ Lỗi khi lọc loại văn bản '{doc_type}': {e}")
            return False

    def _assign_and_transfer_current_doc(
        self,
        page: Page,
        log,
        click_transfer: bool = True
    ) -> bool:
        """
        Executes assignment steps inside 'Thông tin luân chuyển văn bản':
          - Trang 1: Chọn Nam, Ngo Hoang Nam
          - Trang 3: Chọn Lanh, Nguyen Xuan Lanh
          - Cách thức xử lý: Lưu văn bản
          - Chuyên viên xử lý chính: Nam, Ngo Hoang Nam
          - Bấm nút Chuyển
        """
        try:
            # Step 4.1: Trang 1 chọn Nam, Ngo Hoang Nam
            log("   [4.1] Chọn Nam, Ngo Hoang Nam (DLRR-HCM) tại Trang 1...")
            row_nam = page.locator("div[id*='dt3Org'] tbody tr:has-text('Nam, Ngo Hoang Nam')").first
            row_nam.wait_for(state="visible", timeout=10000)
            chk_nam = row_nam.locator(".ui-chkbox-box").first
            if "ui-state-active" not in (chk_nam.get_attribute("class") or ""):
                chk_nam.click()
            time.sleep(0.8)

            # Step 4.2: Chuyển sang Trang 3
            log("   [4.2] Chuyển danh sách sang Trang 3...")
            btn_page3 = page.locator("div[id*='dt3Org'] .ui-paginator-page:text-is('3')").first
            btn_page3.wait_for(state="visible", timeout=10000)
            btn_page3.click()
            time.sleep(2.0)

            # Step 4.3: Trang 3 chọn Lanh, Nguyen Xuan Lanh
            log("   [4.3] Chọn Lanh, Nguyen Xuan Lanh (DLRR-HCM) tại Trang 3...")
            row_lanh = page.locator("div[id*='dt3Org'] tbody tr:has-text('Lanh, Nguyen Xuan Lanh')").first
            row_lanh.wait_for(state="visible", timeout=10000)
            chk_lanh = row_lanh.locator(".ui-chkbox-box").first
            if "ui-state-active" not in (chk_lanh.get_attribute("class") or ""):
                chk_lanh.click()
            time.sleep(0.8)

            # Step 4.4: Cách thức xử lý: Lưu văn bản
            log("   [4.4] Chọn Cách thức xử lý: 'Lưu văn bản'...")
            row_luu = page.locator("div[id*='dt3CTXL'] tr:has-text('Lưu văn bản')").first
            row_luu.wait_for(state="visible", timeout=10000)
            rad_luu = row_luu.locator(".ui-radiobutton-box").first
            if "ui-state-active" not in (rad_luu.get_attribute("class") or ""):
                rad_luu.click()
            time.sleep(0.8)

            # Step 4.5: Chuyên viên xử lý chính: Nam, Ngo Hoang Nam
            log("   [4.5] Chọn Chuyên viên xử lý chính: 'Nam, Ngo Hoang Nam'...")
            sel_cv = page.locator("div[id*='sel3NXLC'].ui-selectonemenu").first
            sel_cv.wait_for(state="visible", timeout=10000)
            sel_cv.click()
            time.sleep(0.8)
            opt_cv = page.locator(".ui-selectonemenu-panel:visible li:has-text('Nam, Ngo Hoang Nam')").first
            opt_cv.wait_for(state="visible", timeout=5000)
            opt_cv.click()
            time.sleep(1.0)

            # Step 4.6: Bấm nút Chuyển
            if click_transfer:
                log("   [4.6] 🚀 Bấm nút 'Chuyển' ở cuối trang...")
                chuyen_btn = page.locator("button:has-text('Chuyển')").first
                chuyen_btn.wait_for(state="visible", timeout=8000)
                chuyen_btn.click()
                time.sleep(5)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                return True
            else:
                log("   [Dry-run] Bỏ qua bước bấm Chuyển.")
                return True
        except Exception as e:
            log(f"   ⚠️ Lỗi trong bước phân công / chuyển: {e}")
            return False

    def _save_current_doc(
        self,
        page: Page,
        log,
        click_transfer: bool = True
    ) -> bool:
        """
        Executes 'Lưu văn bản' directly on the document detail page:
          - Bấm nút 'Lưu văn bản' trên thanh thao tác
          - Tự động chấp nhận xác nhận: confirm('Bạn thực sự muốn thực hiện thao tác này?')
        """
        try:
            log("   [Lưu] Tìm nút 'Lưu văn bản' trên trang chi tiết...")
            luu_btn = page.locator("button:has-text('Lưu văn bản'), input[value*='Lưu văn bản']").first
            luu_btn.wait_for(state="visible", timeout=10000)

            if click_transfer:
                log("   [Lưu] 🚀 Bấm nút 'Lưu văn bản' và xác nhận lưu...")
                page.once("dialog", lambda dialog: dialog.accept())
                luu_btn.click()
                time.sleep(4)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                try:
                    page.wait_for_selector(".ui-blockui", state="hidden", timeout=6000)
                except Exception:
                    pass
                log("   [Lưu] ✅ Đã bấm Lưu văn bản thành công.")
                return True
            else:
                log("   [Dry-run] Bỏ qua bước bấm Lưu văn bản.")
                return True
        except Exception as e:
            log(f"   ⚠️ Lỗi trong bước Lưu văn bản: {e}")
            return False

    def process_workflow(
        self,
        doc_types: List[str],
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_documents: Optional[int] = None,
        click_transfer: bool = True,
        headless: bool = False,
        stop_event=None,
        log_callback=None
    ) -> Dict[str, Any]:
        """
        Unified workflow requested by user:
          1. Launches browser and opens http://vpdt.cucthue.hochiminhcity.gov.vn/
          2. Waits until user/portal completes login.
          3. For each selected document type, filters and assigns/transfers all documents.
        """
        def log(msg: str):
            print(f"[VPDT Processor] {msg}")
            if log_callback:
                try:
                    log_callback(msg)
                except Exception:
                    pass

        result = {
            "success": False,
            "message": "",
            "doc_types": doc_types,
            "total_processed": 0,
            "processed_documents": [],
            "screenshot": ""
        }

        if not doc_types:
            result["message"] = "Chưa chọn loại văn bản nào để xử lý."
            log(f"⚠️ {result['message']}")
            return result

        with sync_playwright() as p:
            log("🌐 Đang khởi động trình duyệt Google Chrome...")
            browser = None
            for ch in ["chrome", "msedge", None]:
                try:
                    kwargs = {
                        "headless": headless,
                        "slow_mo": 300,
                        "args": ["--start-maximized", "--ignore-certificate-errors"]
                    }
                    if ch:
                        kwargs["channel"] = ch
                    browser = p.chromium.launch(**kwargs)
                    break
                except Exception:
                    continue

            if not browser:
                result["message"] = "Không thể khởi động trình duyệt Chrome/Edge trên máy."
                log(f"❌ {result['message']}")
                return result

            context_kwargs = {
                "no_viewport": True,
                "ignore_https_errors": True
            }
            if SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 50:
                try:
                    context_kwargs["storage_state"] = str(SESSION_FILE)
                except Exception:
                    pass

            try:
                context: BrowserContext = browser.new_context(**context_kwargs)
            except Exception:
                context_kwargs.pop("storage_state", None)
                context = browser.new_context(**context_kwargs)
            page: Page = context.new_page()

            try:
                # Step 1: Open portal base url
                log(f"👉 Bước 1: Mở trang chủ hệ thống: {BASE_URL}...")
                self._safe_goto(page, BASE_URL, log)

                # Step 2: Wait for login
                log("👉 Bước 2: Kiểm tra và chờ đăng nhập...")
                logged_in = self.wait_for_user_login(
                    page=page,
                    username=username or self.config.get("username", ""),
                    password=password or self.config.get("password", ""),
                    log=log,
                    timeout_sec=180,
                    stop_event=stop_event
                )

                if not logged_in:
                    result["message"] = "Đăng nhập không thành công hoặc người dùng đã hủy."
                    return result

                # Step 3: Process each selected document category
                total_all = 0
                for d_idx, doc_type in enumerate(doc_types, start=1):
                    if stop_event and stop_event.is_set():
                        log("🛑 Đã nhận tín hiệu dừng từ người dùng.")
                        break

                    log("\n" + "#" * 60)
                    log(f"📂 [Mục {d_idx}/{len(doc_types)}] BẮT ĐẦU XỬ LÝ LOẠI: '{doc_type}'")
                    log("#" * 60)

                    # Navigate to incoming docs
                    log("👉 Mở phân hệ Văn bản đến -> Cần xử lý...")
                    self._safe_goto(page, f"{BASE_URL}/group/kv/vbdxl", log)
                    self._ensure_authenticated(page, log)

                    # Filter by doc_type
                    self._apply_filter(page, doc_type, log)

                    processed_set = set()
                    loop_index = 0

                    while True:
                        if stop_event and stop_event.is_set():
                            log("🛑 Đã nhận tín hiệu dừng từ người dùng.")
                            break

                        if max_documents and total_all >= max_documents:
                            log(f"ℹ️ Đã đạt giới hạn tối đa ({max_documents} văn bản).")
                            break

                        self._ensure_authenticated(page, log)

                        if "/group/kv/vbdxl" not in page.url:
                            self._safe_goto(page, f"{BASE_URL}/group/kv/vbdxl", log)
                            self._apply_filter(page, doc_type, log)

                        # Phân loại cách xử lý:
                        # 1. Nhóm Lưu văn bản: Quyết định xử phạt vi phạm hành chính, Quyết định đính chính quyết định XPHC, TB Người nộp thuế bỏ địa chỉ kinh doanh
                        # 2. Nhóm Phân công: CV Cảnh báo rủi ro, CV kiểm tra, xử lý hóa đơn
                        is_save_only = any(
                            k in doc_type.lower()
                            for k in ["xử phạt", "đính chính", "bỏ địa chỉ", "xphc"]
                        )

                        # Định vị dòng văn bản cần xử lý
                        if "đính chính" in doc_type.lower():
                            target_row = page.locator("tbody[id*=':dto_data'] tr:has-text('Quyết định đính chính')").first
                            if target_row.count() == 0:
                                log(f"🎉 Bảng danh sách không còn văn bản '{doc_type}' nào cần xử lý.")
                                break
                        else:
                            if page.locator("td:has-text('Không tồn tại dữ liệu')").count() > 0:
                                log(f"🎉 Bảng danh sách không còn văn bản '{doc_type}' nào cần xử lý (Tổng 0).")
                                break
                            target_row = page.locator("tbody[id*=':dto_data'] tr").first
                            if target_row.count() == 0:
                                log(f"🎉 Bảng danh sách không còn văn bản '{doc_type}' nào cần xử lý.")
                                break

                        # Lấy liên kết mở văn bản trong dòng
                        visible_links = target_row.locator("a:visible").all()
                        first_doc = None
                        doc_number = ""
                        for lnk in visible_links:
                            txt = lnk.inner_text().strip()
                            if txt:
                                first_doc = lnk
                                doc_number = txt
                                break

                        if not first_doc or not doc_number:
                            log(f"🎉 Không tìm thấy liên kết văn bản mở '{doc_type}'.")
                            break

                        if doc_number in processed_set:
                            log(f"⚠️ Văn bản [{doc_number}] đã được xử lý trong phiên này. Kết thúc nhóm '{doc_type}'.")
                            break

                        loop_index += 1
                        total_all += 1
                        log("\n" + "=" * 55)
                        log(f"📄 [Văn bản #{loop_index} - {doc_type}] Đang mở văn bản: [{doc_number}]...")

                        # Mở văn bản
                        first_doc.click()
                        time.sleep(3)
                        page.wait_for_load_state("domcontentloaded")

                        doc_title = ""
                        try:
                            title_cell = page.locator("tr:has-text('Trích yếu') td").last
                            if title_cell.count() > 0:
                                doc_title = title_cell.inner_text().strip()
                                log(f"   Trích yếu: {doc_title[:80]}...")
                        except Exception:
                            pass

                        if is_save_only:
                            log("   👉 Quy trình: [LƯU VĂN BẢN TRỰC TIẾP]")
                            success_action = self._save_current_doc(
                                page=page,
                                log=log,
                                click_transfer=click_transfer
                            )
                        else:
                            log("   👉 Quy trình: [PHÂN CÔNG CHUYÊN VIÊN]")
                            phan_cong_btn = page.locator("button:has-text('Phân công')").first
                            if phan_cong_btn.count() == 0:
                                log(f"⚠️ Không thấy nút 'Phân công' cho văn bản [{doc_number}]. Quay lại...")
                                self._safe_goto(page, f"{BASE_URL}/group/kv/vbdxl", log)
                                self._apply_filter(page, doc_type, log)
                                continue

                            phan_cong_btn.click()
                            time.sleep(4)

                            success_action = self._assign_and_transfer_current_doc(
                                page=page,
                                log=log,
                                click_transfer=click_transfer
                            )

                        if success_action:
                            processed_set.add(doc_number)
                            result["total_processed"] += 1
                            result["processed_documents"].append({
                                "doc_number": doc_number,
                                "type": doc_type,
                                "title": doc_title,
                                "index": total_all
                            })
                            act_label = "LƯU VĂN BẢN" if is_save_only else "CHUYỂN"
                            log(f"✅ ĐÃ {act_label} THÀNH CÔNG VĂN BẢN [{doc_number}] ({doc_type})")

                            if click_transfer:
                                time.sleep(4)
                                if "/group/kv/vbdxl" not in page.url or page.locator("tbody[id*=':dto_data'] tr").count() == 0:
                                    self._safe_goto(page, f"{BASE_URL}/group/kv/vbdxl", log)
                                    self._apply_filter(page, doc_type, log)
                        else:
                            log(f"❌ Xử lý văn bản [{doc_number}] không thành công.")
                            break

                        time.sleep(2)

                # Final screenshot
                final_scr = "scratch/final_workflow_result.png"
                page.screenshot(path=final_scr, full_page=True)
                result["screenshot"] = final_scr

                result["success"] = True
                result["message"] = (
                    f"Đã hoàn thành! Tổng cộng đã xử lý {result['total_processed']} "
                    f"văn bản cho các mục: {', '.join(doc_types)}."
                )
                log("\n" + "=" * 60)
                log(f"🎉 {result['message']}")
                log(f"📸 Ảnh chụp kết quả: {final_scr}")

                # Keep browser open if headed
                if not headless:
                    log("🟢 Giữ nguyên giao diện trình duyệt mở để bạn kiểm tra (trong 120 giây hoặc cho đến khi bạn đóng Chrome)...")
                    for _ in range(120):
                        if not browser.is_connected() or (stop_event and stop_event.is_set()):
                            break
                        time.sleep(1)

            except Exception as e:
                result["success"] = False
                result["message"] = f"Lỗi trong quá trình thực thi: {str(e)}"
                log(f"❌ {result['message']}")
                try:
                    err_scr = "scratch/error_process.png"
                    page.screenshot(path=err_scr, full_page=True)
                    result["screenshot"] = err_scr
                except Exception:
                    pass
            finally:
                try:
                    if browser and browser.is_connected():
                        browser.close()
                except Exception:
                    pass

        return result

    def process_all_documents(
        self,
        doc_type: str = "CV Cảnh báo rủi ro",
        max_documents: Optional[int] = None,
        click_transfer: bool = True,
        headless: bool = False,
        stop_event=None,
        log_callback=None
    ) -> Dict[str, Any]:
        """Convenience method to process a single doc_type via process_workflow."""
        return self.process_workflow(
            doc_types=[doc_type],
            max_documents=max_documents,
            click_transfer=click_transfer,
            headless=headless,
            stop_event=stop_event,
            log_callback=log_callback
        )

    def process_all_risk_documents(
        self,
        max_documents: Optional[int] = None,
        click_transfer: bool = True,
        headless: bool = False,
        stop_event=None,
        log_callback=None
    ) -> Dict[str, Any]:
        """Convenience method to process risk documents."""
        return self.process_all_documents(
            doc_type="CV Cảnh báo rủi ro",
            max_documents=max_documents,
            click_transfer=click_transfer,
            headless=headless,
            stop_event=stop_event,
            log_callback=log_callback
        )
