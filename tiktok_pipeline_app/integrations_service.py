import os
import json
import requests
from typing import Dict, Any, Tuple
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "integrations_config.json")

DEFAULT_INTEGRATIONS = {
    "telegram": {
        "bot_token": "",
        "chat_id": "",
        "bot_name": "",
        "is_connected": False,
        "last_tested": None
    },
    "heygen": {
        "api_key": "",
        "avatar_id": "",
        "voice_id": "",
        "is_connected": False,
        "last_tested": None
    },
    "elevenlabs": {
        "api_key": "",
        "voice_id": "",
        "model_id": "eleven_multilingual_v2",
        "is_connected": False,
        "last_tested": None
    },
    "tiktok": {
        "access_token": "",
        "username": "",
        "client_key": "",
        "client_secret": "",
        "public_base_url": "",
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "display_name": "",
        "open_id": "",
        "avatar_url": "",
        "is_connected": False,
        "last_tested": None
    }
}


def load_integrations_config() -> Dict[str, Any]:
    """Tải cấu hình các nền tảng từ file integrations_config.json"""
    cfg = DEFAULT_INTEGRATIONS.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for k, v in saved.items():
                    if k in cfg and isinstance(v, dict):
                        cfg[k].update(v)
                    else:
                        cfg[k] = v
        except Exception as e:
            print(f"[Integrations] Lỗi đọc config: {e}")
    return cfg


