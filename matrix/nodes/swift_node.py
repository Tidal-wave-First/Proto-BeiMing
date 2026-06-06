"""矩阵节点: swift_node —— 数据清洗与特征提取感官"""
import sys, os, time, json
sys.path.insert(0, 'D:/SwiftAssistant')
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.nodes.base_node import MatrixNode

class SwiftNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("swift_node", bus)
        
    def on_start(self):
        self.listen("swift.clean", self.handle_clean)
        self.listen("swift.extract", self.handle_extract)
        print(f"[swift_node] 数据感官已激活，等待输入...")
    
    def handle_clean(self, payload, sender):
        """简单的数据清洗：去除多余空白、特殊字符等"""
        raw_text = payload.get("text", "")
        # 基础清洗
        cleaned = raw_text.strip()
        cleaned = ' '.join(cleaned.split()) # 合并多余空白
        
        self.emit("swift.cleaned", {
            "original": raw_text[:100],
            "cleaned": cleaned,
            "length": len(cleaned)
        })
    
    def handle_extract(self, payload, sender):
        """简单的特征提取：关键词、文本长度、类型判断"""
        text = payload.get("text", "")
        # 简单分词和关键词提取
        words = text.lower().split()
        # 基于规则的类型判断
        features = {
            "text": text[:200],
            "length": len(text),
            "word_count": len(words),
            "has_code": any(kw in text for kw in ["def ", "import ", "class ", "print(", "="]),
            "has_question": "?" in text or any(text.startswith(w) for w in ["什么", "如何", "怎么", "为什么"]),
            "has_error": any(kw in text.lower() for kw in ["error", "错误", "失败", "exception", "traceback"]),
            "keywords": list(set([w for w in words if len(w) > 3 and w.isalpha()]))[:10]
        }
        
        self.emit("swift.features", features)
        # 如果检测到错误内容，可以主动通知皮层
        if features["has_error"]:
            self.emit("cortex.store", {
                "type": "error_signal",
                "content": text[:200],
                "tags": ["error", "swift_detected"]
            })

def node_main():
    from matrix.bus.message_bus import bus
    node = SwiftNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
