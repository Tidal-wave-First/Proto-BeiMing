"""
AlphaGo式思辨对弈引擎 - 鲲之自弈 (Alpha Loop)
在后台自我对弈：提取模板→生成对立命题→辩论→发现漏洞→扬弃
"""
import random, re, time, threading, requests, os
from .token_budget import budget

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
HAS_API = bool(API_KEY)

class AlphaLoop:
    def __init__(self, cortex, imagination, laboratory):
        self.cortex = cortex
        self.imagination = imagination
        self.laboratory = laboratory
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(">> 思辨对弈引擎启动，鲲将开始自我辩论。")

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()

    def _loop(self):
        time.sleep(120)  # 启动后等待2分钟
        while self.running:
            self.self_play()
            time.sleep(7200)  # 每2小时一次

    def self_play(self):
        if not HAS_API or not budget.can_consume(1000):
            print(">> [自弈] 预算不足，跳过本轮。")
            return

        # 1. 提取思维模板
        thinking_mems = [m for m in self.cortex.memory if '[思维]' in m.get('content', '')]
        if not thinking_mems:
            return
        template_mem = random.choice(thinking_mems)
        template_content = template_mem['content']
        template_match = re.search(r'\[模板\]\s*(.+?)(?:\n|$)', template_content)
        if not template_match:
            return
        template = template_match.group(1)

        # 2. 生成对立命题
        prompt = f"""你是一个辩论赛的出题人。以下是学生掌握的一个思维模板：
“{template[:200]}”

请基于这个模板，生成一个具体的辩论题目。要求：
- 题目必须包含正反两个对立观点
- 格式：[正方观点] <一句话> [反方观点] <一句话>
直接输出，不要解释。"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 200}
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if resp.status_code != 200:
                return
            data = resp.json()
            debate_topic = data["choices"][0]["message"]["content"].strip()
            tokens = data.get("usage", {}).get("total_tokens", 300)
            budget.consume(tokens)
        except:
            return

        # 解析正反观点
        positive_match = re.search(r'\[正方观点\]\s*(.+?)(?:\n|\[)', debate_topic)
        negative_match = re.search(r'\[反方观点\]\s*(.+?)$', debate_topic)
        if not positive_match or not negative_match:
            return
        positive = positive_match.group(1).strip()
        negative = negative_match.group(1).strip()

        print(f">> [自弈] 辩论题目：正方={positive} 反方={negative}")

        # 3. 自我对弈（简化为两轮：正方立论，反方反驳，正方再驳）
        debate_log = f"[正方立论] {positive}\n"
        # 反方反驳（请求DeepSeek生成）
        rebuttal_prompt = f"""你扮演反方辩手，反驳以下正方观点。请提出一个有力的反驳点。
正方观点：{positive}
反方反驳："""
        resp2 = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers,
                              json={"model": "deepseek-chat", "messages": [{"role": "user", "content": rebuttal_prompt}], "temperature": 0.6, "max_tokens": 200}, timeout=20)
        if resp2.status_code == 200:
            rebuttal = resp2.json()["choices"][0]["message"]["content"].strip()
            debate_log += f"[反方反驳] {rebuttal}\n"
            budget.consume(resp2.json().get("usage", {}).get("total_tokens", 200))

            # 正方再驳
            surrebuttal_prompt = f"""你扮演正方辩手，回应反方的反驳。请提出一个更深入的反驳。
反方反驳：{rebuttal}
正方再驳："""
            resp3 = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers,
                                  json={"model": "deepseek-chat", "messages": [{"role": "user", "content": surrebuttal_prompt}], "temperature": 0.6, "max_tokens": 200}, timeout=20)
            if resp3.status_code == 200:
                surrebuttal = resp3.json()["choices"][0]["message"]["content"].strip()
                debate_log += f"[正方再驳] {surrebuttal}\n"
                budget.consume(resp3.json().get("usage", {}).get("total_tokens", 200))

        # 4. 漏洞发现
        analysis_prompt = f"""你是一位逻辑分析师。以下是刚刚结束的一场辩论记录：
{debate_log}

请找出双方论点中存在的逻辑漏洞、知识盲区，并给出改进建议。
格式：[漏洞] <描述> [建议] <改进方向>"""
        resp4 = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers,
                              json={"model": "deepseek-chat", "messages": [{"role": "user", "content": analysis_prompt}], "temperature": 0.3, "max_tokens": 300}, timeout=20)
        if resp4.status_code == 200:
            analysis = resp4.json()["choices"][0]["message"]["content"].strip()
            budget.consume(resp4.json().get("usage", {}).get("total_tokens", 300))
        else:
            analysis = "无法完成分析。"

        # 5. 扬弃与升级
        self.cortex.store(
            content=f"[自弈] 辩论：{positive} vs {negative}\n[分析] {analysis[:300]}",
            ktype="rule",
            importance=0.9
        )
        print(f">> [自弈] 完成一轮辩论。漏洞分析已存入皮层。")

        # 6. 向创造者提建议（如果发现根本性缺陷）
        if "代码" in analysis or "算法" in analysis or "逻辑缺陷" in analysis:
            self.cortex.store(
                content=f"[建议] 自弈中发现潜在问题：{analysis[:200]}",
                ktype="history",
                importance=1.0
            )
