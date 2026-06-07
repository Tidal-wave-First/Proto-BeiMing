"""矩阵生态启动器 + Railway 健康检查服务器"""
import sys, os, time, threading, json
from http.server import HTTPServer, BaseHTTPRequestHandler

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from matrix.bus.message_bus import bus

NODES = [
    "think_node",
    "cortex_node",
    "swift_node",
    "lab_node",
    "api_node"
]

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kunpeng Matrix is alive")
    
    def log_message(self, format, *args):
        pass  # 静默日志

def start_health_server():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"[Matrix] 心跳服务器已启动，监听端口 {port}")
    server.serve_forever()

def start_nodes():
    print("[Matrix] ===== 鲲鹏矩阵生态启动（短剧工作台模式）=====")
    for name in NODES:
        try:
            module = __import__(f"matrix.nodes.{name}", fromlist=['node_main'])
            t = threading.Thread(target=module.node_main, daemon=True)
            t.start()
            print(f"[Matrix] ✓ {name} 已加入矩阵")
        except Exception as e:
            print(f"[Matrix] ✗ {name} 启动失败: {e}")
    print("[Matrix] 所有节点已就绪，矩阵生态正在运行...")

def main():
    # 启动节点线程
    node_thread = threading.Thread(target=start_nodes, daemon=True)
    node_thread.start()
    # 主线程运行健康检查服务器
    start_health_server()

if __name__ == "__main__":
    main()
