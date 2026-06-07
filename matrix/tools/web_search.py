"""网页搜索工具 - 鲲鹏的感官触手"""
import sys, os
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')

try:
    from ddgs import DDGS
except ImportError:
    print("[swift_node] ddgs 库未安装，搜索功能不可用。请在requirements.txt中添加ddgs并重新部署。")
    DDGS = None

class WebSearcher:
    def __init__(self):
        self.engine = DDGS() if DDGS else None
    
    def search(self, query: str, max_results: int = 5):
        if not self.engine:
            return [{"error": "搜索模块未安装"}]
        try:
            results = []
            for r in self.engine.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                })
            return results
        except Exception as e:
            return [{"error": str(e)}]
