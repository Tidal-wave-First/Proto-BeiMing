"""矩阵生态启动器 —— 启动所有已填充的节点"""
import sys, os
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')

print("[Matrix] ===== 鲲鹏矩阵生态启动 =====")
print("[Matrix] 正在唤醒各节点...")
print()

# 节点启动顺序：先启动基础设施，再启动上层应用
nodes_to_start = [
    "cortex_node",   # 记忆皮层（基础设施）
    "swift_node",    # 数据感官
    "lab_node",      # 沙盒实验室
    "think_node",    # 本地推理（需要先加载模型）
    "api_node",      # 外部网关
    "brain_node",    # 试错学习中枢（最后启动，连接所有节点）
]

import importlib, threading, time

started = []
for node_name in nodes_to_start:
    try:
        module = importlib.import_module(f"matrix.nodes.{node_name}")
        t = threading.Thread(target=module.node_main, daemon=True, name=node_name)
        t.start()
        started.append(node_name)
        print(f"  [✓] {node_name}")
    except Exception as e:
        print(f"  [✗] {node_name}: {e}")

print()
print(f"[Matrix] 已启动 {len(started)}/{len(nodes_to_start)} 个节点")
print("[Matrix] 鲲鹏正在矩阵中成长...")
print()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[Matrix] 收到关闭信号，鲲鹏进入休眠状态。")
