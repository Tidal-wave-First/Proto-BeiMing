"""
知识织网师 - 鲲之经络 (Weaver)
定期调用API，找出皮层知识间深层联系，生成原理/框架类认知。
"""
import os
import requests
import time
import threading

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
HAS_API = bool(API_KEY)

class KnowledgeWeaver:
    def __init__(self, cortex, interval_minutes=120):
        self.cortex = cortex
        self.interval = interval_minutes * 60
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(">> 知识织网师已启动")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _loop(self):
        while self.running:
            self.weave()
            time.sleep(self.interval)

    def weave(self):
        if not HAS_API: return
        # 获取最近10条高质量记忆（类型为rule）
        rules = [m for m in self.cortex.memory if m['type'] == 'rule']
        if len(rules) < 5: return
        recent = sorted(rules, key=lambda x: x.get('created_at', 0), reverse=True)[:10]
        contents = [m['content'][:100] for m in recent]
        prompt = f"""你是知识关联专家。以下是我最近学到的知识：
{chr(10).join(['- '+c for c in contents])}

请找出这些知识之间的深层联系，归纳出一个更高层次的原理或框架（一句话即可）。
格式：[高层原则] <你的归纳>"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 150
        }
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions",
                                 headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                result = data["choices"][0]["message"]["content"].strip()
                if result.startswith("[高层原则]"):
                    principle = result[6:].strip()
                    self.cortex.store(
                        content=f"[原理] {principle}",
                        ktype="rule",
                        importance=0.95
                    )
                    print(f">> 织网师发现新原理：{principle}")
        except:
            pass
