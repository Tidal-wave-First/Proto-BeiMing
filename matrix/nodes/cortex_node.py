"""矩阵节点: cortex_node —— 记忆皮层，存储和检索所有经验"""
import sys, os, json, time, threading
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.nodes.base_node import MatrixNode

class CortexNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("cortex_node", bus)
        self.memory = []           # 结构化记忆列表
        self.index = {}            # 关键词索引
        self.lock = threading.Lock()
        self.save_path = "D:/Proto-BeiMing-北冥/data/cortex_memory.json"
        self._load()
    
    def _load(self):
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.memory = data.get("memory", [])
                self.index = data.get("index", {})
            print(f"[cortex_node] 已加载 {len(self.memory)} 条记忆")
        except:
            print("[cortex_node] 初始化为空白皮层")
    
    def _save(self):
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump({"memory": self.memory[-5000:], "index": self.index}, f, ensure_ascii=False)
    
    def on_start(self):
        self.listen("cortex.store", self.handle_store)
        self.listen("cortex.retrieve", self.handle_retrieve)
        self.listen("cortex.query", self.handle_query)
        print(f"[cortex_node] 皮层已激活，监听存储/检索请求")
    
    def handle_store(self, payload, sender):
        with self.lock:
            entry = {
                "id": len(self.memory),
                "type": payload.get("type", "note"),
                "content": payload.get("content", ""),
                "tags": payload.get("tags", []),
                "error_flag": payload.get("error_flag", False),
                "timestamp": time.time(),
                "source": sender
            }
            self.memory.append(entry)
            # 更新索引
            for tag in entry["tags"]:
                if tag not in self.index:
                    self.index[tag] = []
                self.index[tag].append(entry["id"])
            # 定期保存
            if len(self.memory) % 50 == 0:
                self._save()
            self.emit("cortex.stored", {"id": entry["id"]})
    
    def handle_retrieve(self, payload, sender):
        tag = payload.get("tag", "")
        limit = payload.get("limit", 10)
        with self.lock:
            ids = self.index.get(tag, [])[-limit:]
            results = [self.memory[i] for i in ids if i < len(self.memory)]
        self.emit("cortex.result", {"request_tag": tag, "results": results})
    
    def handle_query(self, payload, sender):
        """关键词查询"""
        keyword = payload.get("keyword", "").lower()
        limit = payload.get("limit", 5)
        with self.lock:
            matches = []
            for m in self.memory:
                if keyword in str(m.get("content", "")).lower():
                    matches.append(m)
                if len(matches) >= limit:
                    break
        self.emit("cortex.result", {"request_keyword": keyword, "results": matches})

def node_main():
    from matrix.bus.message_bus import bus
    node = CortexNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
