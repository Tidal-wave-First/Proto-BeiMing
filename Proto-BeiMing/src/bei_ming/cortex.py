"""
大脑皮层 - 北冥之渊（容量10GB）
深蓄记忆，只存抽象后的印象、规律与实验史。
“北冥有鱼，其名为鲲。鲲之大，不知其几千里也。”
这里只存精华，原始浊流尽弃。
"""
import json
import os
import time
from .utils import estimate_size, dir_size

class Cortex:
    def __init__(self, storage_path="./data/cortex", max_bytes=10 * 1024 * 1024 * 1024):
        self.storage_path = storage_path
        self.max_bytes = max_bytes
        self.memory_file = os.path.join(storage_path, "memory.json")
        os.makedirs(storage_path, exist_ok=True)
        # 记忆库结构：列表，每项 dict:
        # {
        #   "id": str,
        #   "type": "impression"|"rule"|"history",
        #   "content": str,            # 抽象后的文本描述
        #   "embedding": list|None,    # 可选，向量存储位置或值
        #   "importance": float,       # 重要性评分 (0-1)
        #   "access_count": int,
        #   "last_accessed": float,
        #   "created_at": float,
        #   "size_estimate": int       # 预估大小
        # }
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
        """存入一条抽象知识"""
        entry = {
            "id": str(time.time()) + "_" + str(len(self.memory)),
            "type": ktype,
            "content": content,
            "importance": importance,
            "access_count": 0,
            "last_accessed": time.time(),
            "created_at": time.time(),
            "size_estimate": len(content.encode('utf-8'))  # 粗略字节估算
        }
        self.memory.append(entry)
        self._save()

    def retrieve(self, query_text, top_k=5):
        """根据查询文本检索最相关的记忆（简单关键词匹配，实际可用向量检索）"""
        results = []
        for mem in self.memory:
            if query_text.lower() in mem['content'].lower():
                results.append(mem)
                mem['access_count'] += 1
                mem['last_accessed'] = time.time()
        # 按重要性 × 最近访问时间加权排序（简单）
        results.sort(key=lambda x: x['importance'] * (1 + x['access_count']), reverse=True)
        self._save()
        return results[:top_k]

    def current_size(self):
        """当前皮层数据大小（字节），使用文件总大小估算"""
        return dir_size(self.storage_path)

    def get_memory_list(self):
        return self.memory
