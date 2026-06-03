"""
辩证引擎 - 化物（DeepSeek导师版）
"""
import time
import re
import hashlib
import json
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

HAS_API = False
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
if DEEPSEEK_API_KEY:
    HAS_API = True

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
        self.training_lock = __import__('threading').Lock()

    def _call_api(self, prompt):
        if not HAS_API:
            return None
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 400
        }
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions",
                                 headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            return None
        except:
            return None

    def has_fresh_material(self):
        if len(self.imagination) < 1: return False
        recent = self.imagination.get_recent(10)
        h = hashlib.md5(str(recent).encode()).hexdigest()
        if h != self.last_material_hash:
            self.last_material_hash = h
            return True
        return False

    def compute_novelty(self, materials):
        if not materials: return 0
        sample = materials[0].get('title', '') or materials[0].get('full_text', '')[:50]
        existing = self.cortex.retrieve(sample, top_k=3)
        if not existing: return 1.0
        return max(0.1, 1.0 - len(existing) * 0.3)

    def digest(self, focus_question=None):
        if len(self.imagination) < 2: return None
        raw = self.imagination.get_recent(10)
        novelty = self.compute_novelty(raw)
        if novelty < 0.3:
            self._quick_abstract(raw)
            return None
        print(f">> 化物：深度咀嚼 {len(raw)} 条材料 (新颖度 {novelty:.2f})...")
        self.digest_count += 1

        # 用API提取多条规律，同时生成训练样本
        extracted = self._extract_rules_with_api(raw, focus_question)
        if not extracted:
            extracted = self._statistical_extraction(raw)

        conclusions = []
        for rule in extracted:
            # rule 格式: "规律内容|变体1|变体2"
            parts = rule.split('|')
            core_rule = parts[0].strip()
            # 存入皮层
            self.cortex.store(
                content=f"[API导师] {core_rule}",
                ktype="rule",
                importance=0.8
            )
            # 保存训练样本：以核心规律为知识，生成问答对
            if focus_question:
                self._save_training_pair(focus_question, core_rule)
            # 也保存所有变体
            for variant in parts[1:]:
                self._save_training_pair(variant.strip(), core_rule)
            conclusions.append((core_rule, "来自API导师"))

        self.imagination.clear()
        return conclusions

    def _extract_rules_with_api(self, materials, focus=None):
        """用DeepSeek从材料中提取规律，返回格式: 规律1|同义表述1|同义表述2"""
        summaries = []
        for m in materials[:8]:
            if isinstance(m, dict):
                text = m.get('full_text', '') or m.get('snippet', '') or m.get('title', '')
            else:
                text = str(m)
            summaries.append(text[:500])
        joined = "\n---\n".join(summaries)
        prompt = f"""你是认知科学家。请从以下材料中提炼2条最重要的规律。
每条规律用以下格式输出（用竖线分隔同义表述）：
规律句子|同一个规律的不同说法|再一种说法
例如：熵是系统混乱度的度量|熵衡量系统的无序程度|熵越大系统越混乱

材料：
{joined[:3000]}

直接输出规律，每条一行，不要编号。"""
        result = self._call_api(prompt)
        if not result:
            return None
        lines = [line.strip() for line in result.split('\n') if '|' in line]
        return lines[:3]

    def _statistical_extraction(self, materials):
        all_text = ' '.join([m.get('full_text', m.get('snippet', '')) for m in materials if isinstance(m, dict)])
        rules = []
        patterns = re.findall(r'([^，。；\n]{2,20})是([^，。；\n]{2,20})', all_text)
        for a, b in patterns[:5]:
            rules.append(f"{a.strip()}是{b.strip()}")
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', all_text)
        freq = {}
        for w in words: freq[w] = freq.get(w, 0) + 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
        for w, c in top:
            if c >= 2: rules.append(f"{w} (出现{c}次)")
        return rules[:5]

    def _save_training_pair(self, question, answer):
        """保存一个问答对到训练数据文件"""
        with self.training_lock:
            with open(TRAINING_FILE, 'a', encoding='utf-8') as f:
                pair = {"instruction": question, "output": answer}
                f.write(json.dumps(pair, ensure_ascii=False) + '\n')

    def _quick_abstract(self, materials):
        titles = [m.get('title', '') for m in materials[:5] if isinstance(m, dict) and m.get('title')]
        if titles:
            self.cortex.store(
                content=f"[略览] 相关主题: {', '.join(titles[:3])}",
                ktype="impression",
                importance=0.3
            )
