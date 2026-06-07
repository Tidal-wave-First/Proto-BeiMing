"""矩阵生态启动器 —— 适配 Railway 云端环境，自动处理路径"""
import sys, os, time, threading

# 关键修复：在导入任何矩阵模块前，将项目根目录加入 sys.path
# 确保无论是本地运行还是 Railway 容器，都能找到 matrix 包
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 也要确保上一级目录（项目根）在路径中
PARENT_DIR = os.path.dirname(PROJECT_ROOT)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

print(f"[Matrix] 项目根目录: {PARENT_DIR}")
print(f"[Matrix] Python路径: {sys.path[:3]}...")

from matrix.bus.message_bus import bus

# 需要启动的核心节点
NODES = [
    "think_node",
    "cortex_node",
    "swift_node",
    "lab_node",
    "api_node"
]

def main():
    print("[Matrix] ===== 鲲鹏矩阵生态启动（云端模式）=====")
    
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
