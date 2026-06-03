"""
垂天之翼 - 多源搜索（新增必应国内版）
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import os
import urllib.parse

class Wings:
    def __init__(self, imagination, ethics_rules, config=None):
        self.imagination = imagination
        self.ethics = ethics_rules
        config = config or {}
        search_cfg = config.get('search', {})
        self.search_backend = search_cfg.get('backend', 'ddgs')
        self.proxy = search_cfg.get('proxy', None)
        self.fallback_source = config.get('fallback_source', 'fallback_knowledge.txt')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    def explore(self, task_desc: str, max_results: int = 5) -> int:
        queries = [task_desc]
        captured = 0
        for query in queries:
            if self.search_backend == 'wikipedia':
                results = self._search_wikipedia(query, max_results)
            elif self.search_backend == 'local_only':
                results = self._local_fallback(query)
            elif self.search_backend == 'bing_cn':
                results = self._search_bing_cn(query, max_results)
            else:  # 默认 ddgs
                results = self._search_ddgs(query, max_results)
                if not results:
                    print(">> 翼展：DDGS 未得，尝试必应国内版...")
                    results = self._search_bing_cn(query, max_results)
            if not results:
                results = self._local_fallback(query)

            for item in results:
                text = item.get('full_text', '')
                if not text and item.get('href'):
                    text = self._scrape(item['href'])
                if not text:
                    continue
                if self._ethics_check(text):
                    continue
                self.imagination.add({
                    'source_url': item.get('href', 'local'),
                    'title': item.get('title', query),
                    'snippet': item.get('snippet', ''),
                    'full_text': text[:5000]
                })
                captured += 1
                print(f">> 翼展：已捕获 [{item.get('title', '未知')}]")
        return captured

    def _search_bing_cn(self, query, max_results):
        """搜索 cn.bing.com，返回标题、链接、摘要"""
        try:
            url = "https://cn.bing.com/search"
            params = {'q': query, 'count': max_results}
            resp = self.session.get(url, params=params, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            for item in soup.select('li.b_algo'):
                title_elem = item.select_one('h2 a')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')
                snippet_elem = item.select_one('.b_caption p')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                results.append({'title': title, 'href': href, 'snippet': snippet})
                if len(results) >= max_results:
                    break
            return results
        except Exception as e:
            print(f"必应国内搜索失败: {e}")
            return []

    def _search_ddgs(self, query, max_results):
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                return [{'title': r['title'], 'href': r['href'], 'snippet': r['body']} for r in ddgs.text(query, max_results=max_results)]
        except Exception as e:
            print(f"DDGS错误: {e}")
            return []

    def _search_wikipedia(self, query, max_results):
        try:
            url = "https://zh.wikipedia.org/w/api.php"
            params = {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": max_results}
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            pages = data.get('query', {}).get('search', [])
            return [{'title': p['title'], 'href': f"https://zh.wikipedia.org/wiki/{urllib.parse.quote(p['title'])}", 'snippet': re.sub(r'<[^>]+>', '', p.get('snippet', ''))} for p in pages]
        except Exception as e:
            print(f"Wikipedia错误: {e}")
            return []

    def _scrape(self, url):
        for _ in range(2):
            try:
                resp = self.session.get(url, timeout=5)
                soup = BeautifulSoup(resp.text, 'html.parser')
                for tag in soup(['script','style','nav','footer']):
                    tag.decompose()
                paragraphs = soup.find_all('p')
                text = '\n'.join(p.get_text() for p in paragraphs)
                return text.strip()
            except:
                time.sleep(1)
        return None

    def _local_fallback(self, query):
        if not os.path.exists(self.fallback_source):
            return []
        with open(self.fallback_source, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        matched = [line.strip() for line in lines if query in line]
        return [{'title':'本地','href':'','snippet':'','full_text':l.strip()} for l in matched[:3]]

    def _ethics_check(self, text):
        for rule in self.ethics:
            if re.search(rule['pattern'], text, re.IGNORECASE):
                return True
        return False
