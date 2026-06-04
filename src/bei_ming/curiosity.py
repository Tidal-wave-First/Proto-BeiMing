"""
好奇心引擎 - 无ollama依赖版
"""
import random
import re
import os
import requests
from collections import defaultdict
from itertools import combinations

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
HAS_API = bool(API_KEY)

class CuriosityEngine:
    def __init__(self, cortex, model="qwen2.5:7b"):
        self.cortex = cortex
        self.model = model

    def generate_topics(self, max_topics=3):
        if HAS_API:
            path = self.plan_learning_path(max_topics)
            if path:
                return path
        concepts = self.cortex.get_concepts()
        if len(concepts) < 5:
            return self._seed_topics()
        cooccur = defaultdict(int)
        concept_list = list(concepts.keys())
        for mem in self.cortex.memory:
            mem_words = set()
            text = mem.get('content', '')
            for w in concept_list:
                if w in text:
                    mem_words.add(w)
            for a, b in combinations(mem_words, 2):
                key = tuple(sorted([a, b]))
                cooccur[key] += 1
        connectivity = defaultdict(int)
        for (a, b), cnt in cooccur.items():
            connectivity[a] += 1
            connectivity[b] += 1
        candidates = []
        for w in concepts:
            freq = concepts[w]
            conn = connectivity[w]
            if conn < 2:
                candidates.append((w, freq, conn))
        candidates.sort(key=lambda x: x[1], reverse=True)
        topics = [c[0] for c in candidates[:max_topics]]
        if not topics:
            low_conn = sorted(connectivity.items(), key=lambda x: x[1])[:10]
            if len(low_conn) >= 2:
                a, b = random.sample(low_conn, 2)
                topics.append(f"{a[0]}与{b[0]}的关系")
        return topics[:max_topics] if topics else self._seed_topics()

    def plan_learning_path(self, n=3):
        memory_summaries = [m['content'][:100] for m in self.cortex.memory[-20:]]
        prompt = f"""你是自主学习规划师。根据我当前的知识片段，请推荐接下来最值得学习的3个主题。
要求：主题应基于现有知识的薄弱环节，并且彼此之间有逻辑递进关系。直接输出主题短语，每行一个。

当前知识片段：
{chr(10).join(memory_summaries)}"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.5, "max_tokens": 100}
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                topics = [line.strip() for line in data["choices"][0]["message"]["content"].strip().split('\n') if line.strip()]
                return topics[:n]
        except:
            pass
        return None

    def _seed_topics(self):
        seeds = ["认知偏差", "逻辑谬误", "科学方法", "系统思维", "博弈论"]
        random.shuffle(seeds)
        return seeds[:3]

    def get_concepts(self):
        return self.cortex.get_concepts()
