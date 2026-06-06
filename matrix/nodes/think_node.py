"""矩阵节点: think_node —— 本地LLM推理心脏"""
import sys, os, threading, time

# 确保能找到 SwiftAssistant 的模块
sys.path.insert(0, 'D:/SwiftAssistant')
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')

from matrix.nodes.base_node import MatrixNode
from thinking_core.local_llm import LocalLLM

class ThinkNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("think_node", bus)
        self.model_path = 'D:/SwiftAssistant/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf'
        self.llm = None
        self.pending_requests = []
        self.lock = threading.Lock()
        
    def on_start(self):
        print(f"[think_node] 正在加载微型大脑: {self.model_path}")
        try:
            # 确保工作目录正确以加载 rules.yaml
            os.chdir('D:/SwiftAssistant')
            self.llm = LocalLLM(model_path=self.model_path)
            print(f"[think_node] 微型大脑已在线，等待思考请求...")
        except Exception as e:
            print(f"[think_node] 大脑加载失败: {e}。将使用回退逻辑。")
        
        # 监听思考请求
        self.listen("think.request", self.handle_think_request)
    
    def handle_think_request(self, payload, sender):
        prompt = payload.get("prompt", "")
        system_prompt = payload.get("system_prompt", "你是一个追求真理的硅基思维体。")
        request_id = payload.get("request_id", "unknown")
        
        print(f"[think_node] 收到思考请求 from {sender}: {prompt[:50]}...")
        
        if self.llm:
            try:
                response = self.llm.chat(prompt, system_prompt=system_prompt)
            except Exception as e:
                response = f"推理出错: {e}"
        else:
            response = "微型大脑未加载，无法独立思考。"
        
        # 发布思考结果
        self.emit("think.response", {
            "request_id": request_id,
            "response": response,
            "prompt": prompt
        })

# 节点独立运行入口
def node_main():
    from matrix.bus.message_bus import bus
    node = ThinkNode(bus)
    node.on_start()
    # 保持节点活跃
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
