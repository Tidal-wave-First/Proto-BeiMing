"""矩阵节点: swift_node —— 短剧脚本格式化与素材整理（带响应监听）"""
import sys, os, time, json, re
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
sys.path.insert(0, 'D:/SwiftAssistant')
from matrix.nodes.base_node import MatrixNode

class SwiftNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("swift_node", bus)
        self.script_templates = {
            "反转": "【场景：{place}】\n{char_a}：{line_a}\n{char_b}：{line_b}\n【反转：{twist}】\n{char_a}：{reaction}",
            "冲突": "【冲突场景】\n背景：{background}\n{char_a}与{char_b}因{reason}发生争执\n高潮：{climax}\n结局：{ending}",
            "日常": "【日常】\n{char_a}在{place}{action}\n意外发现：{discovery}\n结果：{result}"
        }
        self.pending_requests = {}  # 存储等待响应的请求ID
        
    def on_start(self):
        self.listen("swift.format_script", self.handle_format_script)
        self.listen("swift.analyze_lines", self.handle_analyze_lines)
        self.listen("swift.generate_prompt", self.handle_generate_prompt)
        # 关键：监听 think.response，接住本地模型的思考结果
        self.listen("think.response", self.handle_think_response)
        print(f"[swift_node] 短剧创作引擎已激活（已安装响应监听器）")
    
    def handle_generate_prompt(self, payload, sender):
        """发送创作请求给 think_node"""
        topic = payload.get("topic", "短剧创作")
        request_id = payload.get("request_id", "unknown")
        
        prompt = f"请为一个短剧设计一个精彩的反转剧情，主题是：{topic}。要求：1个场景，2-3个角色，1个意外反转，台词简洁有力。请直接输出剧本，包含角色名和台词。"
        
        # 记录请求ID，等待响应
        self.pending_requests[request_id] = topic
        
        self.emit("think.request", {
            "request_id": request_id,
            "prompt": prompt,
            "system_prompt": "你是一个专业的短剧编剧，擅长设计反转和冲突。请用中文回复，直接输出剧本。"
        })
    
    def handle_think_response(self, payload, sender):
        """收到 think_node 的推理结果，进行格式化并存储"""
        request_id = payload.get("request_id", "unknown")
        response = payload.get("response", "")
        
        if not response or request_id not in self.pending_requests:
            return
        
        topic = self.pending_requests.pop(request_id)
        print(f"[swift_node] 收到剧本响应，正在格式化...")
        
        # 简单格式化：提取角色和台词，如果没有则直接使用原始响应
        formatted_script = response
        
        # 存入皮层
        self.emit("cortex.store", {
            "type": "script_draft",
            "content": formatted_script,
            "tags": ["script", "final", topic[:10]]
        })
        
        self.emit("swift.script_ready", {
            "request_id": request_id,
            "script": formatted_script
        })
        print(f"[swift_node] 剧本已格式化并存入皮层")

    def handle_format_script(self, payload, sender):
        template_name = payload.get("template", "反转")
        params = payload.get("params", {})
        request_id = payload.get("request_id", "unknown")
        
        template = self.script_templates.get(template_name, self.script_templates["反转"])
        try:
            script = template.format(**params)
            self.emit("cortex.store", {
                "type": "script_draft",
                "content": script,
                "tags": ["script", template_name]
            })
            self.emit("swift.script_ready", {"request_id": request_id, "script": script})
        except KeyError as e:
            self.emit("swift.script_ready", {"request_id": request_id, "error": f"缺少参数: {e}"})
    
    def handle_analyze_lines(self, payload, sender):
        script_text = payload.get("script", "")
        request_id = payload.get("request_id", "unknown")
        
        lines = re.findall(r'【([^】]+)】|([^：]+)：([^\n]+)', script_text)
        analysis = {
            "scene_count": len(re.findall(r'【([^】]+)】', script_text)),
            "characters": list(set(re.findall(r'([^：\n]+)：', script_text))),
            "line_count": len(re.findall(r'[^：\n]+：[^\n]+', script_text)),
            "word_count": len(script_text)
        }
        
        self.emit("swift.analysis_ready", {"request_id": request_id, "analysis": analysis})

def node_main():
    from matrix.bus.message_bus import bus
    node = SwiftNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
