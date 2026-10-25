# -*- coding: utf-8 -*-
"""
Dịch vụ tích hợp Telegram Bot (@BotFather) cho HB MIND AI & Tổng Thư Ký Cô Tấm.
Tự động gửi thông báo lịch làm việc (Google Calendar) và công việc (Google Tasks) đến CIO Bắc Nguyễn.
Hỗ trợ tương tác 2 chiều: Nhận tin nhắn từ CIO Bắc Nguyễn và phản hồi tự động như báo cáo của Cô Tấm.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import datetime
import threading
import time
from typing import Dict, Any, Optional

from config_manager import ConfigManager

class TelegramService:
    _polling_thread = None
    _is_polling = False
    _last_update_id = 0

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Lấy cấu hình Telegram Bot từ config.json"""
        full_cfg = ConfigManager.load_config()
        tg_cfg = full_cfg.get("telegram", {})
        return {
            "bot_token": tg_cfg.get("bot_token", ""),
            "chat_id": str(tg_cfg.get("chat_id", "")),
            "bot_username": tg_cfg.get("bot_username", ""),
            "bot_name": tg_cfg.get("bot_name", ""),
            "enabled": tg_cfg.get("enabled", True),
            "is_connected": bool(tg_cfg.get("bot_token") and tg_cfg.get("chat_id")),
            "last_tested": tg_cfg.get("last_tested"),
            "is_polling": cls._is_polling
        }

    @classmethod
    def save_config(cls, bot_token: str, chat_id: str, enabled: bool = True, bot_username: str = "", bot_name: str = "") -> Dict[str, Any]:
        """Lưu thông tin cấu hình Telegram Bot vào config.json"""
        full_cfg = ConfigManager.load_config()
        if "telegram" not in full_cfg or not isinstance(full_cfg["telegram"], dict):
            full_cfg["telegram"] = {}
        
        full_cfg["telegram"]["bot_token"] = bot_token.strip()
        full_cfg["telegram"]["chat_id"] = str(chat_id).strip()
        full_cfg["telegram"]["enabled"] = bool(enabled)
        if bot_username:
            full_cfg["telegram"]["bot_username"] = bot_username.strip()
        if bot_name:
            full_cfg["telegram"]["bot_name"] = bot_name.strip()
            
        success = ConfigManager.save_config(full_cfg)
        
        # Nếu bật cấu hình và có bot_token, khởi động polling nếu chưa chạy
        if enabled and bot_token.strip():
            cls.start_polling()

        return {
            "success": success,
            "message": "Đã lưu cấu hình Telegram Bot thành công!" if success else "Lỗi lưu cấu hình Telegram",
            "config": cls.get_config()
        }

    @classmethod
    def test_connection(cls, bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Kiểm tra kết nối Telegram Bot:
        1. Gọi getMe để xác minh Bot Token hợp lệ
        2. Nếu có Chat ID, gửi tin nhắn chào mừng thử nghiệm
        """
        cfg = cls.get_config()
        token = (bot_token or cfg.get("bot_token", "")).strip()
        cid = str(chat_id or cfg.get("chat_id", "")).strip()

        if not token:
            return {"success": False, "message": "Vui lòng nhập Bot Token từ @BotFather"}

        # 1. Kiểm tra Token qua getMe
        bot_info = None
        try:
            url_get_me = f"https://api.telegram.org/bot{token}/getMe"
            req = urllib.request.Request(url_get_me, headers={"User-Agent": "HBMind-Bot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not data.get("ok"):
                    return {"success": False, "message": f"Telegram API từ chối Token: {data.get('description')}"}
                bot_info = data.get("result", {})
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            try:
                err_json = json.loads(err_body)
                return {"success": False, "message": f"Lỗi Telegram: {err_json.get('description', str(he))}"}
            except Exception:
                return {"success": False, "message": f"Mã lỗi HTTP {he.code}: {err_body}"}
        except Exception as e:
            return {"success": False, "message": f"Không thể kết nối Telegram API: {str(e)}"}

        bot_name = bot_info.get("first_name", "Bot")
        bot_username = bot_info.get("username", "")

        # 2. Nếu có Chat ID, gửi tin nhắn thử nghiệm
        msg_result = None
        if cid:
            now_str = datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
            test_msg = (
                f"🎉 <b>HB MIND AI - KẾT NỐI TELEGRAM THÀNH CÔNG!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌸 <b>Tổng thư ký Cô Tấm</b> xin chào <b>CIO Bắc Nguyễn</b>!\n\n"
                f"🤖 <b>Bot Telegram:</b> @{bot_username} ({bot_name})\n"
                f"🆔 <b>Chat ID:</b> <code>{cid}</code>\n"
                f"🕒 <b>Thời gian kích hoạt:</b> {now_str}\n\n"
                f"✅ <i>Từ bây giờ, Sếp có thể nhắn tin trực tiếp cho em trên Telegram (ví dụ: 'lịch hôm nay', 'công việc', 'báo cáo' hoặc /lich, /task, /baocao), em sẽ báo cáo ngay cho Sếp ạ!</i>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Dạ, em xin báo cáo hết ạ! 🌺"
            )
            send_res = cls._raw_send_message(token, cid, test_msg)
            if not send_res.get("success"):
                return {
                    "success": False,
                    "message": f"Token hợp lệ (@{bot_username}) nhưng không thể gửi tin tới Chat ID {cid}: {send_res.get('message')}. Vui lòng mở Telegram tìm bot @{bot_username} và bấm /start trước!",
                    "bot_info": bot_info
                }
            msg_result = " và đã gửi tin nhắn thử nghiệm thành công tới Telegram của Sếp"

        # Cập nhật thông tin bot vào cấu hình
        cls.save_config(token, cid, enabled=True, bot_username=bot_username, bot_name=bot_name)
        full_cfg = ConfigManager.load_config()
        if "telegram" in full_cfg:
            full_cfg["telegram"]["last_tested"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            ConfigManager.save_config(full_cfg)

        # Kích hoạt lắng nghe tin nhắn
        cls.start_polling()

        return {
            "success": True,
            "message": f"Kết nối Bot @{bot_username} thành công{msg_result or ''}!",
            "bot_info": bot_info
        }

    @classmethod
    def _raw_send_message(cls, token: str, chat_id: str, text: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        """Gửi tin nhắn thô trực tiếp qua Telegram HTTP API"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, 
                data=data_bytes, 
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "HBMind-TelegramService/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return {"success": True, "result": res_json.get("result")}
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            try:
                err_dict = json.loads(err_body)
                desc = err_dict.get("description", str(he))
                return {"success": False, "message": desc}
            except Exception:
                return {"success": False, "message": err_body or str(he)}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @classmethod
    def send_message(cls, text: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        """Gửi tin nhắn Telegram sử dụng cấu hình đã lưu trong hệ thống"""
        cfg = cls.get_config()
        if not cfg.get("enabled", True):
            return {"success": False, "message": "Thông báo Telegram đang ở trạng thái Tắt."}

        token = cfg.get("bot_token", "").strip()
        cid = cfg.get("chat_id", "").strip()
        if not token or not cid:
            return {"success": False, "message": "Chưa thiết lập Bot Token hoặc Chat ID trong Thiết lập chung."}

        return cls._raw_send_message(token, cid, text, parse_mode=parse_mode)

    @classmethod
    def send_chief_briefing(
        cls,
        briefing_type: str = "all",
        custom_intro: Optional[str] = None,
        cal_range: Optional[str] = None,
        task_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gửi báo cáo công việc của Tổng Thư Ký Cô Tấm đến Telegram:
        - Chỉ báo cáo đối với những lịch làm việc nào CHƯA DIỄN RA.
        - Chỉ báo cáo đối với những công việc nào TRONG PHẠM VI THIẾT LẬP mà CHƯA HOÀN THÀNH.
        """
        cfg = cls.get_config()
        if not cfg.get("enabled", True) or not cfg.get("bot_token") or not cfg.get("chat_id"):
            return {"success": False, "skipped": True, "message": "Telegram chưa được cấu hình hoặc đã tắt."}

        try:
            from chief_secretary_service import ChiefSecretaryService
        except Exception as e:
            return {"success": False, "message": f"Không thể tải ChiefSecretaryService: {e}"}

        chief_cfg = ChiefSecretaryService.get_config()
        remind_cal = chief_cfg.get("remind_calendar", True)
        remind_tasks = chief_cfg.get("remind_tasks", True)

        now_dt = datetime.datetime.now()
        now_str = now_dt.strftime("%H:%M - %d/%m/%Y")

        eff_cal_range = (cal_range or chief_cfg.get("calendar_scope") or "today").strip().lower()
        eff_task_range = (task_range or chief_cfg.get("task_scope") or "today").strip().lower()
        if eff_task_range == "completed":
            eff_task_range = (chief_cfg.get("task_scope") or "today").strip().lower()
            if eff_task_range == "completed":
                eff_task_range = "today"

        # Lấy dữ liệu lịch chưa diễn ra
        cal_data = ChiefSecretaryService.get_calendar_events(eff_cal_range)
        raw_events = cal_data.get("events", [])
        upcoming_events = [ev for ev in raw_events if ChiefSecretaryService._is_event_upcoming(ev, now_dt)]

        # Lấy dữ liệu công việc trong phạm vi thiết lập mà chưa hoàn thành
        task_data = ChiefSecretaryService.get_tasks(eff_task_range)
        raw_tasks = task_data.get("tasks", [])
        pending_tasks = [t for t in raw_tasks if isinstance(t, dict) and not t.get("completed", False)]

        # Xây dựng nội dung tin nhắn Telegram HTML
        lines = []
        lines.append("🌸 <b>TỔNG THƯ KÝ CÔ TẤM BÁO CÁO CIO BẮC NGUYỄN</b>")
        lines.append(f"🕒 <i>Thời điểm: {now_str}</i>")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # 1. Phần Lịch làm việc chưa diễn ra (Google Calendar)
        include_cal = remind_cal and (briefing_type in ("calendar", "calendar_only", "all", "morning"))
        if include_cal:
            lines.append("📆 <b>LỊCH LÀM VIỆC CHƯA DIỄN RA (GOOGLE CALENDAR):</b>")
            if upcoming_events:
                for ev in upcoming_events:
                    st = ev.get("start_time") or ev.get("time") or "08:30"
                    et = f" - {ev['end_time']}" if ev.get("end_time") else ""
                    loc = f" <i>({ev['location']})</i>" if ev.get("location") else ""
                    lines.append(f" • <b>{st}{et}</b>: {ev.get('title')}{loc}")
            else:
                lines.append(" • <i>Hiện không còn lịch hẹn nào chưa diễn ra trên Google Calendar.</i>")
            lines.append("")

        # 2. Phần Công việc chưa hoàn thành trong phạm vi thiết lập (Google Tasks)
        include_tasks = remind_tasks and (briefing_type in ("tasks", "tasks_only", "all", "morning"))
        if include_tasks:
            lines.append("📋 <b>CÔNG VIỆC CHƯA HOÀN THÀNH TRONG PHẠM VI THIẾT LẬP:</b>")
            if pending_tasks:
                for t in pending_tasks:
                    dt = f" [Hạn: {t['due_time']}]" if t.get("due_time") else ""
                    cat = f" <i>[{t['category']}]</i>" if t.get("category") else ""
                    lines.append(f" • <b>{t.get('title')}</b>{dt}{cat}")
            else:
                lines.append(" • <i>Không có công việc nào chưa hoàn thành trong phạm vi thiết lập.</i>")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        intro = chief_cfg.get("opening_phrase", "Dạ, em xin báo cáo Sếp Bắc")
        outro = chief_cfg.get("closing_phrase", "Em báo cáo hết ạ")
        lines.append(f"💬 <i>\"{intro}. Chúc Sếp một ngày làm việc tràn đầy năng lượng và hiệu quả. {outro}!\"</i> 🌺")

        message_html = "\n".join(lines)
        return cls.send_message(message_html)

    # =========================================================================
    # TƯƠNG TÁC 2 CHIỀU: LẮNG NGHE & PHẢN HỒI TIN NHẮN TỪ TELEGRAM CỦA SẾP
    # =========================================================================
    @classmethod
    def start_polling(cls) -> bool:
        """Khởi động luồng nền lắng nghe tin nhắn từ Telegram Bot (Long Polling)"""
        if cls._is_polling and cls._polling_thread and cls._polling_thread.is_alive():
            return True

        cfg = cls.get_config()
        if not cfg.get("enabled", True) or not cfg.get("bot_token"):
            return False

        cls._is_polling = True
        cls._polling_thread = threading.Thread(
            target=cls._polling_worker,
            daemon=True,
            name="TelegramBotPoller"
        )
        cls._polling_thread.start()
        print(f"[TelegramService] Đã kích hoạt luồng nền lắng nghe Telegram Bot @{cfg.get('bot_username', 'Bot')}")
        return True

    @classmethod
    def stop_polling(cls):
        """Dừng luồng lắng nghe Telegram"""
        cls._is_polling = False

    @classmethod
    def _polling_worker(cls):
        """Worker chạy ngầm liên tục gọi getUpdates để nhận tin nhắn từ Telegram"""
        while cls._is_polling:
            try:
                cfg = cls.get_config()
                token = cfg.get("bot_token", "").strip()
                if not token or not cfg.get("enabled", True):
                    time.sleep(5)
                    continue

                url = f"https://api.telegram.org/bot{token}/getUpdates?offset={cls._last_update_id + 1}&timeout=10"
                req = urllib.request.Request(url, headers={"User-Agent": "HBMind-Bot/1.0"})
                
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("ok"):
                        updates = data.get("result", [])
                        for update in updates:
                            cls._last_update_id = update["update_id"]
                            cls._handle_incoming_update(update, token)

            except urllib.error.HTTPError as he:
                time.sleep(4)
            except Exception as e:
                time.sleep(3)

    @classmethod
    def _handle_incoming_update(cls, update: Dict[str, Any], token: str):
        """Xử lý từng update tin nhắn đến từ người dùng Telegram"""
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            return

        chat = msg.get("chat", {})
        chat_id = str(chat.get("id", ""))
        user = msg.get("from", {})
        user_name = user.get("first_name", "Sếp")
        raw_text = msg.get("text", "").strip()

        if not raw_text or not chat_id:
            return

        # Tự động ghim chat_id nếu cấu hình chưa có hoặc người dùng gửi /start
        cfg = cls.get_config()
        saved_cid = cfg.get("chat_id", "").strip()
        if not saved_cid or raw_text.startswith("/start"):
            cls.save_config(token, chat_id, enabled=True, bot_username=cfg.get("bot_username", ""), bot_name=cfg.get("bot_name", ""))

        # Phân tích ý định câu hỏi và trả lời qua Cô Tấm
        reply_html = cls._build_chief_reply(raw_text, user_name)
        if reply_html:
            cls._raw_send_message(token, chat_id, reply_html)

    @classmethod
    def _build_chief_reply(cls, text: str, user_name: str) -> str:
        """Tạo nội dung câu trả lời chuẩn xác của Tổng Thư Ký Cô Tấm dựa theo tin nhắn của Sếp"""
        txt = text.lower().strip()
        
        try:
            from chief_secretary_service import ChiefSecretaryService
        except Exception:
            ChiefSecretaryService = None

        now_str = datetime.datetime.now().strftime("%H:%M - %d/%m/%Y")

        # 1. Lệnh chào mừng hoặc trợ giúp: /start, /help, chào, hi, hello
        if txt in ("/start", "/help", "chào", "chào em", "chào cô tấm", "xin chào", "hello", "hi", "help"):
            return (
                f"🌸 <b>DẠ, EM LÀ TỔNG THƯ KÝ CÔ TẤM KÍNH CHÀO SẾP BẮC!</b> 🌺\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Em luôn túc trực hỗ trợ nhắc việc và báo cáo lịch trình cho Sếp. Sếp có thể nhắn bất kỳ câu nào sau đây:\n\n"
                f"📆 <b>/lich</b> hoặc <i>\"lịch hôm nay\"</i>: Báo cáo các cuộc họp Google Calendar hôm nay.\n"
                f"📋 <b>/task</b> hoặc <i>\"công việc hôm nay\"</i>: Báo cáo nhiệm vụ Google Tasks cần xử lý.\n"
                f"📑 <b>/baocao</b> hoặc <i>\"báo cáo\"</i>: Báo cáo toàn bộ lịch trình và công việc hôm nay.\n\n"
                f"💡 Sếp cũng có thể nhắn tự nhiên như: <i>'hôm nay có việc gì không em'</i>, <i>'lịch làm việc'</i>... Em sẵn sàng phục vụ Sếp ạ! ✨"
            )

        # 2. Phân loại ý định:
        is_calendar_query = any(k in txt for k in ["/lich", "lịch", "lich", "calendar", "họp", "hop", "meeting", "lịch trình", "lich trinh"])
        is_task_query = any(k in txt for k in ["/task", "công việc", "cong viec", "task", "việc", "viec", "nhiệm vụ", "nhiem vu", "deadline"])
        is_full_report_query = any(k in txt for k in ["/baocao", "báo cáo", "bao cao", "tất cả", "tat ca", "toàn bộ", "tổng hợp", "tong hop", "briefing", "overview"])

        # Nếu chỉ hỏi lịch làm việc (không chứa từ khóa công việc)
        if is_calendar_query and not is_task_query and not is_full_report_query:
            cal_mode = True
        elif is_task_query and not is_calendar_query and not is_full_report_query:
            task_mode = True
        else:
            # Báo cáo cả hai nếu hỏi báo cáo, cả hai hoặc câu hỏi tổng quan
            is_full_report_query = True

        if is_full_report_query:
            if not ChiefSecretaryService:
                return "Dạ, hệ thống đang bận cập nhật dữ liệu. Xin Sếp đợi trong giây lát ạ."
            
            now_dt = datetime.datetime.now()
            chief_cfg = ChiefSecretaryService.get_config()
            eff_cal_range = (chief_cfg.get("calendar_scope") or "today").strip().lower()
            eff_task_range = (chief_cfg.get("task_scope") or "today").strip().lower()
            if eff_task_range == "completed":
                eff_task_range = "today"

            cal_data = ChiefSecretaryService.get_calendar_events(eff_cal_range)
            task_data = ChiefSecretaryService.get_tasks(eff_task_range)
            today_events = [ev for ev in cal_data.get("events", []) if ChiefSecretaryService._is_event_upcoming(ev, now_dt)]
            today_tasks = [t for t in task_data.get("tasks", []) if isinstance(t, dict) and not t.get("completed", False)]

            lines = [
                f"🌸 <b>TỔNG THƯ KÝ CÔ TẤM - BÁO CÁO TOÀN DIỆN CHO CIO BẮC NGUYỄN</b>",
                f"🕒 <i>Thời điểm: {now_str}</i>",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"📆 <b>LỊCH LÀM VIỆC CHƯA DIỄN RA ({len(today_events)} lịch):</b>"
            ]
            if today_events:
                for ev in today_events:
                    st = ev.get("start_time") or ev.get("time") or "08:30"
                    et = f" - {ev['end_time']}" if ev.get("end_time") else ""
                    loc = f" <i>({ev['location']})</i>" if ev.get("location") else ""
                    lines.append(f" • <b>{st}{et}</b>: {ev.get('title')}{loc}")
            else:
                lines.append(" • <i>Hiện không còn lịch hẹn nào chưa diễn ra trên Google Calendar.</i>")
            
            lines.append("")
            lines.append(f"📋 <b>CÔNG VIỆC CHƯA HOÀN THÀNH ({len(today_tasks)} việc):</b>")
            if today_tasks:
                for t in today_tasks:
                    dt = f" [Hạn: {t['due_time']}]" if t.get("due_time") else ""
                    lines.append(f" • <b>{t.get('title')}</b>{dt}")
            else:
                lines.append(" • <i>Không có công việc nào chưa hoàn thành trong phạm vi thiết lập.</i>")

            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            ev_summary = f"{len(today_events)} lịch làm việc chưa diễn ra" if today_events else "không còn lịch làm việc chưa diễn ra"
            task_summary = f"{len(today_tasks)} công việc chưa hoàn thành" if today_tasks else "không có công việc tồn đọng"
            lines.append(f"💬 <i>\"Dạ, em xin báo cáo Sếp Bắc, hiện tại Sếp có {ev_summary} và {task_summary}. Chúc Sếp làm việc thuận lợi và hiệu quả! Em báo cáo hết ạ.\"</i> 🌺")
            return "\n".join(lines)

        # Nếu chỉ hỏi lịch làm việc
        if is_calendar_query:
            if not ChiefSecretaryService:
                return "Dạ, em chưa kết nối được dữ liệu Google Calendar. Sếp kiểm tra lại giúp em nhé."
            now_dt = datetime.datetime.now()
            chief_cfg = ChiefSecretaryService.get_config()
            eff_cal_range = (chief_cfg.get("calendar_scope") or "today").strip().lower()
            cal_data = ChiefSecretaryService.get_calendar_events(eff_cal_range)
            today_events = [ev for ev in cal_data.get("events", []) if ChiefSecretaryService._is_event_upcoming(ev, now_dt)]
            lines = [
                f"🌸 <b>TỔNG THƯ KÝ CÔ TẤM - BÁO CÁO LỊCH LÀM VIỆC CHƯA DIỄN RA</b>",
                f"🕒 <i>Thời điểm: {now_str}</i>",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"📆 <b>GOOGLE CALENDAR CỦA SẾP BẮC ({len(today_events)} lịch chưa diễn ra):</b>"
            ]
            if today_events:
                ev_descs = []
                for ev in today_events:
                    st = ev.get("start_time") or ev.get("time") or "08:30"
                    et = f" - {ev['end_time']}" if ev.get("end_time") else ""
                    loc = f" <i>({ev['location']})</i>" if ev.get("location") else ""
                    lines.append(f" • <b>{st}{et}</b>: {ev.get('title')}{loc}")
                    ev_descs.append(f"lúc {st} {ev.get('title')}")
                lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                lines.append(f"💬 <i>\"Dạ, em xin báo cáo Sếp Bắc, hiện sếp có {len(today_events)} lịch làm việc chưa diễn ra trên Google Calendar: {'; '.join(ev_descs)}. Em báo cáo hết ạ.\"</i> 🌺")
            else:
                lines.append(" • <i>Hiện Sếp không còn lịch hẹn nào chưa diễn ra trên Google Calendar.</i>")
                lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                lines.append(f"💬 <i>\"Dạ, em xin báo cáo Sếp Bắc, hiện Sếp không còn lịch làm việc nào chưa diễn ra trên Google Calendar ạ. Em báo cáo hết ạ.\"</i> 🌺")
            return "\n".join(lines)

        # Nếu chỉ hỏi công việc
        if is_task_query:
            if not ChiefSecretaryService:
                return "Dạ, em chưa kết nối được dữ liệu Google Tasks. Sếp kiểm tra lại giúp em nhé."
            chief_cfg = ChiefSecretaryService.get_config()
            eff_task_range = (chief_cfg.get("task_scope") or "today").strip().lower()
            if eff_task_range == "completed":
                eff_task_range = "today"
            task_data = ChiefSecretaryService.get_tasks(eff_task_range)
            today_tasks = [t for t in task_data.get("tasks", []) if isinstance(t, dict) and not t.get("completed", False)]
            lines = [
                f"🌸 <b>TỔNG THƯ KÝ CÔ TẤM - BÁO CÁO NHIỆM VỤ CHƯA HOÀN THÀNH</b>",
                f"🕒 <i>Thời điểm: {now_str}</i>",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"📋 <b>GOOGLE TASKS CHƯA HOÀN THÀNH ({len(today_tasks)} việc):</b>"
            ]
            if today_tasks:
                task_descs = []
                for t in today_tasks:
                    dt = f" [Hạn: {t['due_time']}]" if t.get("due_time") else ""
                    lines.append(f" • <b>{t.get('title')}</b>{dt}")
                    time_pfx = f"lúc {t.get('due_time')} " if t.get("due_time") else ""
                    task_descs.append(f"{time_pfx}{t.get('title')}")
                lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                lines.append(f"💬 <i>\"Dạ, em xin báo cáo Sếp Bắc, trong phạm vi thiết lập sếp có {len(today_tasks)} công việc chưa hoàn thành cần xử lý: {'; '.join(task_descs)}. Em báo cáo hết ạ.\"</i> 🌺")
            else:
                lines.append(" • <i>Trong phạm vi thiết lập, Sếp không có công việc nào chưa hoàn thành.</i>")
                lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                lines.append(f"💬 <i>\"Dạ, em xin báo cáo Sếp Bắc, trong phạm vi thiết lập sếp không có công việc nào chưa hoàn thành trên Google Tasks ạ. Em báo cáo hết ạ.\"</i> 🌺")
            return "\n".join(lines)

        # Câu hỏi tự nhiên khác
        return (
            f"🌸 <b>Tổng thư ký Cô Tấm:</b>\n"
            f"Dạ, em xin báo cáo Sếp Bắc! Em đã ghi nhận tin nhắn của Sếp: <i>\"{text}\"</i>.\n\n"
            f"Sếp có thể nhắn nhanh cho em bất kỳ lúc nào:\n"
            f"• <b>/lich</b> hoặc <i>'lịch hôm nay'</i>: Tra cứu lịch họp Google Calendar\n"
            f"• <b>/task</b> hoặc <i>'công việc'</i>: Tra cứu nhiệm vụ Google Tasks\n"
            f"• <b>/baocao</b> hoặc <i>'báo cáo'</i>: Báo cáo tổng thể cả lịch trình và công việc\n\n"
            f"Dạ, em luôn túc trực phục vụ Sếp Bắc ạ! 🌺"
        )
