"""矩阵节点: api_node —— 联网搜索 + DeepSeek推理网关"""
import sys, os, time, requests, re, json
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.nodes.base_node import MatrixNode

class ApiNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("api_node", bus)
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.search_engine = "bing"  # bing / duckduckgo / none
    
    def on_start(self):
        self.listen("api.search", self.handle_search)
        self.listen("api.fetch", self.handle_fetch)
        self.listen("api.deepseek", self.handle_deepseek)
        print(f"[api_node] 网关已激活 | 搜索: {self.search_engine} | DeepSeek: {'已配置' if self.deepseek_key else '未配置'}")
    
    def handle_search(self, payload, sender):
        query = payload.get("query", "")
        max_results = payload.get("max_results", 5)
        request_id = payload.get("request_id", "unknown")
        
        print(f"[api_node] 搜索: {query[:40]}...")
        results = []
        
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            url = "https://www.bing.com/search"
            resp = requests.get(url, params={"q": query}, headers=headers, timeout=10)
            snippets = re.findall(r'<p[^>]*>(.*?)</p>', resp.text, re.DOTALL)
            for s in snippets:
                clean = re.sub(r'<[^>]+>', '', s).strip()
                if len(clean) > 30 and len(clean) < 300:
                    results.append(clean)
                if len(results) >= max_results:
                    break
        except Exception as e:
            print(f"[api_node] 搜索失败: {e}")
        
        self.emit("api.search_result", {"request_id": request_id, "results": results, "query": query})
        # 存入皮层
        for r in results[:3]:
            self.emit("cortex.store", {"type": "web_material", "content": r, "tags": ["search", query[:20]]})
    
    def handle_fetch(self, payload, sender):
        url = payload.get("url", "")
        request_id = payload.get("request_id", "unknown")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            text = re.sub(r'<[^>]+>', ' ', resp.text)
            text = re.sub(r'\s+', ' ', text).strip()[:2000]
            self.emit("api.fetch_result", {"request_id": request_id, "content": text, "url": url})
        except Exception as e:
            self.emit("api.fetch_result", {"request_id": request_id, "error": str(e)})
    
    def handle_deepseek(self, payload, sender):
        """调用 DeepSeek API 进行深度推理"""
        prompt = payload.get("prompt", "")
        system_prompt = payload.get("system_prompt", "你是一个专业的短剧编剧。")
        request_id = payload.get("request_id", "unknown")
        target_topic = payload.get("target_topic", "think.response")
        
        if not self.deepseek_key:
            self.emit(target_topic, {"request_id": request_id, "error": "DeepSeek API Key 未配置", "fallback": True})
            return
        
        print(f"[api_node] DeepSeek推理: {prompt[:50]}...")
        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.8
            }
            resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=30)
            result = resp.json()
            reply = result["choices"][0]["message"]["content"]
            print(f"[api_node] DeepSeek返回: {reply[:60]}...")
            self.emit(target_topic, {"request_id": request_id, "response": reply, "model": "deepseek-chat"})
        except Exception as e:
            print(f"[api_node] DeepSeek调用失败: {e}")
            self.emit(target_topic, {"request_id": request_id, "error": str(e), "fallback": True})

def node_main():
    from matrix.bus.message_bus import bus
    node = ApiNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
