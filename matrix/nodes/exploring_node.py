"""矩阵节点: exploring_node —— 独立运行，通过总线通信"""
import sys, os
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.nodes.base_node import MatrixNode

class exploring_node_impl(MatrixNode):
    def __init__(self, bus):
        super().__init__("exploring_node", bus)
    
    def tick(self):
        # TODO: 接入对应的功能模块
        pass

# 启动入口
if __name__ == "__main__":
    from matrix.bus.message_bus import bus
    node = exploring_node_impl(bus)
    node.start()
