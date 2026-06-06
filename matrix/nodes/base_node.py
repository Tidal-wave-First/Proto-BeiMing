"""矩阵节点基类 —— 每个模块继承此基类，作为独立节点运行"""
import threading
from typing import Any

class MatrixNode:
    def __init__(self, name: str, bus):
        self.name = name
        self.bus = bus
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
    
    def start(self):
        print(f"[{self.name}] 节点启动")
        self.thread.start()
    
    def _loop(self):
        while self.running:
            self.tick()
    
    def tick(self):
        """子类重写此方法，实现各自的核心循环"""
        pass
    
    def emit(self, topic: str, payload: Any):
        self.bus.publish(topic, payload, sender=self.name)
    
    def listen(self, topic: str, callback):
        self.bus.subscribe(topic, callback)
    
    def stop(self):
        self.running = False
