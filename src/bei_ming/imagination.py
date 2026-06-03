import time
from collections import deque
from .utils import estimate_size

class ImaginationSpace:
    def __init__(self, max_bytes=1 * 1024 * 1024 * 1024):
        self.buffer = deque()
        self.max_size = max_bytes
        self.current_size = 0

    def add(self, item, meta=None):
        record = {
            'timestamp': time.time(),
            'content': item,
            'meta': meta or {},
            'size': estimate_size(item)
        }
        while self.current_size + record['size'] > self.max_size and self.buffer:
            old = self.buffer.popleft()
            self.current_size -= old['size']
        self.buffer.append(record)
        self.current_size += record['size']

    def get_recent(self, n=10):
        items = list(self.buffer)[-n:]
        return [i['content'] for i in items]

    def clear(self):
        self.buffer.clear()
        self.current_size = 0

    def __len__(self):
        return len(self.buffer)
