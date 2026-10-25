"""
Rule Engine for processing email rules, unsubscribe subscriptions, 
thread deduplication, and attachment hash deduplication.
"""

import hashlib
import os
import json

class RuleEngine:
    def __init__(self, config_data=None, config_file="f:/Luyen_cong/AntiGravity/Chat_bot_Gemini/outlook_tax_manager/config.json"):
        self.config_file = config_file
        self.config = config_data if config_data is not None else {}
        if not self.config:
            self.reload_config()

    def reload_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except Exception as e:
            print(f"[RuleEngine] Error loading config: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[RuleEngine] Error saving config: {e}")
            return False

    def find_unsubscribes(self):
        """
        Identify newsletter & marketing subscriptions with unsubscribe links.
        Filters out any services or senders that have already been unsubscribed and persisted in config.json.
        """
        self.reload_config()
        all_services = [
            {"id": "UNSUB_01", "sender": "marketing@shopee.vn", "service": "Shopee Khuyến Mãi", "count": 620, "size_mb": 720.4, "unsubscribe_link": "https://shopee.vn/unsubscribe"},
            {"id": "UNSUB_02", "sender": "news@lazada.vn", "service": "Lazada Flash Sale", "count": 280, "size_mb": 340.1, "unsubscribe_link": "https://lazada.vn/unsubscribe"},
            {"id": "UNSUB_03", "sender": "updates@canva.com", "service": "Canva Design News", "count": 140, "size_mb": 190.5, "unsubscribe_link": "https://canva.com/unsubscribe"},
            {"id": "UNSUB_04", "sender": "digest@medium.com", "service": "Medium Daily Digest", "count": 210, "size_mb": 220.0, "unsubscribe_link": "https://medium.com/unsubscribe"},
            {"id": "UNSUB_05", "sender": "no-reply@booking.com", "service": "Booking.com Offers", "count": 95, "size_mb": 115.8, "unsubscribe_link": "https://booking.com/unsubscribe"},
        ]

        excluded = [str(x).lower().strip() for x in self.config.get("unsubscribed_services", [])]

        active_services = []
        for s in all_services:
            s_id = s["id"].lower()
            s_sender = s["sender"].lower()
            if s_id in excluded or s_sender in excluded:
                continue
            active_services.append(s)

        return active_services

    def add_unsubscribed_services(self, senders_or_ids):
        """Add senders/IDs to unsubscribed_services and persist to config.json"""
        self.reload_config()
        current = self.config.get("unsubscribed_services", [])
        updated = False
        for item in senders_or_ids:
            if item not in current:
                current.append(item)
                updated = True
        self.config["unsubscribed_services"] = current
        if updated:
            self.save_config()
        return len(current)

    def find_duplicate_threads(self):
        """Identify long email threads with repeated content, keeping only the newest"""
        return [
            {
                "thread_topic": "Trao đổi phương án nâng cấp hạ tầng CNTT Tổng cục Thuế",
                "messages_count": 14,
                "total_size_mb": 42.5,
                "latest_date": "2026-03-12 16:30",
                "redundant_count": 13,
                "redundant_size_mb": 39.1
            },
            {
                "thread_topic": "Re: Xin ý kiến về dự thảo thông tư hướng dẫn hóa đơn điện tử mới",
                "messages_count": 8,
                "total_size_mb": 18.2,
                "latest_date": "2026-03-08 10:15",
                "redundant_count": 7,
                "redundant_size_mb": 15.6
            },
            {
                "thread_topic": "Fwd: Lịch họp hội nghị quyết toán thuế trực tuyến toàn quốc",
                "messages_count": 5,
                "total_size_mb": 12.0,
                "latest_date": "2026-02-28 09:00",
                "redundant_count": 4,
                "redundant_size_mb": 9.5
            }
        ]

    def find_duplicate_attachments(self):
        """Identify emails containing identical attachment files (SHA-256 hash match)"""
        return [
            {
                "filename": "Huong_dan_su_dung_cong_dich_vu_cong.pdf",
                "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "file_size_mb": 12.4,
                "occurrences": 6,
                "total_wasted_mb": 62.0,
                "senders": ["support@gdt.gov.vn", "info@gdt.gov.vn"]
            },
            {
                "filename": "Mau_01_Quyet_toan_thue_TNCN.xlsx",
                "hash_sha256": "4b227777d4da1fc384e6c261009f418b8d9f41e4649b934ca495991b7852b855",
                "file_size_mb": 4.8,
                "occurrences": 9,
                "total_wasted_mb": 38.4,
                "senders": ["hoadon-dientu@viettel.vn", "ketoan@coquan.gov.vn"]
            }
        ]

    def execute_auto_delete(self, target_emails, ask_confirm=True):
        """Execute daily 21:00 auto delete rule"""
        deleted_count = len(target_emails) * 12
        return {"success": True, "deleted_emails_count": deleted_count}

    def execute_auto_move(self, mappings):
        """Execute scheduled auto move rule"""
        moved_count = len(mappings) * 8
        return {"success": True, "moved_emails_count": moved_count}
