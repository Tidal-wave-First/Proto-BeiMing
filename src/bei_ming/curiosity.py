"""
好奇心引擎 - 课程规划师 + Token预算
"""
import random, re, os, requests
from collections import defaultdict
from itertools import combinations
from .token_budget import budget

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
HAS_API = bool(API_KEY)

class CuriosityEngine:
    def __init__(self, cortex, model="qwen2.5:7b"):
        self.cortex = cortex
        self.model = model
        self.learning_path = []
        self.path_index = 0

    def generate_topics(self, max_topics=3):
        if self.learning_path and self.path_index < len(self.learning_path):
            topic = [self.learning_path[self.path_index]]
            self.path_index += 1
            return topic
        
        if HAS_API and budget.can_consume(300):
            new_path = self.plan_learning_path(5)
            if new_path:
                self.learning_path = new_path
                self.path_index = 1
                return [self.learning_path[0]]
        
        return self._fallback_topics(max_topics)

    def plan_learning_path(self, n=5):
        memory_summaries = [m['content'][:80] for m in self.cortex.memory[-30:]]
        if not memory_summaries: return None
        prompt = f"""你是自主学习规划师。我当前的知识片段如下：
{chr(10).join(memory_summaries)}

请为我规划一条有逻辑递进关系的学习路径，包含 {n} 个主题。
要求：
- 主题应基于我现有知识的薄弱环节
- 彼此之间应有从基础到高级、从现象到原理的递进关系
- 每个主题是一个适合网络搜索的短语
- 直接输出主题，每行一个，不要编号或解释"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 200}
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions",
                                 headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                tokens = data.get("usage", {}).get("total_tokens", 200)
                budget.consume(tokens)
                topics = [line.strip() for line in data["choices"][0]["message"]["content"].strip().split('\n') if line.strip()]
                return topics[:n]
        except:
            pass
        return None

    def _fallback_topics(self, max_topics):
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
        candidates = [(w, concepts[w], connectivity[w]) for w in concepts if connectivity[w] < 2]
        candidates.sort(key=lambda x: x[1], reverse=True)
        topics = [c[0] for c in candidates[:max_topics]]
        return topics if topics else self._seed_topics()

    def _seed_topics(self):
        seeds = ["认知偏差", "逻辑谬误", "科学方法", "系统思维", "博弈论"]
        random.shuffle(seeds)
        return seeds[:3]

    def get_concepts(self):
        return self.cortex.get_concepts()
