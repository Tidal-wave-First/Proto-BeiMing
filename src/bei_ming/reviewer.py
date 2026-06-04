"""
自觉复盘器 - 鲲之温故 (Reviewer)
在空闲时自动复习皮层中的思维笔记，进行自我提问和演练。
"""
import random
import re
import time
import threading

class ConsciousReviewer:
    def __init__(self, cortex, engine, interval_minutes=30):
        self.cortex = cortex
        self.engine = engine
        self.interval = interval_minutes * 60
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(">> 自觉复盘器已启动，鲲将在静默中温故知新。")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _loop(self):
        while self.running:
            self.review()
            time.sleep(self.interval)

    def review(self):
        # 获取皮层中最近的 [思维] 记忆
        thinking_mems = [m for m in self.cortex.memory if '[思维]' in m.get('content', '')]
        if not thinking_mems:
            return

        # 随机选一条
        mem = random.choice(thinking_mems)
        content = mem['content']

        # 尝试提取模板
        template_match = re.search(r'\[模板\]\s*(.+?)(?:\n|$)', content)
        if template_match:
            template = template_match.group(1)
            # 用模板演练一个随机概念
            random_concepts = ["时间", "因果", "信息", "系统", "边界", "自由", "无限"]
            concept = random.choice(random_concepts)
            exercise = f"试着用思维模板分析：{concept}"
            # 尝试自己回答（基于皮层检索）
            relevant = self.cortex.retrieve(concept, top_k=3)
            if relevant:
                answer_snippet = '; '.join([r['content'][:80] for r in relevant if 'content' in r])
                review_result = f"[复盘] 我温习了思维模板：“{template[:100]}”，并用它分析了“{concept}”。我想到：{answer_snippet}"
            else:
                review_result = f"[复盘] 我温习了思维模板：“{template[:100]}”，并尝试用它分析“{concept}”，但暂时没有足够的相关知识。我将这个问题标记为待求解。"
        else:
            # 如果没有模板，就尝试自我提问
            question = f"关于“{content[:50]}”，我还能提出什么新问题？"
            review_result = f"[复盘] 我重读了思维笔记：“{content[:100]}”，并问自己：“{question}”。我暂时没有答案，但这个问题值得探索。"

        # 存入皮层
        self.cortex.store(
            content=review_result,
            ktype="history",
            importance=0.6
        )
        print(f">> 复盘完成：{review_result[:80]}...")
