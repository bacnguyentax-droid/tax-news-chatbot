import sys
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from typing import List, Dict, Any
from config import DEFAULT_TAX_KEYWORDS, MAX_GAP_SECONDS, BUFFER_START_SECONDS, BUFFER_END_SECONDS
from audio_transcriber import AudioTranscriber

# Thiết lập stdout mã hóa UTF-8 để không bị lỗi trên Windows console cũ
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class TranscriptAnalyzer:
    def __init__(
        self,
        keywords: List[str] = None,
        buffer_start: float = BUFFER_START_SECONDS,
        buffer_end: float = BUFFER_END_SECONDS,
        max_gap: float = MAX_GAP_SECONDS
    ):
        self.keywords = [k.lower() for k in (keywords or DEFAULT_TAX_KEYWORDS)]
        self.buffer_start = buffer_start
        self.buffer_end = buffer_end
        self.max_gap = max_gap
        self.ai_transcriber = AudioTranscriber(model_name="base")

    @staticmethod
    def format_seconds_to_hhmmss(seconds: float) -> str:
        """
        Chuyển đổi số giây sang định dạng HH:MM:SS.
        """
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def get_transcript(self, video_id: str, video_url: str = None) -> List[Dict[str, Any]]:
        """
        Lấy phụ đề tiếng Việt bằng quy trình Hybrid:
        1. Phụ đề có sẵn của YouTube.
        2. Nếu không có phụ đề -> Dùng Whisper AI chuyển âm thanh thành chữ kèm mốc thời gian.
        """
        raw_snippets = []

        # Tầng 1: Sử dụng youtube-transcript-api lấy phụ đề tiếng Việt (thủ công & tự động)
        try:
            api = YouTubeTranscriptApi()
            t_list = api.list(video_id)
            
            t_selected = None
            try:
                t_selected = t_list.find_transcript(['vi', 'vi-VN'])
            except Exception:
                pass

            if not t_selected:
                try:
                    t_selected = t_list.find_generated_transcript(['vi', 'vi-VN'])
                except Exception:
                    pass

            if not t_selected:
                for t in t_list:
                    if t.is_translatable:
                        try:
                            t_selected = t.translate('vi')
                            break
                        except Exception:
                            pass

            if t_selected:
                raw_snippets = t_selected.fetch()

        except Exception:
            pass

        # Tầng 2: Sử dụng yt-dlp trích xuất phụ đề từ luồng Player
        if not raw_snippets:
            try:
                import json
                import re
                import yt_dlp
                v_url = video_url or f"https://www.youtube.com/watch?v={video_id}"
                ydl_opts = {
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautosub': True,
                    'subtitleslangs': ['vi', 'vi-VN', 'vi.*'],
                    'quiet': True,
                    'no_warnings': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(v_url, download=False)
                    all_subs = {}
                    if info.get('subtitles'):
                        all_subs.update(info['subtitles'])
                    if info.get('automatic_captions'):
                        all_subs.update(info['automatic_captions'])

                    vi_key = next((k for k in all_subs.keys() if k.startswith('vi')), None)
                    if vi_key:
                        sub_formats = all_subs[vi_key]
                        fmt = next((f for f in sub_formats if f.get('ext') == 'json3'), None)
                        if not fmt:
                            fmt = next((f for f in sub_formats if f.get('ext') == 'vtt'), None)

                        if fmt:
                            content = ydl.urlopen(fmt['url']).read().decode('utf-8')
                            if fmt.get('ext') == 'json3':
                                data = json.loads(content)
                                for ev in data.get('events', []):
                                    start = float(ev.get('tStartMs', 0)) / 1000.0
                                    dur = float(ev.get('dDurationMs', 0)) / 1000.0
                                    text = ''.join([s.get('utf8', '') for s in ev.get('segs', [])]).strip()
                                    if text:
                                        raw_snippets.append({'text': text, 'start': start, 'duration': dur})
                            elif fmt.get('ext') == 'vtt':
                                lines = content.splitlines()
                                time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})')
                                cur_start, cur_dur = 0.0, 0.0
                                for line in lines:
                                    m = time_pattern.search(line)
                                    if m:
                                        parts = m.group(1).split(':')
                                        cur_start = float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                                        parts_end = m.group(2).split(':')
                                        end_t = float(parts_end[0])*3600 + float(parts_end[1])*60 + float(parts_end[2])
                                        cur_dur = max(1.0, end_t - cur_start)
                                    elif line.strip() and not line.startswith('WEBVTT') and not line.isdigit():
                                        clean_t = re.sub(r'<[^>]+>', '', line.strip())
                                        if clean_t:
                                            raw_snippets.append({'text': clean_t, 'start': cur_start, 'duration': cur_dur})

            except Exception:
                pass

        # Tầng 3 (Whisper AI Fallback): Nếu không có phụ đề sẵn ➔ Cho Whisper AI bóc tách âm thanh
        if not raw_snippets and video_url:
            print(f"[HYBRID SOLUTION] Video {video_id} không có phụ đề sẵn ➔ Đang kích hoạt Whisper AI nhận dạng giọng nói...")
            raw_snippets = self.ai_transcriber.extract_audio_and_transcribe(video_url)

        if not raw_snippets:
            print(f"[THÔNG BÁO] Video {video_id} không tìm thấy dữ liệu phụ đề.")
            return []

        # Chuẩn hóa dữ liệu
        normalized = []
        for item in raw_snippets:
            if isinstance(item, dict):
                text = item.get('text', '')
                start = float(item.get('start', 0.0))
                duration = float(item.get('duration', 0.0))
            else:
                text = getattr(item, 'text', '')
                start = float(getattr(item, 'start', 0.0))
                duration = float(getattr(item, 'duration', 0.0))

            normalized.append({
                'text': text,
                'start': start,
                'duration': duration
            })

        return normalized

    def _find_smart_boundaries(
        self,
        subtitles: List[Dict[str, Any]],
        first_seg: Dict[str, Any],
        last_seg: Dict[str, Any],
        default_buf_start: float = 10.0,
        default_buf_end: float = 10.0
    ) -> (float, float):
        """
        Xác định mốc cắt thông minh:
        - Tìm ngược về trước để bắt trọn câu dẫn/đầu bài tin (dấu hiệu: 'thưa quý vị', 'mới đây', 'liên quan', khoảng lặng >1.8s).
        - Tìm tiến về sau để bắt trọn câu kết bài tin (dấu chấm câu, khoảng lặng >1.8s, từ chuyển cảnh).
        - Tránh tuyệt đối việc cắt thừa thông tin bài tin trước hoặc bài tin sau.
        """
        raw_start = first_seg['start']
        raw_end = last_seg['end']

        if not subtitles:
            return max(0.0, raw_start - 5.0), raw_end + 5.0

        first_idx = 0
        last_idx = len(subtitles) - 1

        for idx, sub in enumerate(subtitles):
            if abs(sub['start'] - raw_start) < 0.2:
                first_idx = idx
                break

        for idx in range(len(subtitles) - 1, -1, -1):
            sub_end = subtitles[idx]['start'] + subtitles[idx]['duration']
            if abs(sub_end - raw_end) < 0.2 or subtitles[idx]['start'] <= raw_end <= sub_end:
                last_idx = idx
                break

        # 1. BẮT ĐẦU THÔNG MINH (Dẫn bài tin): Quét ngược tối đa 20s
        smart_start = max(0.0, raw_start - 5.0)
        intro_keywords = ["thưa quý vị", "liên quan", "về vấn đề", "mới đây", "theo ghi nhận", "chuyển sang", "bộ tài chính", "cơ quan thuế", "tại", "theo", "thưa", "ngày"]
        
        current_idx = first_idx
        min_start_limit = max(0.0, raw_start - 25.0)
        
        while current_idx > 0 and subtitles[current_idx]['start'] > min_start_limit:
            prev_sub = subtitles[current_idx - 1]
            cur_sub = subtitles[current_idx]
            gap = cur_sub['start'] - (prev_sub['start'] + prev_sub['duration'])

            if gap >= 1.8:
                smart_start = cur_sub['start']
                break

            cur_text_lower = cur_sub['text'].lower().strip()
            if any(cur_text_lower.startswith(kw) or f" {kw}" in cur_text_lower for kw in intro_keywords):
                smart_start = cur_sub['start']
                break

            current_idx -= 1
            smart_start = subtitles[current_idx]['start']

        # 2. KẾT THÚC THÔNG MINH (Kết bài tin): Quét tiến tối đa 20s
        smart_end = raw_end + 5.0
        outro_keywords = ["chuyển sang", "trong khi đó", "cũng trong ngày", "tin khác", "thời tiết", "tiếp theo", "sau đây", "tiếp tục"]

        current_idx = last_idx
        max_end_limit = raw_end + 25.0

        while current_idx < len(subtitles) - 1 and (subtitles[current_idx]['start'] + subtitles[current_idx]['duration']) < max_end_limit:
            cur_sub = subtitles[current_idx]
            next_sub = subtitles[current_idx + 1]
            gap = next_sub['start'] - (cur_sub['start'] + cur_sub['duration'])

            if gap >= 1.8:
                smart_end = cur_sub['start'] + cur_sub['duration']
                break

            next_text_lower = next_sub['text'].lower().strip()
            if any(next_text_lower.startswith(kw) for kw in outro_keywords):
                smart_end = cur_sub['start'] + cur_sub['duration']
                break

            current_idx += 1
            smart_end = subtitles[current_idx]['start'] + subtitles[current_idx]['duration']

        final_start = max(0.0, smart_start)
        final_end = max(final_start + 3.0, smart_end)

        return round(final_start, 2), round(final_end, 2)

    def extract_tax_sections(
        self,
        video_id: str,
        video_title: str = "",
        video_description: str = "",
        video_url: str = None,
        buffer_start: float = None,
        buffer_end: float = None,
        max_gap: float = None
    ) -> List[Dict[str, Any]]:
        """
        Phân tích phụ đề theo thuật toán lọc thông minh:
        Tự động xác định ranh giới bài tin chuẩn xác, tránh thừa trước/thừa sau.
        """
        buf_start = buffer_start if buffer_start is not None else self.buffer_start
        buf_end = buffer_end if buffer_end is not None else self.buffer_end
        gap_limit = max_gap if max_gap is not None else self.max_gap

        meta_text = f"{video_title} {video_description}".lower()
        has_tax_meta = any(kw in meta_text for kw in self.keywords)

        if not has_tax_meta:
            print(f"[CẮT GIẢM TIẾN TRÌNH] Bỏ qua video {video_id} ('{video_title[:40]}...') do Tiêu đề & Mô tả không chứa từ khóa thuế.")
            return []

        v_url = video_url or f"https://www.youtube.com/watch?v={video_id}"

        subtitles = self.get_transcript(video_id, video_url=v_url)

        matched_segments = []

        # 1. Lọc các câu/đoạn có từ khóa thuế từ phụ đề nếu có
        if subtitles:
            for item in subtitles:
                text = item.get('text', '').lower()
                start = item.get('start', 0.0)
                duration = item.get('duration', 0.0)
                end = start + duration

                found_keywords = [kw for kw in self.keywords if kw in text]
                if found_keywords:
                    matched_segments.append({
                        "start": start,
                        "end": end,
                        "text": item.get('text', ''),
                        "keywords": found_keywords
                    })

        # 2. Nếu phụ đề không có hoặc Whisper AI bị hạn chế nhưng Tiêu đề/Mô tả khớp từ khóa thuế
        # -> Vẫn giữ lại phân đoạn tiêu điểm để KHÔNG BAO GIỜ bị bỏ sót video đã chọn ở Giai đoạn 1!
        if not matched_segments and has_tax_meta:
            found_keywords = [kw for kw in self.keywords if kw in meta_text]
            start_t = subtitles[0]['start'] if subtitles else 0.0
            end_t = (subtitles[-1]['start'] + subtitles[-1]['duration']) if subtitles else 180.0
            matched_segments.append({
                "start": start_t,
                "end": end_t,
                "text": f"Tin tức thuế theo tiêu đề: {video_title}",
                "keywords": found_keywords
            })

        if not matched_segments:
            return []

        grouped_sections = []
        current_group = [matched_segments[0]]

        for seg in matched_segments[1:]:
            prev_seg = current_group[-1]
            if seg['start'] - prev_seg['end'] <= gap_limit:
                current_group.append(seg)
            else:
                grouped_sections.append(current_group)
                current_group = [seg]

        if current_group:
            grouped_sections.append(current_group)

        results = []
        for group in grouped_sections:
            first_seg = group[0]
            last_seg = group[-1]

            buffered_start, buffered_end = self._find_smart_boundaries(
                subtitles=subtitles,
                first_seg=first_seg,
                last_seg=last_seg,
                default_buf_start=buf_start,
                default_buf_end=buf_end
            )

            combined_text = " ... ".join([s['text'] for s in group])
            all_keywords = list(set(kw for s in group for kw in s['keywords']))

            results.append({
                "video_id": video_id,
                "start_seconds": buffered_start,
                "end_seconds": buffered_end,
                "start_str": self.format_seconds_to_hhmmss(buffered_start),
                "end_str": self.format_seconds_to_hhmmss(buffered_end),
                "duration_seconds": round(buffered_end - buffered_start, 2),
                "duration_str": self.format_seconds_to_hhmmss(buffered_end - buffered_start),
                "tax_text": combined_text,
                "matched_keywords": sorted(all_keywords)
            })

        return results



