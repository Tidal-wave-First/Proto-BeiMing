"""矩阵节点: swift_node —— 数据采集与整理感官"""
import sys, os, time, threading, json
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.nodes.base_node import MatrixNode
from matrix.tools.web_search import WebSearcher

class SwiftNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("swift_node", bus)
        self.searcher = WebSearcher()
        self.lock = threading.Lock()
        self.collected_data = []
    
    def on_start(self):
        self.listen("swift.search", self.handle_search)
        self.listen("swift.summarize", self.handle_summarize)
        self.listen("swift.get_data", self.handle_get_data)
        print(f"[swift_node] 感官已激活，搜索功能{'就绪' if self.searcher.engine else '不可用'}")
    
    def handle_search(self, payload, sender):
        query = payload.get("query", "")
        max_results = payload.get("max_results", 5)
        request_id = payload.get("request_id", "unknown")
        
        print(f"[swift_node] 正在搜索: {query}")
        results = self.searcher.search(query, max_results)
        
        with self.lock:
            self.collected_data.extend(results)
        
        # 发布搜索结果，同时存储到皮层
        self.emit("swift.search_result", {
            "request_id": request_id,
            "query": query,
            "results": results
        })
        
        # 将有效结果存入皮层
        for r in results:
            if "error" not in r:
                self.emit("cortex.store", {
                    "type": "web_search",
                    "content": f"{r['title']}: {r['body']}",
                    "tags": ["search", query.split()[0] if query else "unknown"],
                    "source_url": r.get("href", "")
                })
    
    def handle_summarize(self, payload, sender):
        """整理已收集的数据，生成摘要"""
        with self.lock:
            data = self.collected_data[-20:]  # 最近20条
        
        if not data:
            self.emit("swift.summary", {"error": "暂无已收集的数据"})
            return
        
        # 请求本地大脑进行摘要推理
        summary_prompt = f"请用中文将以下信息整理成一段连贯的摘要，用于短剧创作参考：\n{json.dumps(data, ensure_ascii=False)[:1500]}"
        
        self.emit("think.request", {
            "request_id": f"summarize_{int(time.time())}",
            "prompt": summary_prompt,
            "system_prompt": "你是一个专业的短剧创作研究员，擅长从碎片信息中提炼故事灵感。"
        })
    
    def handle_get_data(self, payload, sender):
        """返回已收集的所有数据"""
        self.emit("swift.data", {"data": self.collected_data[-50:]})

def node_main():
    from matrix.bus.message_bus import bus
    node = SwiftNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
