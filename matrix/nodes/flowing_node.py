"""矩阵节点: flowing_node —— Streamlit 短剧创作工作台"""
import sys, os, time, json
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')

# 尝试导入 streamlit
try:
    import streamlit as st
except ImportError:
    print("[flowing_node] Streamlit 未安装。工作台不可用。请在requirements.txt中添加streamlit并重新部署。")
    st = None

from matrix.nodes.base_node import MatrixNode
from matrix.bus.message_bus import bus

class FlowingNode(MatrixNode):
    def __init__(self, bus):
        super().__init__("flowing_node", bus)
        self.pending_responses = {}
        self.script_versions = []
        self.current_idea = ""
        
    def on_start(self):
        """启动 Streamlit 工作台"""
        if st is None:
            print("[flowing_node] 由于缺少 streamlit，工作台无法启动。")
            return
            
        print(f"[flowing_node] 短剧创作工作台正在启动，请稍后访问 http://localhost:8501")
        # Streamlit 会接管主线程，所以这里用子进程启动
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'matrix', 'nodes', 'flowing_app.py')
        # 确保文件存在
        if not os.path.exists(script_path):
             print(f"[flowing_node] 错误：找不到界面文件 {script_path}")
             return
        subprocess.Popen(['streamlit', 'run', script_path, '--server.port', '8501'])

def node_main():
    node = FlowingNode(bus)
    node.on_start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    node_main()
