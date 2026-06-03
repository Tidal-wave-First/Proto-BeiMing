"""
好奇心引擎 - 无 LLM 回退版
"""
import random
import re
from collections import defaultdict
from itertools import combinations

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

class CuriosityEngine:
    def __init__(self, cortex, model="qwen2.5:7b"):
        self.cortex = cortex
        self.model = model

    def generate_topics(self, max_topics=3):
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
        if not topics:
            topics = self._seed_topics()
        if HAS_OLLAMA:
            polished = self._polish_topics(topics[:max_topics])
            filtered = [t for t in polished if self._is_valid_topic(t)]
            if filtered:
                return filtered
        return self._seed_topics()

    def _is_valid_topic(self, topic):
        words = re.findall(r'[\u4e00-\u9fff]{2,}', topic)
        return len(words) >= 2 and len(topic) >= 6

    def _seed_topics(self):
        seeds = ["认知偏差的类型及其影响", "逻辑谬误在日常生活中的实例", "科学方法与批判性思维",
                 "系统思维如何应用于管理", "博弈论中的经典案例", "人工智能的伦理边界",
                 "熵的概念及其跨学科应用", "反馈循环在社会系统中的作用", "自组织现象的原理"]
        random.shuffle(seeds)
        return seeds[:3]

    def _polish_topics(self, concepts):
        if not concepts: return concepts
        prompt = f"""你是好奇的学习者。将概念词转化为适合网络搜索的问题或短语，每个一行。
概念词：{', '.join(concepts)}"""
        try:
            resp = ollama.generate(model=self.model, prompt=prompt)
            lines = resp['response'].strip().split('\n')
            topics = [line.strip('- ').strip() for line in lines if line.strip()]
            return topics[:len(concepts)]
        except:
            return concepts
