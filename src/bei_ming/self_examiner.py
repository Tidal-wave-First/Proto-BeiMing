"""
自我考官 - 鲲之自省 + Token预算
"""
import os, requests, time, threading
from .token_budget import budget

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
HAS_API = bool(API_KEY)

class SelfExaminer:
    def __init__(self, cortex, engine, interval_minutes=180):
        self.cortex = cortex
        self.engine = engine
        self.interval = interval_minutes * 60
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(">> 自我考官已启动")

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()

    def _loop(self):
        while self.running:
            self.examine()
            time.sleep(self.interval)

    def examine(self):
        if not HAS_API: return
        if not budget.can_consume(400):
            print(">> [考官] 预算不足，跳过")
            return

        rules = [m for m in self.cortex.memory if m['type'] == 'rule']
        if len(rules) < 5: return
        recent = sorted(rules, key=lambda x: x.get('created_at', 0), reverse=True)[:10]
        contents = [m['content'][:120] for m in recent]
        prompt = f"""你是严格的逻辑考官。基于以下我脑中的知识，请生成3个自测问题来检验我是否真正理解。
每个问题之后，请用一句话给出你期望的正确答案。
格式：
问题1：<问题>
答案1：<答案>
问题2：<问题>
答案2：<答案>
问题3：<问题>
答案3：<答案>

我的知识：
{chr(10).join(['- '+c for c in contents])}"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 300}
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions",
                                 headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                result = data["choices"][0]["message"]["content"].strip()
                tokens = data.get("usage", {}).get("total_tokens", 400)
                budget.consume(tokens)
                self.cortex.store(
                    content=f"[自省] {result[:200]}",
                    ktype="history",
                    importance=0.7
                )
                print(">> 自我考官完成一轮自测")
        except:
            pass
