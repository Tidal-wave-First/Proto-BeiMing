"""
大脑皮层 - 北冥之渊（增强概念提取）
"""
import json
import os
import time
import re
from .utils import dir_size

class Cortex:
    def __init__(self, storage_path="./data/cortex", max_bytes=10 * 1024 * 1024 * 1024):
        self.storage_path = storage_path
        self.max_bytes = max_bytes
        self.memory_file = os.path.join(storage_path, "memory.json")
        os.makedirs(storage_path, exist_ok=True)
        self.memory = self._load()

    def _load(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)

    def store(self, content, ktype="impression", importance=0.5):
        entry = {
            "id": str(time.time()) + "_" + str(len(self.memory)),
            "type": ktype,
            "content": content,
            "importance": importance,
            "access_count": 0,
            "last_accessed": time.time(),
            "created_at": time.time(),
            "size_estimate": len(content.encode('utf-8'))
        }
        self.memory.append(entry)
        self._save()

    def retrieve(self, query_text, top_k=5):
        results = []
        for mem in self.memory:
            if query_text.lower() in mem['content'].lower():
                results.append(mem)
                mem['access_count'] += 1
                mem['last_accessed'] = time.time()
        results.sort(key=lambda x: x['importance'] * (1 + x['access_count']), reverse=True)
        self._save()
        return results[:top_k]

    def current_size(self):
        return dir_size(self.storage_path)

    def get_memory_list(self):
        return self.memory

    def get_concepts(self, min_length=2):
        """提取所有记忆中的中文概念词（出现频次>=2）"""
        concepts = {}
        for mem in self.memory:
            text = mem.get('content', '')
            words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
            for w in words:
                concepts[w] = concepts.get(w, 0) + 1
        return {w: c for w, c in concepts.items() if c >= min_length}
