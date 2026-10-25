import os
import sys
import tempfile
import yt_dlp
from typing import List, Dict, Any

class AudioTranscriber:
    def __init__(self, model_name: str = "base"):
        """
        Khởi tạo mô hình Whisper AI để nhận dạng giọng nói tiếng Việt từ file âm thanh.
        model_name có thể là: 'tiny', 'base', 'small' ('base' chạy nhanh và chính xác trên CPU/GPU).
        """
        self.model_name = model_name
        self.model = None

    def _load_model(self):
        if self.model is None:
            try:
                import whisper
                print(f"[WHISPER AI] Đang nạp mô hình Whisper AI ('{self.model_name}')...")
                self.model = whisper.load_model(self.model_name)
                print("[WHISPER AI] Nạp mô hình AI thành công!")
            except ImportError:
                print("[CẢNH BÁO] Chưa cài đặt thư viện 'openai-whisper'. Bạn có thể cài bằng lệnh: pip install openai-whisper")
                return None
            except Exception as e:
                print(f"[CẢNH BÁO] Không thể nạp Whisper AI: {e}")
                return None
        return self.model

    def extract_audio_and_transcribe(self, video_url: str) -> List[Dict[str, Any]]:
        """
        Tải file âm thanh siêu nhẹ của video và cho Whisper AI chuyển giọng nói thành văn bản kèm mốc thời gian.
        """
        model = self._load_model()
        if model is None:
            return []

        temp_dir = tempfile.gettempdir()
        temp_audio_path = os.path.join(temp_dir, f"temp_whisper_audio_{os.getpid()}.m4a")

        # 1. Tải luồng âm thanh siêu nhẹ bằng yt-dlp với thuật toán vượt Bot Detection YouTube
        print(f"[WHISPER AI] Đang tải luồng âm thanh của video: {video_url}...")

        # Tìm kiếm file cookies.txt nếu có
        cookie_file = None
        from config import DEFAULT_COOKIE_PATH
        candidate_cookies = [
            DEFAULT_COOKIE_PATH,
            os.path.join(os.getcwd(), "cookies.txt"),
            os.path.join(os.getcwd(), "youtube_cookies.txt"),
        ]
        for c in candidate_cookies:
            if os.path.exists(c) and os.path.getsize(c) > 0:
                cookie_file = c
                break

        client_candidates = [
            ['mweb', 'ios'],
            ['tv_embedded'],
            ['android', 'ios'],
            ['web', 'mweb']
        ]

        download_success = False
        for clients in client_candidates:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_audio_path,
                'extractor_args': {'youtube': {'player_client': clients}},
                'remote_components': {'ejs:github': {}},
                'overwrites': True,
                'quiet': True,
                'no_warnings': True
            }
            if cookie_file:
                ydl_opts['cookiefile'] = cookie_file

            # Thử tự động nạp Cookie từ trình duyệt nếu có
            for browser_name in ['chrome', 'edge', 'firefox']:
                try:
                    ydl_opts_cookie = dict(ydl_opts)
                    ydl_opts_cookie['cookiesfrombrowser'] = (browser_name,)
                    with yt_dlp.YoutubeDL(ydl_opts_cookie) as ydl:
                        ydl.download([video_url])
                    if os.path.exists(temp_audio_path) and os.path.getsize(temp_audio_path) > 1000:
                        download_success = True
                        break
                except Exception:
                    pass

            if download_success:
                break

            # Nếu không có cookie, thử không cần cookie với client phù hợp
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                if os.path.exists(temp_audio_path) and os.path.getsize(temp_audio_path) > 1000:
                    download_success = True
                    break
            except Exception:
                continue

        if not download_success:
            print(f"[WHISPER AI LỖI] Không thể tải luồng âm thanh từ YouTube.")
            if os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass
            return []

        # 2. Cho Whisper AI nhận dạng giọng nói (Language: vi)
        snippets = []
        try:
            print("[WHISPER AI] Đang phân tích chuyển giọng nói tiếng Việt thành phụ đề...")
            result = model.transcribe(temp_audio_path, language="vi", fp16=False)
            segments = result.get("segments", [])

            for seg in segments:
                start = float(seg.get("start", 0.0))
                end = float(seg.get("end", 0.0))
                dur = max(0.5, end - start)
                text = seg.get("text", "").strip()

                if text:
                    snippets.append({
                        "text": text,
                        "start": start,
                        "duration": dur
                    })

            print(f"[WHISPER AI THÀNH CÔNG] Đã tạo thành công {len(snippets)} câu phụ đề bằng AI!")

        except Exception as err:
            print(f"[WHISPER AI LỖI] Nhận dạng giọng nói thất bại: {err}")
        finally:
            # Dọn dẹp file âm thanh tạm
            if os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass

        return snippets