def save_integrations_config(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Lưu cấu hình các nền tảng vào file json để duy trì phiên làm việc vĩnh viễn"""
    try:
        current = load_integrations_config()
        for k, v in data.items():
            if k in current and isinstance(v, dict):
                current[k].update(v)
            else:
                current[k] = v

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return True, "Đã lưu cấu hình kết nối thành công!"
    except Exception as e:
        return False, f"Lỗi lưu cấu hình: {str(e)}"


def mask_key(k: str) -> str:
    """Ẩn bớt ký tự khóa để bảo mật"""
    if not k:
        return ""
    if len(k) <= 8:
        return "********"
    return k[:4] + "..." + k[-4:]


# =========================================================
# KIỂM TRA KẾT NỐI CHO TỪNG NỀN TẢNG
# =========================================================

def test_telegram_connection(bot_token: str, chat_id: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    """Kiểm tra bot token Telegram và gửi tin nhắn kiểm tra nếu có chat_id"""
    token = (bot_token or "").strip()
    if not token:
        return False, "Vui lòng nhập Telegram Bot Token!", {}

    try:
        # 1. getMe để kiểm tra tính hợp lệ của token
        me_url = f"https://api.telegram.org/bot{token}/getMe"
        resp = requests.get(me_url, timeout=15)
        if resp.status_code != 200:
            return False, f"Token Telegram không hợp lệ (Mã {resp.status_code}): {resp.text}", {}

        me_data = resp.json()
        if not me_data.get("ok"):
            return False, f"Lỗi Telegram: {me_data.get('description')}", {}

        bot_info = me_data.get("result", {})
        bot_name = bot_info.get("first_name", "")
        bot_username = bot_info.get("username", "")

        msg_detail = f"Bot: {bot_name} (@{bot_username})"

        # 2. Nếu có chat_id, gửi thử 1 tin nhắn test
        c_id = (chat_id or "").strip()
        if c_id:
            send_url = f"https://api.telegram.org/bot{token}/sendMessage"
            send_payload = {
                "chat_id": c_id,
                "text": "🎉 [TikTok Automation Studio] Kết nối Telegram thành công!\nSẵn sàng nhận thông báo duyệt chủ đề và duyệt video.",
                "parse_mode": "HTML"
            }
            send_resp = requests.post(send_url, json=send_payload, timeout=15)
            if send_resp.status_code == 200:
                msg_detail += " | Đã gửi tin nhắn xác nhận đến Chat ID thành công!"
            else:
                msg_detail += f" | Lưu ý: Không gửi được tin tới Chat ID ({send_resp.text})"

        # Tự động lưu trạng thái kết nối thành công
        save_integrations_config({
            "telegram": {
                "bot_token": token,
                "chat_id": c_id,
                "bot_name": f"@{bot_username}" if bot_username else bot_name,
                "is_connected": True,
                "last_tested": datetime.now().isoformat()
            }
        })

        return True, f"Kết nối Telegram thành công! {msg_detail}", {
            "bot_name": bot_name,
            "username": bot_username
        }
    except Exception as e:
        return False, f"Lỗi kết nối Telegram: {str(e)}", {}


def test_heygen_connection(api_key: str, avatar_id: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    """Kiểm tra HeyGen API Key qua HeyGen v3 API"""
    key = (api_key or "").strip()
    if not key:
        return False, "Vui lòng nhập HeyGen API Key!", {}

    if key.startswith("AIzaSy"):
        return False, "Khóa này là mã Google Gemini API Key (bắt đầu bằng 'AIzaSy...'), không phải HeyGen API Key! Khóa HeyGen thường bắt đầu bằng 'sk_...'. Vui lòng kiểm tra lại tại https://app.heygen.com/settings?nav=API", {}

    try:
        # Gọi HeyGen v3 User Me endpoint
        headers = {
            "X-Api-Key": key,
            "Accept": "application/json"
        }
        url = "https://api.heygen.com/v3/users/me"
        resp = requests.get(url, headers=headers, timeout=15)

        # Fallback thử endpoint v2 remaining_quota nếu cần
        if resp.status_code != 200:
            url_v2 = "https://api.heygen.com/v2/user/remaining_quota"
            resp_v2 = requests.get(url_v2, headers=headers, timeout=15)
            if resp_v2.status_code == 200:
                resp = resp_v2

        if resp.status_code in [401, 403]:
            return False, "HeyGen API Key không chính xác hoặc đã hết hạn! Vui lòng kiểm tra tại HeyGen Console.", {}
        elif resp.status_code != 200:
            return False, f"Lỗi gọi HeyGen API ({resp.status_code}): {resp.text}", {}

        data = resp.json().get("data", {})
        email = data.get("email", "")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        user_display = f"{first_name} {last_name}".strip() or email or "Tài khoản HeyGen"

        wallet = data.get("wallet", {})
        rem_balance = wallet.get("remaining_balance", 0.0) if isinstance(wallet, dict) else 0.0
        curr = (wallet.get("currency") or "usd").upper() if isinstance(wallet, dict) else "USD"

        info_msg = f"Tài khoản: {user_display} ({email})"
        if rem_balance is not None:
            info_msg += f" | Số dư ví: {rem_balance} {curr}"

        # Lưu trạng thái kết nối thành công
        save_integrations_config({
            "heygen": {
                "api_key": key,
                "avatar_id": avatar_id.strip() or "HCMTax",
                "user_name": user_display,
                "user_email": email,
                "is_connected": True,
                "last_tested": datetime.now().isoformat()
            }
        })

        return True, f"Kết nối HeyGen thành công! ({info_msg})", {
            "user_name": user_display,
            "email": email,
            "remaining_balance": rem_balance
        }
    except Exception as e:
        return False, f"Lỗi kết nối HeyGen: {str(e)}", {}


def test_elevenlabs_connection(api_key: str, voice_id: str = "", model_id: str = "eleven_multilingual_v2") -> Tuple[bool, str, Dict[str, Any]]:
    """Kiểm tra ElevenLabs API Key và lấy thông tin gói tài khoản hoặc danh sách giọng đọc"""
    key = (api_key or "").strip()
    if not key:
        return False, "Vui lòng nhập ElevenLabs API Key!", {}

    try:
        headers = {"xi-api-key": key, "Accept": "application/json"}

        # 1. Thử gọi API subscription (lấy thông tin hạn mức gói tài khoản)
        url_sub = "https://api.elevenlabs.io/v1/user/subscription"
        resp_sub = requests.get(url_sub, headers=headers, timeout=15)

        info_str = ""
        tier = "active"
        character_count = 0
        character_limit = 0
        voice_count = 0

        if resp_sub.status_code == 200:
            sub = resp_sub.json()
            tier = sub.get("tier", "unknown")
            character_count = sub.get("character_count", 0)
            character_limit = sub.get("character_limit", 0)
            info_str = f"Gói: {tier.upper()} | Đã dùng: {character_count:,}/{character_limit:,} ký tự"
        else:
            # 2. Nếu API Key có quyền phân cấp (thiếu user_read), xác thực qua Voice Library
            url_voices = "https://api.elevenlabs.io/v1/voices"
            resp_voices = requests.get(url_voices, headers=headers, timeout=15)

            if resp_voices.status_code == 200:
                voices_data = resp_voices.json().get("voices", [])
                voice_count = len(voices_data)
                info_str = f"Xác thực hợp lệ | Sẵn sàng {voice_count} giọng đọc AI"
            else:
                if resp_voices.status_code in [401, 403]:
                    err_msg = "ElevenLabs API Key không chính xác hoặc không có quyền truy cập!"
                    try:
                        err_json = resp_voices.json()
                        if "detail" in err_json and isinstance(err_json["detail"], dict):
                            err_msg += f" ({err_json['detail'].get('message', '')})"
                    except Exception:
                        pass
                    return False, err_msg, {}
                return False, f"Lỗi gọi ElevenLabs API ({resp_voices.status_code}): {resp_voices.text}", {}

        # Lưu trạng thái kết nối thành công
        save_integrations_config({
            "elevenlabs": {
                "api_key": key,
                "voice_id": voice_id.strip(),
                "model_id": model_id.strip() if model_id else "eleven_multilingual_v2",
                "is_connected": True,
                "last_tested": datetime.now().isoformat()
            }
        })

        return True, f"Kết nối ElevenLabs thành công! ({info_str})", {
            "tier": tier,
            "character_count": character_count,
            "character_limit": character_limit,
            "voice_count": voice_count
        }
    except Exception as e:
        return False, f"Lỗi kết nối ElevenLabs: {str(e)}", {}


def test_gemini_connection(api_key: str, model: str = "gemini-2.5-flash") -> Tuple[bool, str, Dict[str, Any]]:
    """Kiểm tra Gemini API Key"""
    from gemini_content_service import call_gemini_generate, save_gemini_config
    key = (api_key or "").strip()
    if not key:
        return False, "Vui lòng nhập Gemini API Key!", {}

    test_cfg = {
        "api_key": key,
        "model": model or "gemini-2.5-flash",
        "enable_web_search": False
    }

    success, text, _ = call_gemini_generate("Hãy phản hồi chính xác 4 chữ: 'Gemini sẵn sàng'", test_cfg)
    if success:
        save_gemini_config({"api_key": key, "model": model})
        return True, f"Kết nối Gemini thành công! (Mô hình: {model})", {"response": text}
    else:
        return False, f"Kiểm tra Gemini thất bại: {text}", {}


def test_tiktok_connection(access_token: str = "", username: str = "", client_key: str = "", client_secret: str = "", privacy_level: str = "PUBLIC_TO_EVERYONE", public_base_url: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    """Kiểm tra kết nối tài khoản TikTok qua TikTok Content Posting API hoặc thông tin kênh"""
    token = (access_token or "").strip()
    u_name = (username or "").strip()
    c_key = (client_key or "").strip()
    c_sec = (client_secret or "").strip()
    priv = (privacy_level or "").strip() or "PUBLIC_TO_EVERYONE"
    pub_url = (public_base_url or "").strip().rstrip("/")

    if not token and not u_name:
        return False, "Vui lòng nhập TikTok Access Token hoặc Tên Kênh TikTok (@username) của bạn!", {}

    # 1. Nếu có Access Token, gọi trực tiếp TikTok Open API v2
    if token:
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name,bio_description,is_verified,follower_count"
            resp = requests.get(url, headers=headers, timeout=15)

            if resp.status_code == 200:
                data = resp.json()
                err = data.get("error", {})
                err_code = err.get("code")
                if err_code and err_code != "ok":
                    return False, f"TikTok API thông báo: {err.get('message', err_code)}", {}

                user = data.get("data", {}).get("user", {})
                display_name = user.get("display_name", "") or u_name or "Kênh TikTok"
                open_id = user.get("open_id", "")
                follower_count = user.get("follower_count", 0)
                avatar_url = user.get("avatar_url", "")

                info_str = f"Kênh: {display_name}"
                if follower_count:
                    info_str += f" | {follower_count:,} Followers"

                # Lưu cấu hình thành công
                save_integrations_config({
                    "tiktok": {
                        "access_token": token,
                        "username": u_name or display_name,
                        "client_key": c_key,
                        "client_secret": c_sec,
                        "public_base_url": pub_url,
                        "display_name": display_name,
                        "open_id": open_id,
                        "avatar_url": avatar_url,
                        "privacy_level": priv,
                        "is_connected": True,
                        "last_tested": datetime.now().isoformat()
                    }
                })

                return True, f"Kết nối TikTok thành công! ({info_str})", {
                    "display_name": display_name,
                    "open_id": open_id,
                    "follower_count": follower_count
                }
            else:
                err_text = ""
                try:
                    err_json = resp.json().get("error", {})
                    err_text = err_json.get("message") or err_json.get("code") or resp.text
                except Exception:
                    err_text = resp.text
                return False, f"Không thể xác thực TikTok Token ({resp.status_code}): {err_text}", {}
        except Exception as e:
            return False, f"Lỗi kết nối máy chủ TikTok: {str(e)}", {}

    # 2. Nếu có Username kênh (kết nối kênh đại diện cho giai đoạn đăng bài)
    clean_user = u_name if u_name.startswith("@") else f"@{u_name}"
    save_integrations_config({
        "tiktok": {
            "access_token": "",
            "username": clean_user,
            "client_key": c_key,
            "client_secret": c_sec,
            "public_base_url": pub_url,
            "display_name": clean_user,
            "privacy_level": priv,
            "is_connected": True,
            "last_tested": datetime.now().isoformat()
        }
    })

    return True, f"Đã kết nối và lưu thông tin Kênh TikTok: {clean_user} (Chế độ đăng: {priv})", {
        "display_name": clean_user,
        "username": clean_user
    }


# =========================================================
# TÍNH NĂNG TƯƠNG TÁC HAI CHIỀU TELEGRAM: HỎI & CHỜ PHẢN HỒI
# =========================================================

import time
import uuid

ACTIVE_APPROVAL_SESSIONS = {}


def auto_detect_telegram_chat_id(bot_token: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Tự động quét tin nhắn mới nhất gửi tới Bot để lấy Chat ID của người dùng"""
    token = bot_token.strip()
    if not token:
        return False, "Chưa có Telegram Bot Token!", {}

    try:
        # Lấy thông tin bot trước
        me_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        bot_user = me_resp.json().get("result", {}).get("username", "bot") if me_resp.status_code == 200 else "bot"

        # Quét updates
        up_url = f"https://api.telegram.org/bot{token}/getUpdates?limit=20"
        up_resp = requests.get(up_url, timeout=15)
        if up_resp.status_code != 200:
            return False, f"Không thể lấy updates từ Telegram (Mã {up_resp.status_code})", {}

        updates = up_resp.json().get("result", [])
        if not updates:
            return False, f"Chưa có tin nhắn nào gửi tới @{bot_user}. Vui lòng mở Telegram, tìm @{bot_user} và bấm START hoặc nhắn 'hello' trước!", {
                "bot_username": bot_user
            }

        # Duyệt từ tin mới nhất về trước
        for u in reversed(updates):
            chat = None
            from_user = None
            if "message" in u:
                chat = u["message"].get("chat")
                from_user = u["message"].get("from")
            elif "callback_query" in u:
                chat = u["callback_query"].get("message", {}).get("chat")
                from_user = u["callback_query"].get("from")

            if chat and chat.get("id"):
                c_id = str(chat["id"])
                # Bỏ qua nếu chat_id trùng với ID bot
                c_name = chat.get("first_name") or chat.get("title") or (from_user.get("first_name") if from_user else "Người dùng")
                c_username = chat.get("username") or (from_user.get("username") if from_user else "")

                # Lưu ngay vào cấu hình
                save_integrations_config({
                    "telegram": {
                        "bot_token": token,
                        "chat_id": c_id,
                        "is_connected": True,
                        "last_tested": datetime.now().isoformat()
                    }
                })

                return True, f"Đã tìm thấy Chat ID của bạn: {c_id} ({c_name})", {
                    "chat_id": c_id,
                    "user_name": c_name,
                    "username": f"@{c_username}" if c_username else "",
                    "bot_username": bot_user
                }

        return False, f"Chưa tìm thấy người dùng gửi tin nhắn cho @{bot_user}. Vui lòng nhắn tin cho @{bot_user} rồi thử lại!", {
            "bot_username": bot_user
        }
    except Exception as e:
        return False, f"Lỗi quét Chat ID: {str(e)}", {}


def send_telegram_question(bot_token: str, chat_id: str, question: str = "bạn có đồng ý chỉnh sửa không?") -> Tuple[bool, str, Dict[str, Any]]:
    """Gửi câu hỏi kèm 2 nút [Đồng ý] / [Từ chối] tới Telegram và khởi tạo phiên chờ phản hồi"""
    token = bot_token.strip()
    c_id = chat_id.strip()

    if not token:
        return False, "Chưa cấu hình Telegram Bot Token!", {}

    # Nếu chat_id là tên bot hoặc trống, thử tự động tìm chat_id
    if not c_id or c_id.startswith("@") and "bot" in c_id.lower():
        found, msg, det = auto_detect_telegram_chat_id(token)
        if found:
            c_id = det["chat_id"]
        else:
            bot_user = det.get("bot_username", "BoomNam_Bot")
            return False, f"Chat ID hiện tại ({chat_id}) không thể nhận tin! Vui lòng mở Telegram, nhắn tin cho @{bot_user} (hoặc bấm /start) trước để Bot lấy Chat ID của bạn.", {
                "need_start": True,
                "bot_username": bot_user
            }

    prompt_id = str(uuid.uuid4())[:8]
    clean_question = question.strip() if question else "bạn có đồng ý chỉnh sửa không?"

    payload = {
        "chat_id": c_id,
        "text": f"🔔 <b>[TIKTOK STUDIO - XÁC NHẬN TÁC NGHIỆP]</b>\n\n❓ <b>{clean_question}</b>\n\n<i>👉 Vui lòng nhấn nút chọn bên dưới hoặc gõ trực tiếp câu trả lời của bạn:</i>",
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "✅ Đồng ý", "callback_data": f"approve_{prompt_id}"},
                    {"text": "❌ Từ chối", "callback_data": f"reject_{prompt_id}"}
                ]
            ]
        }
    }

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code != 200:
            err_json = resp.json() if resp.text.startswith("{") else {}
            desc = err_json.get("description", resp.text)
            return False, f"Không thể gửi tin nhắn Telegram: {desc}", {}

        msg_data = resp.json().get("result", {})
        message_id = msg_data.get("message_id")

        # Lưu session vào bộ nhớ
        ACTIVE_APPROVAL_SESSIONS[prompt_id] = {
            "prompt_id": prompt_id,
            "token": token,
            "chat_id": c_id,
            "message_id": message_id,
            "question": clean_question,
            "sent_at": time.time(),
            "status": "waiting",
            "answered": False,
            "response": None,
            "responder": None,
            "answered_at": None
        }

        return True, "Đã gửi câu hỏi tới Telegram thành công! Đang chờ phản hồi...", {
            "prompt_id": prompt_id,
            "chat_id": c_id,
            "message_id": message_id,
            "question": clean_question
        }
    except Exception as e:
        return False, f"Lỗi gửi câu hỏi Telegram: {str(e)}", {}


