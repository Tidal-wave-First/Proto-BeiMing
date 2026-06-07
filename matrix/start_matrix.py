"""矩阵生态启动器 —— 启动所有核心节点，包括短剧工作台"""
import sys, os, time, threading
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.bus.message_bus import bus

# 需要启动的核心节点（按顺序）
NODES = [
    "think_node",
    "cortex_node",
    "swift_node",
    "lab_node",
    "api_node"
]

def main():
    print("[Matrix] ===== 鲲鹏矩阵生态启动（短剧工作台模式）=====")
    
    threads = []
    for name in NODES:
        try:
            module = __import__(f"matrix.nodes.{name}", fromlist=['node_main'])
            t = threading.Thread(target=module.node_main, daemon=True)
            t.start()
            threads.append(t)
            print(f"[Matrix] ✓ {name} 已加入矩阵")
        except Exception as e:
            print(f"[Matrix] ✗ {name} 启动失败: {e}")
    
    print("[Matrix] 所有节点已就绪，矩阵生态正在运行...")
    
    # 主线程保活
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("[Matrix] 矩阵关闭")

if __name__ == "__main__":
    main()
