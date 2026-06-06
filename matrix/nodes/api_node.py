"""矩阵节点: api_node —— 外部API网关，按需调用DeepSeek等更强大的模型"""
import sys, os, time, json
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.nodes.base_node import MatrixNode

class ApiNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("api_node", bus)
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.available = bool(self.api_key)
        
    def on_start(self):
        self.listen("api.request", self.handle_request)
        status = "已连接" if self.available else "未配置密钥，等待接入"
        print(f"[api_node] 外部网关已激活。状态: {status}")
    
    def handle_request(self, payload, sender):
        """转发请求到外部API"""
        if not self.available:
            self.emit("api.response", {
                "error": "API 不可用，请配置 DEEPSEEK_API_KEY 环境变量或等待本地大脑强大起来。"
            })
            return
        
        prompt = payload.get("prompt", "")
        request_id = payload.get("request_id", "unknown")
        
        try:
            import requests
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是北冥之鲲的外部导师，用简练深刻的中文回答。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                self.emit("api.response", {
                    "request_id": request_id,
                    "response": reply,
                    "model": "deepseek-chat"
                })
            else:
                self.emit("api.response", {
                    "error": f"API 返回错误: {response.status_code}"
                })
                
        except Exception as e:
            self.emit("api.response", {
                "error": f"API 调用失败: {e}"
            })

def node_main():
    from matrix.bus.message_bus import bus
    node = ApiNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
