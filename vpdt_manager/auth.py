"""
Authentication and Session Manager for VPDT Portal
Handles automated login, session persistence, and login validation.
"""

import sys
import os
import time
from typing import Dict, Any, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from vpdt_manager.config import (
    LOGIN_URL,
    BASE_URL,
    SESSION_FILE,
    SCREENSHOT_PATH,
    load_config,
)


class VPDTAuthenticator:
    """Manages login and session storage for the VPDT Liferay Portal."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        headless: Optional[bool] = None,
        save_session: bool = True,
        keep_open: bool = True,
        stop_event: Optional[Any] = None,
        on_success_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Automates login into VPDT system.
        If keep_open is True and headless is False, keeps the browser open indefinitely.
        """
        user = username or self.config.get("username", "")
        pwd = password or self.config.get("password", "")
        is_headless = headless if headless is not None else self.config.get("headless", False)
        slow_mo = self.config.get("browser_slow_mo_ms", 300)
        timeout = self.config.get("default_timeout_ms", 30000)

        if not user or not pwd:
            return {
                "success": False,
                "message": "Tên đăng nhập hoặc mật khẩu chưa được cung cấp.",
                "current_url": "",
                "screenshot_path": ""
            }

        result = {
            "success": False,
            "message": "",
            "current_url": "",
            "screenshot_path": str(SCREENSHOT_PATH)
        }

        with sync_playwright() as p:
            # Launch existing Chrome or Edge on Windows
            browser = None
            for ch in ["chrome", "msedge", None]:
                try:
                    kwargs = {
                        "headless": is_headless,
                        "slow_mo": slow_mo,
                        "args": ["--start-maximized", "--ignore-certificate-errors"]
                    }
                    if ch:
                        kwargs["channel"] = ch
                    browser = p.chromium.launch(**kwargs)
                    print(f"[VPDT Auth] Đã mở trình duyệt ({ch or 'chromium default'}) thành công.")
                    break
                except Exception as ex:
                    print(f"[VPDT Auth] Thử mở trình duyệt {ch} không thành công: {ex}, đang thử kênh khác...")

            if not browser:
                result["message"] = "Không thể khởi động trình duyệt Chrome hoặc Edge trên máy."
                return result
            context: BrowserContext = browser.new_context(
                no_viewport=True,
                ignore_https_errors=True
            )
            page: Page = context.new_page()
            page.set_default_timeout(timeout)

            try:
                print(f"[VPDT Auth] Đang mở trang đăng nhập: {LOGIN_URL}...")
                page.goto(LOGIN_URL, wait_until="domcontentloaded")

                # Locate login form inputs
                print("[VPDT Auth] Đang tìm các trường đăng nhập...")
                user_input = page.locator("#_58_login, input[name='_58_login']").first
                pass_input = page.locator("#_58_password, input[name='_58_password']").first
                submit_btn = page.locator("input[type='submit'][value*='Đăng nhập'], #_58_fm input[type='submit']").first

                user_input.wait_for(state="visible", timeout=15000)
                pass_input.wait_for(state="visible", timeout=15000)

                # Fill credentials
                print(f"[VPDT Auth] Đang điền tên đăng nhập: {user}")
                user_input.fill(user)
                time.sleep(0.3)

                print("[VPDT Auth] Đang điền mật khẩu...")
                pass_input.fill(pwd)
                time.sleep(0.5)

                # Fix Liferay Tomcat jsessionid bug: remove ;jsessionid=... from form action if present
                page.evaluate("""() => {
                    const fm = document.getElementById('_58_fm');
                    if (fm && fm.action.includes(';jsessionid=')) {
                        fm.action = fm.action.replace(/;jsessionid=[^?&]+/, '');
                    }
                }""")

                # Submit form
                print("[VPDT Auth] Đang gửi yêu cầu đăng nhập...")
                if submit_btn.is_visible():
                    submit_btn.click()
                else:
                    pass_input.press("Enter")

                # Wait for post-login navigation or response
                time.sleep(4)
                try:
                    page.wait_for_load_state("networkidle", timeout=12000)
                except Exception:
                    pass

                result["current_url"] = page.url

                # Check for login errors in portal
                error_alert = page.locator(
                    ".portlet-msg-error, .alert-error, .alert-danger, span:text-matches('không đúng', 'i'), span:text-matches('thất bại', 'i')"
                )
                if error_alert.count() > 0 and error_alert.first.is_visible():
                    err_text = error_alert.first.inner_text().strip()
                    result["success"] = False
                    result["message"] = f"Đăng nhập thất bại từ hệ thống: {err_text}"
                    page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
                    print(f"[VPDT Auth] {result['message']}")
                    return result

                # Check if still on login form
                has_login_input = page.locator("#_58_login").count() > 0
                body_signed_in = page.locator("body.signed-in").count() > 0
                has_workspace = "/group/" in page.url or page.locator("text='Văn bản đến'").count() > 0

                if body_signed_in or (has_workspace and not has_login_input):
                    result["success"] = True
                    result["message"] = "Đăng nhập thành công vào hệ thống VPDT!"
                    print(f"[VPDT Auth] {result['message']} URL hiện tại: {page.url}")

                    # Save screenshot of dashboard
                    page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
                    print(f"[VPDT Auth] Đã lưu ảnh chụp màn hình bàn làm việc vào: {SCREENSHOT_PATH}")

                    # Save storage state for session reuse
                    if save_session:
                        context.storage_state(path=str(SESSION_FILE))
                        print(f"[VPDT Auth] Đã lưu phiên làm việc (Session & Cookies) vào: {SESSION_FILE}")

                    # Notify caller immediately if callback provided
                    if on_success_callback:
                        try:
                            on_success_callback(result)
                        except Exception as cb_err:
                            print(f"[VPDT Auth] Lỗi callback: {cb_err}")

                    # KEEP BROWSER OPEN: If headed mode, keep the browser interface open
                    if not is_headless and keep_open:
                        print("[VPDT Auth] 🟢 Đã giữ nguyên giao diện trình duyệt mở để bạn tiếp tục thao tác!")
                        if stop_event is not None:
                            while not stop_event.is_set() and browser.is_connected():
                                time.sleep(0.3)
                        else:
                            # Standalone CLI mode
                            print("[VPDT Auth] Nhấn phím Enter (hoặc đóng cửa sổ trình duyệt) để kết thúc...")
                            try:
                                while browser.is_connected():
                                    time.sleep(0.5)
                            except (KeyboardInterrupt, EOFError):
                                pass
                else:
                    result["success"] = False
                    result["message"] = "Đăng nhập chưa thành công, hệ thống chưa vào bàn làm việc chính."
                    page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
                    print(f"[VPDT Auth] {result['message']}")

            except Exception as e:
                result["success"] = False
                result["message"] = f"Lỗi trong quá trình đăng nhập: {str(e)}"
                try:
                    page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
                except Exception:
                    pass
                print(f"[VPDT Auth] Lỗi: {e}")

            finally:
                try:
                    if browser and browser.is_connected():
                        browser.close()
                except Exception:
                    pass

        return result

    def is_session_valid(self, headless: bool = True) -> bool:
        """Checks if saved session_state.json is still valid and authenticated."""
        if not SESSION_FILE.exists():
            return False

        with sync_playwright() as p:
            browser = None
            for ch in ["chrome", "msedge", None]:
                try:
                    kwargs = {"headless": headless, "args": ["--ignore-certificate-errors"]}
                    if ch:
                        kwargs["channel"] = ch
                    browser = p.chromium.launch(**kwargs)
                    break
                except Exception:
                    continue

            if not browser:
                return False
            try:
                context = browser.new_context(
                    storage_state=str(SESSION_FILE),
                    ignore_https_errors=True
                )
                page = context.new_page()
                page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)

                # Check if signed-in or redirected to login
                if "/web/guest/login" in page.url:
                    return False

                body_signed_in = page.locator("body.signed-in")
                return body_signed_in.count() > 0 or "/login" not in page.url
            except Exception:
                return False
            finally:
                browser.close()
