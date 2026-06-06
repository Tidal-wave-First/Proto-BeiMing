"""矩阵消息总线 —— 所有节点通过此总线通信，不直接调用"""
import json
import threading
import time
from collections import defaultdict
from typing import Callable, Dict, List, Any

class MatrixBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_log: List[Dict] = []
        self.lock = threading.Lock()
    
    def publish(self, topic: str, payload: Any, sender: str = "unknown"):
        with self.lock:
            event = {
                "topic": topic,
                "payload": payload,
                "sender": sender,
                "timestamp": time.time()
            }
            self.event_log.append(event)
            # 保留最近1000条
            if len(self.event_log) > 1000:
                self.event_log = self.event_log[-500:]
        
        for callback in self.subscribers.get(topic, []):
            try:
                callback(payload, sender)
            except Exception as e:
                print(f"[Bus] 订阅者回调错误: {e}")

    def subscribe(self, topic: str, callback: Callable):
        self.subscribers[topic].append(callback)
    
    def get_log(self, limit: int = 20):
        return self.event_log[-limit:]

bus = MatrixBus()
print("[Matrix Bus] 消息总线已启动")