def poll_telegram_response(prompt_id: str) -> Dict[str, Any]:
    """Kiểm tra xem người dùng đã trả lời câu hỏi trên Telegram hay chưa"""
    session = ACTIVE_APPROVAL_SESSIONS.get(prompt_id)
    if not session:
        return {"success": False, "message": "Phiên hỏi đáp không tồn tại hoặc đã hết hạn."}

    # Nếu đã được trả lời trước đó
    if session.get("answered"):
        return {
            "success": True,
            "answered": True,
            "response": session.get("response"),
            "responder": session.get("responder"),
            "answered_at": session.get("answered_at"),
            "question": session.get("question")
        }

    token = session["token"]
    c_id = str(session["chat_id"])
    target_msg_id = session.get("message_id")
    sent_at = session.get("sent_at", 0)

    try:
        up_url = f"https://api.telegram.org/bot{token}/getUpdates?limit=25"
        resp = requests.get(up_url, timeout=10)
        if resp.status_code != 200:
            return {"success": True, "answered": False, "waiting": True}

        updates = resp.json().get("result", [])

        for u in reversed(updates):
            # 1. Kiểm tra Callback Query (Bấm nút inline)
            if "callback_query" in u:
                cq = u["callback_query"]
                data = cq.get("data", "")
                from_u = cq.get("from", {})
                user_name = from_u.get("first_name", "Người dùng")
                username = f" (@{from_u.get('username')})" if from_u.get("username") else ""
                full_responder = f"{user_name}{username}"

                if data in [f"approve_{prompt_id}", f"reject_{prompt_id}"]:
                    is_agree = "approve" in data
                    ans_label = "✅ Đồng ý" if is_agree else "❌ Từ chối"
                    ans_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

                    # Trả lời callback để tắt spinner trên Telegram
                    try:
                        requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={
                            "callback_query_id": cq.get("id"),
                            "text": f"Hệ thống đã nhận: {ans_label}"
                        }, timeout=5)
                        
                        # Gửi xác nhận phản hồi trong Telegram
                        confirm_text = f"🎉 <b>ĐÃ XÁC NHẬN PHẢN HỒI!</b>\n\nBạn đã chọn: <b>{ans_label}</b> cho câu hỏi: <i>'{session.get('question')}'</i>\nThời gian: <code>{ans_time}</code>"
                        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
                            "chat_id": c_id,
                            "text": confirm_text,
                            "parse_mode": "HTML"
                        }, timeout=5)
                    except Exception:
                        pass

                    session["answered"] = True
                    session["status"] = "answered"
                    session["response"] = ans_label
                    session["responder"] = full_responder
                    session["answered_at"] = ans_time

                    return {
                        "success": True,
                        "answered": True,
                        "response": ans_label,
                        "responder": full_responder,
                        "answered_at": ans_time,
                        "question": session.get("question")
                    }

            # 2. Kiểm tra Message thường (Người dùng gõ chữ trả lời)
            if "message" in u:
                msg = u["message"]
                msg_chat = msg.get("chat", {})
                msg_time = msg.get("date", 0)
                msg_text = msg.get("text", "").strip()

                # Kiểm tra cùng chat và gửi sau thời điểm hỏi
                if str(msg_chat.get("id")) == c_id and msg_time >= (sent_at - 2) and msg_text and not msg_text.startswith("/"):
                    from_u = msg.get("from", {})
                    user_name = from_u.get("first_name", "Người dùng")
                    username = f" (@{from_u.get('username')})" if from_u.get("username") else ""
                    full_responder = f"{user_name}{username}"
                    ans_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

                    # Gửi xác nhận trong Telegram
                    try:
                        confirm_text = f"🎉 <b>ĐÃ XÁC NHẬN PHẢN HỒI!</b>\n\nNội dung bạn trả lời: <b>{msg_text}</b>\nThời gian: <code>{ans_time}</code>"
                        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
                            "chat_id": c_id,
                            "text": confirm_text,
                            "parse_mode": "HTML"
                        }, timeout=5)
                    except Exception:
                        pass

                    session["answered"] = True
                    session["status"] = "answered"
                    session["response"] = msg_text
                    session["responder"] = full_responder
                    session["answered_at"] = ans_time

                    return {
                        "success": True,
                        "answered": True,
                        "response": msg_text,
                        "responder": full_responder,
                        "answered_at": ans_time,
                        "question": session.get("question")
                    }

        return {"success": True, "answered": False, "waiting": True}
    except Exception as e:
        return {"success": False, "message": f"Lỗi kiểm tra phản hồi: {str(e)}"}

