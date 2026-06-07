"""矩阵节点: think_node —— 双引擎推理（运行时读取.env，零模块级依赖）"""
import sys, os, time, requests, json
sys.path.insert(0, 'D:/SwiftAssistant')
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')

from matrix.nodes.base_node import MatrixNode
from thinking_core.local_llm import LocalLLM

class ThinkNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("think_node", bus)
        self.model_path = 'D:/SwiftAssistant/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf'
        self.local_llm = None
        self.api_key = ""
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
        # 运行时直接读取 .env
        self._load_api_key()
        print(f"[think_node] 能源核心加载完毕。Key状态: {'有效' if self.api_key else '缺失'}")
        
    def _load_api_key(self):
        env_path = 'D:/Proto-BeiMing-北冥/.env'
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key == 'DEEPSEEK_API_KEY':
                            self.api_key = value
                            print(f"[think_node] 已从.env读取到API Key: {value[:12]}...")
                            return
        print("[think_node] 警告: .env中未找到DEEPSEEK_API_KEY")
        
    def on_start(self):
        print(f"[think_node] 双引擎推理节点启动")
        print(f"[think_node] 主引擎: DeepSeek API (deepseek-chat)")
        
        try:
            os.chdir('D:/SwiftAssistant')
            self.local_llm = LocalLLM(model_path=self.model_path)
            print(f"[think_node] 回退引擎: TinyLlama 已就绪")
        except Exception as e:
            print(f"[think_node] 本地模型加载失败（可忽略）: {e}")
        
        self.listen("think.request", self.handle_think_request)
    
    def handle_think_request(self, payload, sender):
        prompt = payload.get("prompt", "")
        system_prompt = payload.get("system_prompt", "你是短剧编剧，擅长反转。请用中文回复。")
        request_id = payload.get("request_id", "unknown")
        
        print(f"[think_node] 收到请求 from {sender}: {prompt[:50]}...")
        
        if self.api_key:
            print(f"[think_node] 正在调用 DeepSeek API...")
            response = self._think_api(prompt, system_prompt)
        else:
            print(f"[think_node] 使用本地模型进行推理...")
            response = self._think_local(prompt, system_prompt)
        
        self.emit("think.response", {
            "request_id": request_id,
            "response": response,
            "prompt": prompt
        })
        
        self.emit("cortex.store", {
            "type": "thought",
            "content": response[:500],
            "tags": ["thought", "script"]
        })
    
    def _think_api(self, prompt, system_prompt):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.8
            }
            resp = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[think_node] API失败: {e}")
            return f"API调用失败: {e}"
    
    def _think_local(self, prompt, system_prompt):
        try:
            return self.local_llm.chat(prompt, system_prompt=system_prompt)
        except Exception as e:
            return f"本地推理失败: {e}"

def node_main():
    from matrix.bus.message_bus import bus
    node = ThinkNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
