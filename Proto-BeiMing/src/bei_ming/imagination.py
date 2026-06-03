"""
想象空间 - 九万里风（取自“抟扶摇而上者九万里”）
容量：1GB 工作记忆，高速暂存当前思考的原始材料、假设与实验数据。
断电可丢失，但运行时的每一次振翅都倚仗此风。
"""
import time
from collections import deque
from .utils import estimate_size

class ImaginationSpace:
    def __init__(self, max_bytes=1 * 1024 * 1024 * 1024):  # 1GB
        self.buffer = deque()
        self.max_size = max_bytes
        self.current_size = 0

    def add(self, item, meta=None):
        """将一段信息（原始文本、图像描述、假设等）放入想象空间"""
        record = {
            'timestamp': time.time(),
            'content': item,
            'meta': meta or {},
            'size': estimate_size(item)
        }
        # 若超限，移除最旧的内容，直到空间足够
        while self.current_size + record['size'] > self.max_size and self.buffer:
            old = self.buffer.popleft()
            self.current_size -= old['size']
        self.buffer.append(record)
        self.current_size += record['size']

    def get_recent(self, n=10):
        """获取最近放入的n条信息"""
        items = list(self.buffer)[-n:]
        return [i['content'] for i in items]

    def clear(self):
        self.buffer.clear()
        self.current_size = 0

    def __len__(self):
        return len(self.buffer)
