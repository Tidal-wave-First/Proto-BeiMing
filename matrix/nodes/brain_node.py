"""矩阵节点: brain_node —— 试错学习中枢，协调所有节点并实现认知闭环"""
import sys, os, time, uuid
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.nodes.base_node import MatrixNode

class BrainNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("brain_node", bus)
        self.pending = {}  # 待处理的请求追踪
        
    def on_start(self):
        # 监听各种响应，形成闭环
        self.listen("think.response", self.on_think_done)
        self.listen("lab.result", self.on_lab_done)
        self.listen("cortex.result", self.on_cortex_done)
        self.listen("swift.features", self.on_swift_features)
        self.listen("api.response", self.on_api_done)
        
        # 启动后，主动进行一次自我思考测试
        print(f"[brain_node] 试错学习中枢已激活。开始首次思考...")
        self.think("什么是试错学习？用一句话回答")
    
    def think(self, prompt, use_api=False):
        """发送思考请求"""
        request_id = str(uuid.uuid4())[:8]
        self.pending[request_id] = {"prompt": prompt, "time": time.time()}
        
        if use_api:
            self.emit("api.request", {"prompt": prompt, "request_id": request_id})
        else:
            self.emit("think.request", {"prompt": prompt, "request_id": request_id})
    
    def on_think_done(self, payload, sender):
        """收到本地模型的思考结果"""
        response = payload.get("response", "")
        request_id = payload.get("request_id", "")
        print(f"[brain_node] 本地大脑思考结果: {response[:100]}...")
        
        # 存储到皮层
        self.emit("cortex.store", {
            "type": "thought",
            "content": response,
            "tags": ["thought", "local_llm", request_id]
        })
        
        # 提取特征并分析
        self.emit("swift.extract", {"text": response})
        
        # 学习环路：用同一个问题问外部API，对比学习
        if request_id in self.pending:
            original_prompt = self.pending[request_id]["prompt"]
            # 为了学习，用本地大脑的回答作为上下文，让外部API给出更好的答案
            enhanced_prompt = f"问题：{original_prompt}\n\n本地模型粗糙回答：{response}\n\n请给出一个更精确的回答，并说明你修改了什么。"
            self.emit("api.request", {"prompt": enhanced_prompt, "request_id": f"{request_id}_api"})
    
    def on_api_done(self, payload, sender):
        """收到外部API的结果，进行对比学习"""
        response = payload.get("response", "")
        error = payload.get("error", "")
        
        if error:
            print(f"[brain_node] API 调用失败: {error}")
            return
        
        print(f"[brain_node] 外部导师回答: {response[:100]}...")
        
        # 存储导师回答到皮层，并标记为“导师指导”
        self.emit("cortex.store", {
            "type": "mentor_guidance",
            "content": response,
            "tags": ["mentor", "api", "reference"]
        })
        
        # 这里可以触发“学习动作”：将本地模型与导师的差异存入知识库
        # 为未来的微型模型微调积累数据
    
    def on_lab_done(self, payload, sender):
        """收到实验室执行结果"""
        output = payload.get("output", "")
        error = payload.get("error", "")
        
        if error:
            print(f"[brain_node] 实验室报错: {error[:100]}")
            # 将错误存入皮层，作为“失败经验”
            self.emit("cortex.store", {
                "type": "error_experience",
                "content": error,
                "tags": ["error", "lab", "mistake"],
                "error_flag": True
            })
        else:
            print(f"[brain_node] 实验室执行成功: {output[:50] if output else '无输出'}...")
    
    def on_cortex_done(self, payload, sender):
        """收到皮层检索结果（可用于后续推理）"""
        results = payload.get("results", [])
        if results:
            print(f"[brain_node] 检索到 {len(results)} 条相关记忆")
    
    def on_swift_features(self, payload, sender):
        """收到特征提取结果"""
        if payload.get("has_error"):
            print(f"[brain_node] 检测到错误信号，触发关注...")
            # 可以在这里触发更深入的错误分析

def node_main():
    from matrix.bus.message_bus import bus
    node = BrainNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
