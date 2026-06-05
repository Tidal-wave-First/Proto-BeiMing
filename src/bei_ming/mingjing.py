"""
明镜自我反思引擎 - 鲲之自鉴 (Ming Jing)
定期诊断自身局限，规划升级路径。
"""
import re, time, threading, requests, os
from .token_budget import budget

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
HAS_API = bool(API_KEY)

class MingJing:
    def __init__(self, cortex, engine):
        self.cortex = cortex
        self.engine = engine
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(">> 明镜引擎启动，鲲将定期审视自身局限。")

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()

    def _loop(self):
        time.sleep(300)  # 启动后等待5分钟
        while self.running:
            self.reflect()
            time.sleep(21600)  # 每6小时一次

    def reflect(self):
        if not HAS_API or not budget.can_consume(800):
            print(">> [明镜] 预算不足，跳过自我反思。")
            return

        # 1. 收集失败案例
        failures = []
        for mem in self.cortex.memory:
            if any(tag in mem.get('content', '') for tag in ['待验证', '反驳', '统计']):
                failures.append(mem['content'][:100])
            if mem.get('importance', 0.5) < 0.4:
                failures.append(mem['content'][:100])

        if len(failures) < 3:
            print(">> [明镜] 失败案例不足，暂不反思。")
            return

        # 2. 归纳能力短板
        prompt = f"""你是一位能力诊断师。我的学生（一个AI）在认知上有以下弱项和失败案例：
{chr(10).join(failures[:10])}

请归纳出它目前最突出的3个能力短板，并为每个短板给出一个具体的学习主题。
格式：
[短板1] <能力维度> -> 学习主题：<主题>
[短板2] <能力维度> -> 学习主题：<主题>
[短板3] <能力维度> -> 学习主题：<主题>"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 300}
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code != 200: return
            data = resp.json()
            analysis = data["choices"][0]["message"]["content"].strip()
            tokens = data.get("usage", {}).get("total_tokens", 500)
            budget.consume(tokens)
        except:
            return

        # 3. 解析并存储
        weaknesses = []
        for line in analysis.split('\n'):
            match = re.search(r'\[短板\d\]\s*(.+?)\s*->\s*学习主题：\s*(.+)', line)
            if match:
                dimension = match.group(1).strip()
                topic = match.group(2).strip()
                weaknesses.append((dimension, topic))

        for dim, topic in weaknesses:
            self.cortex.store(
                content=f"[明镜] 能力短板：{dim}。建议学习：{topic}",
                ktype="rule",
                importance=0.9
            )

        # 4. 生成自测问题
        for dim, topic in weaknesses[:2]:
            question = f"请解释：{topic}，并举例说明。"
            self.cortex.store(
                content=f"[自测] {question}",
                ktype="history",
                importance=0.7
            )

        print(f">> [明镜] 自我反思完成，发现 {len(weaknesses)} 个短板。")

        # 5. 将学习主题反馈给好奇心引擎
        if hasattr(self.engine, 'curiosity') and self.engine.curiosity:
            for _, topic in weaknesses:
                self.engine.curiosity.learning_path.append(topic)
