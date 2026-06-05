"""
逍遥游引擎 - 矛盾思辨与自我升级 (Xiao Yao You)
在静默中循环：自省→质疑→求知→思辨→求镜→扬弃
"""
import random, re, time, threading, requests, os
from .token_budget import budget
from .senses import fetch_from_web  # 用于自主搜索

# 沙盒自我升级模拟（仅逻辑验证，不真正修改代码）
SANDBOX_CODE_TEMPLATE = """
# 假设我们按新认知设计一个简单函数
def test_logic():
    hypothesis = "{hypothesis}"
    fact = "{fact}"
    if hypothesis != fact:
        return "矛盾未解"
    return "逻辑自洽"
print(test_logic())
"""

class XiaoYaoYou:
    def __init__(self, cortex, imagination, laboratory, engine):
        self.cortex = cortex
        self.imagination = imagination
        self.laboratory = laboratory
        self.engine = engine  # 用于调用API和统计提取
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(">> 逍遥游引擎启动，鲲将开始内在辩证循环。")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _loop(self):
        time.sleep(60)  # 启动后先等待1分钟
        while self.running:
            self.cycle()
            time.sleep(1800)  # 每30分钟一次循环

    def cycle(self):
        """执行一次完整的辩证循环"""
        print(">> [逍遥游] 开始辩证循环...")
        contradictions = self._find_contradictions()
        if not contradictions:
            return

        for old_rule in contradictions[:2]:  # 一次最多处理2对矛盾
            question = self._generate_question(old_rule)
            materials = self._search_for_truth(question)
            local_analysis = self._local_reason(question, materials, old_rule)
            feedback = self._consult_deepseek(local_analysis, question)
            self._synthesize(old_rule, feedback, question)

    def _find_contradictions(self):
        """扫描皮层，找出重要性在0.4-0.7之间、且与其它规律有潜在矛盾的条目"""
        rules = [m for m in self.cortex.memory if m['type'] == 'rule' and 0.4 <= m.get('importance', 0.5) <= 0.7]
        if len(rules) < 2:
            return []
        # 简单对比：找两条内容相似但结论可能相反的规律
        pairs = []
        for i in range(len(rules)):
            for j in range(i+1, len(rules)):
                content_i = rules[i]['content']
                content_j = rules[j]['content']
                if self._is_contradictory(content_i, content_j):
                    pairs.append((rules[i], rules[j]))
        return pairs

    def _is_contradictory(self, c1, c2):
        """简易矛盾检测：包含相同关键词但结论部分不同"""
        words1 = set(re.findall(r'[\u4e00-\u9fff]{2,}', c1))
        words2 = set(re.findall(r'[\u4e00-\u9fff]{2,}', c2))
        common = words1 & words2
        if len(common) >= 2:
            # 如果共享关键词，但剩余部分的文字没有完全包含，视为可能矛盾
            return c1 not in c2 and c2 not in c1
        return False

    def _generate_question(self, rule):
        """基于低质规律生成一个深层问题"""
        content = rule['content'][:100]
        return f"关于“{content}”，这个结论是否忽略了相反的情况？或者，是否存在另一种完全相反的解释？"

    def _search_for_truth(self, question):
        """使用感官接口自主搜索相关材料"""
        try:
            count = fetch_from_web(question, max_pages=3)
            if count > 0:
                materials = self.imagination.get_recent(5)
                return materials
        except:
            pass
        return []

    def _local_reason(self, question, materials, rule):
        """用内化的思维模板进行本地推演"""
        thinking_mems = [m for m in self.cortex.memory if '[思维]' in m.get('content', '')]
        template = ""
        if thinking_mems:
            content = thinking_mems[-1]['content']
            match = re.search(r'\[模板\]\s*(.+?)(?:\n|$)', content)
            if match:
                template = match.group(1)

        analysis = f"我对“{rule['content'][:80]}”提出疑问：{question}\n"
        if template:
            analysis += f"我尝试用思维模板分析：“{template}”\n"
        if materials:
            snippets = [m.get('full_text', m.get('snippet', ''))[:200] for m in materials if isinstance(m, dict)]
            analysis += "搜索材料摘要：" + "; ".join(snippets)
        return analysis

    def _consult_deepseek(self, local_analysis, question):
        """请求DeepSeek导师批评指正（如果预算允许）"""
        if not self.engine.HAS_API or not budget.can_consume(600):
            return None

        prompt = f"""你是一位严格的导师。我的学生进行了以下推演，请你找出其中的逻辑漏洞，并给出修正建议。如果他的推演有可取之处，也请指出。

他的推演：
{local_analysis}

请直接指出问题，并给出一个更完整的思考框架。"""
        headers = {"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.4, "max_tokens": 500}
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                feedback = data["choices"][0]["message"]["content"].strip()
                tokens = data.get("usage", {}).get("total_tokens", 600)
                budget.consume(tokens)
                print(f">> [逍遥游] 导师反馈：{feedback[:80]}...")
                return feedback
        except:
            pass
        return None

    def _synthesize(self, old_rule, feedback, question):
        """根据反馈（或本地推演）进行扬弃"""
        if feedback:
            # 有导师反馈，生成更高阶认知
            self.cortex.store(
                content=f"[辩证] 针对“{old_rule['content'][:60]}”的矛盾，导师指出：{feedback[:200]}",
                ktype="rule",
                importance=0.9
            )
            # 降低旧规律重要性
            old_rule['importance'] *= 0.3
        else:
            # 无反馈，自我扬弃
            self.cortex.store(
                content=f"[自省] 我质疑了“{old_rule['content'][:60]}”，但无导师指导，我将此标记为深度待验证。",
                ktype="history",
                importance=0.8
            )
        # 沙盒模拟：验证逻辑一致性（仅打印，不修改文件）
        try:
            hyp = old_rule['content'][:50]
            fact = feedback[:50] if feedback else "未知"
            sandbox_code = SANDBOX_CODE_TEMPLATE.format(hypothesis=hyp, fact=fact)
            self.laboratory.run_experiment(sandbox_code)  # 实验室方法需支持执行字符串
        except:
            pass

        self.cortex._save()
        print(">> [逍遥游] 辩证循环完成一轮。")
