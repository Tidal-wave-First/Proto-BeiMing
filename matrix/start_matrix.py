"""矩阵生态启动器 + Railway 心跳服务"""
import sys, os, time, threading
from flask import Flask
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from matrix.bus.message_bus import bus

NODES = [
    "think_node",
    "cortex_node", 
    "swift_node",
    "lab_node",
    "api_node"
]

app = Flask(__name__)

@app.route('/')
def heartbeat():
    return "Kunpeng Matrix is running", 200

def start_nodes():
    print("[Matrix] ===== 鲲鹏矩阵生态启动 =====")
    for name in NODES:
        try:
            module = __import__(f"matrix.nodes.{name}", fromlist=['node_main'])
            t = threading.Thread(target=module.node_main, daemon=True)
            t.start()
            print(f"[Matrix] ✓ {name} 已加入矩阵")
        except Exception as e:
            print(f"[Matrix] ✗ {name} 启动失败: {e}")
    print("[Matrix] 所有节点已就绪")

def main():
    start_nodes()
    port = int(os.environ.get("PORT", 5000))
    print(f"[Matrix] 心跳服务器已启动，监听端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()
