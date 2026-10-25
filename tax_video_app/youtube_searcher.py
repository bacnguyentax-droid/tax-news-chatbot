import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any

class YouTubeSearcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    @staticmethod
    def parse_date_to_iso(date_str: str, is_end_of_day: bool = False) -> str:
        """
        Chuyển đổi chuỗi DD/MM/YYYY hoặc YYYY-MM-DD sang định dạng ISO 8601 UTC.
        Ví dụ: 10/10/2026 -> 2026-10-10T00:00:00Z
        """
        date_str = date_str.strip()
        dt = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                dt = datetime.datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if dt is None:
            raise ValueError(f"Định dạng ngày không hợp lệ: {date_str}. Hãy dùng DD/MM/YYYY.")

        if is_end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59)
        else:
            dt = dt.replace(hour=0, minute=0, second=0)

        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def search_videos_by_channel(
        self,
        start_date: str,
        end_date: str,
        channel_id: str = None,
        query: str = None,
        tax_keywords: List[str] = None,
        filter_by_metadata: bool = True,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm tất cả video xuất bản từ start_date đến end_date từ kênh được chỉ định.
        Sử dụng youtube.videos().list() để lấy TIÊU ĐỀ và MÔ TẢ ĐẦY ĐỦ 100% không bị ẩn / cắt bớt (dấu ...).
        Giai đoạn 1: Lọc nếu Tiêu đề hoặc Mô tả trùng khớp với từ khóa tìm kiếm.
        """
        published_after = self.parse_date_to_iso(start_date, is_end_of_day=False)
        published_before = self.parse_date_to_iso(end_date, is_end_of_day=True)

        kws = [k.lower().strip() for k in (tax_keywords or []) if k.strip()]

        videos = []
        try:
            kwargs = {
                "part": "snippet",
                "type": "video",
                "publishedAfter": published_after,
                "publishedBefore": published_before,
                "maxResults": 50,
                "order": "date"
            }

            if channel_id:
                kwargs["channelId"] = channel_id
            elif query:
                kwargs["q"] = query

            items = []
            next_page_token = None
            max_pages = 5

            for page in range(max_pages):
                if next_page_token:
                    kwargs["pageToken"] = next_page_token

                request = self.youtube.search().list(**kwargs)
                response = request.execute()

                page_items = response.get("items", [])
                items.extend(page_items)

                next_page_token = response.get("nextPageToken")
                if not next_page_token or len(page_items) == 0:
                    break

            video_ids = [item.get("id", {}).get("videoId") for item in items if item.get("id", {}).get("videoId")]

            # Lấy mô tả & tiêu đề ĐẦY ĐỦ 100% không bị cắt dấu ... bằng API videos().list
            full_snippets = {}
            if video_ids:
                try:
                    for i in range(0, len(video_ids), 50):
                        batch_ids = video_ids[i:i+50]
                        v_resp = self.youtube.videos().list(part="snippet", id=",".join(batch_ids)).execute()
                        for v_item in v_resp.get("items", []):
                            v_id = v_item.get("id")
                            v_snip = v_item.get("snippet", {})
                            full_snippets[v_id] = v_snip
                except Exception as e_full:
                    print(f"[CẢNH BÁO] Không nạp được full snippet từ videos().list: {e_full}")

            for item in items:
                video_id = item.get("id", {}).get("videoId")
                if not video_id:
                    continue

                full_snip = full_snippets.get(video_id) or item.get("snippet", {})
                title = full_snip.get("title", "")
                description = full_snip.get("description", "")

                # Loại bỏ dấu ... ở cuối nếu bị YouTube search cắt trước đó
                clean_desc = description.strip()
                if clean_desc.endswith("..."):
                    clean_desc = clean_desc[:-3].strip()
                elif clean_desc.endswith("…"):
                    clean_desc = clean_desc[:-1].strip()

                combined_meta = f"{title} {clean_desc}".lower()
                # Nếu bật lọc metadata và có danh sách từ khóa, kiểm tra sự xuất hiện
                matched_kws = []
                if kws:
                    matched_kws = [kw for kw in kws if kw in combined_meta]

                if filter_by_metadata and kws and not matched_kws:
                    continue

                kw_str = ", ".join(matched_kws) if matched_kws else "Thuế"

                videos.append({
                    "video_id": video_id,
                    "title": title,
                    "description": clean_desc,
                    "channel_title": full_snip.get("channelTitle", "Đài truyền hình"),
                    "published_at": full_snip.get("publishedAt", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "matched_keywords": matched_kws,
                    "keywords_str": kw_str
                })

        except HttpError as e:
            if e.resp.status == 429 or "quota" in str(e).lower() or "ratelimit" in str(e).lower():
                raise RuntimeError("YouTube API Key đã hết hạn ngạch truy vấn miễn phí trong ngày (Quota Exceeded 429). Vui lòng đổi API Key mới trong ứng dụng!")
            raise RuntimeError(f"Lỗi YouTube Data API: {e}")
        except Exception as e:
            raise RuntimeError(f"Lỗi tìm kiếm video: {str(e)}")

        return videos

    def search_multi_channels(
        self,
        start_date: str,
        end_date: str,
        channels: List[Dict[str, str]],
        tax_keywords: List[str] = None,
        filter_by_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm Giai đoạn 1: Quét tất cả các kênh được chọn, lọc ra video có Tiêu đề hoặc Mô tả chứa từ khóa.
        Tự động nạp Mô tả ĐẦY ĐỦ (Full Untruncated Description).
        """
        all_videos = {}
        
        for ch in channels:
            ch_name = ch.get("name", "Kênh")
            ch_id = ch.get("id")

            if not ch_id:
                continue

            try:
                print(f"[STAGE 1 SEARCH] Quét video từ {start_date} đến {end_date} trên kênh: {ch_name} (ID: {ch_id})...")
                results = self.search_videos_by_channel(
                    start_date=start_date,
                    end_date=end_date,
                    channel_id=ch_id,
                    tax_keywords=tax_keywords,
                    filter_by_metadata=filter_by_metadata
                )
                for vid in results:
                    vid["channel_name"] = ch_name
                    all_videos[vid["video_id"]] = vid
            except Exception as e:
                print(f"[CẢNH BÁO] Không thể tìm trên kênh {ch_name}: {e}")
                if "quota" in str(e).lower() or "429" in str(e):
                    raise e

        return list(all_videos.values())



