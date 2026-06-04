"""
辩证引擎 - 思维学徒版（三七开预算）
"""
import time, re, hashlib, json, os, requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass
from .dashboard import record_digest
from .token_budget import budget

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
HAS_API = bool(API_KEY)
TRAINING_FILE = "training_data.jsonl"

class DialecticEngine:
    def __init__(self, imagination, cortex, laboratory, model="qwen2.5:7b", ethics_rules=None):
        self.imagination = imagination
        self.cortex = cortex
        self.laboratory = laboratory
        self.model = model
        self.ethics = ethics_rules or []
        self.digest_count = 0
        self.last_material_hash = None

    def _call_api(self, prompt, max_tokens=150):
        """调用 DeepSeek，max_tokens 可调节"""
        if not HAS_API:
            return None, 0
        estimated_input = len(prompt) // 4
        estimated_total = estimated_input + max_tokens
        if not budget.can_consume(estimated_total):
            print(f">> [预算] 余额不足，跳过API。剩余 {budget.get_remaining()} tokens")
            return None, 0

        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": max_tokens
        }
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions",
                                 headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                result = data["choices"][0]["message"]["content"].strip()
                tokens = data.get("usage", {}).get("total_tokens", estimated_total)
                print(f">> [API] 消耗 {tokens} tokens，剩余 {budget.get_remaining()}")
                budget.consume(tokens)
                return result, tokens
            else:
                print(f">> [API] 错误 {resp.status_code}")
                return None, 0
        except Exception as e:
            print(f">> [API] 异常 {e}")
            return None, 0

    def digest(self, focus_question=None):
        if len(self.imagination) < 2:
            return None
        raw = self.imagination.get_recent(10)
        texts = []
        for m in raw:
            if isinstance(m, dict):
                text = m.get('full_text', '') or m.get('snippet', '') or m.get('title', '')
            else:
                text = str(m)
            if text:
                texts.append(text[:500])
        combined = "\n---\n".join(texts)

        # 第一阶段：快速提取知识（三成预算，max_tokens=150）
        prompt = f"""你是知识提炼专家。从材料中提取最核心的认知，按格式返回：
[定义] <一句话定义>
[规律1] <核心规律>
[规律2] <另一条规律，若无则省略>
[可验证] <一个可被事实检验的判断>

材料：
{combined[:3000]}"""
        result, tokens = self._call_api(prompt, max_tokens=150)
        if not result:
            print(">> API精炼失败，回退统计提取")
            rules = self._statistical_extraction(raw)
            for r in rules[:5]:
                self.cortex.store(content=f"[统计] {r}", ktype="rule", importance=0.5)
            self.imagination.clear()
            return rules

        # 解析知识
        knowledge = {"定义": [], "规律": [], "可验证": []}
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith("[定义]"): knowledge["定义"].append(line[4:].strip())
            elif line.startswith("[规律1]") or line.startswith("[规律2]"): knowledge["规律"].append(line[5:].strip())
            elif line.startswith("[可验证]"): knowledge["可验证"].append(line[5:].strip())

        # 存储知识
        for key, items in knowledge.items():
            for item in items:
                content = f"[{key}] {item}"
                self.cortex.store(content=content, ktype="rule", importance=0.8)
                if focus_question:
                    self._save_training_pair(focus_question, item)
                if key == "定义":
                    self._save_training_pair(f"什么是{item[:20]}", item)

        record_digest(focus_question or "无主题", tokens)

        # 第二阶段：思维学习（七成预算，max_tokens=600）
        if budget.can_consume(800):
            thinking_prompt = f"""你刚才从材料中提炼了以下知识：
{json.dumps(knowledge, ensure_ascii=False, indent=2)}

现在，请以一位导师的身份，详细展示你是如何从原始材料中得出这些结论的。请包括：
1. 你发现的关键线索
2. 你的推理步骤
3. 一个通用的思考模板（例如：遇到类似问题时，应先分析X，再归纳Y）
4. 提出一个可以挑战这些知识的问题

格式：
[线索] ...
[推理] ...
[模板] ...
[挑战] ..."""
            thinking_result, t_tokens = self._call_api(thinking_prompt, max_tokens=600)
            if thinking_result:
                self.cortex.store(
                    content=f"[思维] {thinking_result[:500]}",
                    ktype="rule",
                    importance=0.95
                )
                print(">> 思维学徒：已内化思考过程")
        else:
            print(">> 预算不足，跳过思维训练")

        self.imagination.clear()
        return [(item, f"API-{key}") for key, items in knowledge.items() for item in items]

    def _save_training_pair(self, question, answer):
        try:
            with open(TRAINING_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"instruction": question, "output": answer}, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"写入训练数据失败: {e}")

    def _statistical_extraction(self, materials):
        all_text = ' '.join([m.get('full_text', m.get('snippet', '')) for m in materials if isinstance(m, dict)])
        rules = []
        patterns = re.findall(r'([^，。；\n]{2,20})是([^，。；\n]{2,20})', all_text)
        for a,b in patterns[:5]:
            rules.append(f"{a.strip()}是{b.strip()}")
        return rules

    def compute_novelty(self, materials):
        if not materials: return 0
        sample = materials[0].get('title','') or materials[0].get('full_text','')[:50]
        existing = self.cortex.retrieve(sample, top_k=3)
        return 1.0 if not existing else max(0.1, 1.0 - len(existing)*0.3)

    def has_fresh_material(self):
        if len(self.imagination) < 1: return False
        recent = self.imagination.get_recent(10)
        h = hashlib.md5(str(recent).encode()).hexdigest()
        if h != self.last_material_hash:
            self.last_material_hash = h
            return True
        return False

    def _quick_abstract(self, materials):
        titles = [m.get('title','') for m in materials[:5] if isinstance(m,dict) and m.get('title')]
        if titles:
            self.cortex.store(content=f"[略览] {', '.join(titles[:3])}", ktype="impression", importance=0.3)
