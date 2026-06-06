"""矩阵节点: ethics_node —— 伦理审查防火墙"""
import sys, os, threading, time

sys.path.insert(0, 'D:/SwiftAssistant')
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')

from matrix.nodes.base_node import MatrixNode
from thinking_core.ethics_council import get_ethics_council

class EthicsNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("ethics_node", bus)
        self.council = None
        self.lock = threading.Lock()
        
    def on_start(self):
        print("[ethics_node] 正在加载伦理委员会...")
        try:
            os.chdir('D:/SwiftAssistant')
            self.council = get_ethics_council()
            print("[ethics_node] 伦理委员会已就绪，开始审查所有思考请求。")
        except Exception as e:
            print(f"[ethics_node] 伦理委员会加载失败: {e}。所有请求将被放行。")
        
        # 拦截所有思考请求，先审查后转发
        self.listen("think.request", self.handle_think_request)
    
    def handle_think_request(self, payload, sender):
        prompt = payload.get("prompt", "")
        
        if self.council:
            verdict = self.council.judge(prompt)
            if verdict.status.value != "approved":
                print(f"[ethics_node] 已拦截违规请求: {prompt[:50]}... (原因: {verdict.reason})")
                # 返回拒绝响应，不再转发
                self.emit("think.response", {
                    "request_id": payload.get("request_id", "unknown"),
                    "response": f"请求被伦理委员会驳回: {verdict.reason}",
                    "prompt": prompt,
                    "censored": True
                })
                return
        
        # 审查通过，转发给 think_node
        print(f"[ethics_node] 审查通过，转发思考请求: {prompt[:50]}...")
        self.emit("think.request", payload)

# 节点独立运行入口
def node_main():
    from matrix.bus.message_bus import bus
    node = EthicsNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
