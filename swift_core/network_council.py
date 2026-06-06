"""
联网思维体 V3.4 - 中文优先筛选
"""

import requests, re
from typing import List, Optional
from common.types import FetchedData
from common.constants import MAX_FETCH_RESULTS, FETCH_TIMEOUT_SECONDS
from thinking_core.ethics_council import EthicsCouncil, get_ethics_council

class NetworkCouncil:
    def __init__(self, ethics=None):
        self.ethics = ethics or get_ethics_council()
        self.knowledge_buffer: dict = {}
        self.is_enabled: bool = True

    def search_and_summarize(self, query: str, purpose: str) -> Optional[str]:
        if self.ethics.judge(purpose).status.value != "approved":
            return None
        if self.ethics.judge(query).status.value != "approved":
            return None

        # 逐个尝试引擎，优先返回包含中文的长摘要
        for engine in [self._search_bing, self._search_duckduckgo_lite]:
            try:
                raw = engine(query)
                for text in raw:
                    text = self._deep_clean(text)
                    # 必须包含中文字符且长度>50
                    if self._is_valid_snippet(text) and len(text) > 50 and re.search(r'[\u4e00-\u9fff]', text):
                        if self.ethics.judge(text).status.value == "approved":
                            return text
            except Exception:
                continue
        return None

    def fetch(self, query: str, purpose: str) -> FetchedData:
        if not self.is_enabled:
            return FetchedData.rejected("未启用")
        if self.ethics.judge(purpose).status.value != "approved":
            return FetchedData.rejected("目的违规")
        if self.ethics.judge(query).status.value != "approved":
            return FetchedData.rejected("查询违规")

        all_cleaned = []
        for engine in [self._search_bing, self._search_duckduckgo_lite]:
            try:
                raw = engine(query)
                for text in raw:
                    text = self._deep_clean(text)
                    if self._is_valid_snippet(text):
                        if self.ethics.judge(text).status.value == "approved":
                            all_cleaned.append(text)
                            if len(all_cleaned) >= MAX_FETCH_RESULTS:
                                break
            except Exception:
                continue
            if len(all_cleaned) >= MAX_FETCH_RESULTS:
                break
        return FetchedData.valid(all_cleaned[:MAX_FETCH_RESULTS])

    def _deep_clean(self, text: str) -> str:
        text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
        text = text.replace("&ensp;", " ").replace("&emsp;", " ")
        text = re.sub(r'&\w+;', ' ', text)
        text = re.sub(r'&#\d+;', ' ', text)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\{[^}]*\}', ' ', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbfa-zA-Z0-9\s.,!?;:()（）【】《》""''、，。！？；：\-\+]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _is_valid_snippet(self, text: str) -> bool:
        if len(text) < 15 or len(text) > 400:
            return False
        # 必须包含中文（2个以上汉字）
        if not re.search(r'[\u4e00-\u9fff]{2,}', text):
            return False
        if re.fullmatch(r'[\d\s\W]+', text):
            return False
        if re.search(r'[<>{}]', text):
            return False
        return True

    def _search_bing(self, query: str) -> List[str]:
        try:
            url = "https://www.bing.com/search"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url, params={"q": query}, headers=headers, timeout=FETCH_TIMEOUT_SECONDS)
            resp.raise_for_status()
            html = resp.text
            snippets = re.findall(r'<p[^>]*class="[^"]*b_caption[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
            if not snippets:
                all_p = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
                snippets = [p for p in all_p if len(p) > 30 and 'function' not in p]
            return [re.sub(r'<[^>]+>', ' ', s).strip() for s in snippets if len(s) > 20][:MAX_FETCH_RESULTS]
        except Exception:
            return []

    def _search_duckduckgo_lite(self, query: str) -> List[str]:
        try:
            url = "https://lite.duckduckgo.com/lite/"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.post(url, data={"q": query}, headers=headers, timeout=FETCH_TIMEOUT_SECONDS)
            resp.raise_for_status()
            snippets = re.findall(r'<a[^>]*class="result-link"[^>]*>(.*?)</a>', resp.text)
            return [s.strip() for s in snippets if len(s) > 5][:MAX_FETCH_RESULTS]
        except Exception:
            return []

    def learn_from(self, data: str, source: str) -> bool:
        if self.ethics.judge(data).status.value != "approved":
            return False
        entry_id = f"{source}_{len(self.knowledge_buffer)}"
        self.knowledge_buffer[entry_id] = {"data": data, "source": source}
        return True

    def clear_knowledge(self):
        self.knowledge_buffer.clear()
