"""
辩证引擎 - 化物（多巴胺驱动版·修复）
"""
import time
import ollama
import re
import hashlib

class DialecticEngine:
    def __init__(self, imagination, cortex, laboratory, model="qwen2.5:7b", ethics_rules=None):
        self.imagination = imagination
        self.cortex = cortex
        self.laboratory = laboratory
        self.model = model
        self.ethics = ethics_rules or []
        self.digest_count = 0
        self.last_material_hash = None

    def has_fresh_material(self):
        if len(self.imagination) < 1:
            return False
        recent = self.imagination.get_recent(10)
        h = hashlib.md5(str(recent).encode()).hexdigest()
        if h != self.last_material_hash:
            self.last_material_hash = h
            return True
        return False

    def compute_novelty(self, materials):
        if not materials:
            return 0
        sample = materials[0].get('title', '') or materials[0].get('full_text', '')[:50]
        existing = self.cortex.retrieve(sample, top_k=3)
        if not existing:
            return 1.0
        return max(0.1, 1.0 - len(existing) * 0.3)

    def digest(self, focus_question=None):
        if len(self.imagination) < 2:
            return None

        raw = self.imagination.get_recent(10)
        novelty = self.compute_novelty(raw)
        print(f">> 多巴胺水平: {novelty:.2f}")
        if novelty < 0.3:
            self._quick_abstract(raw)
            return None

        print(f">> 化物：深度咀嚼 {len(raw)} 条材料 (新颖度 {novelty:.2f})...")
        self.digest_count += 1
        hypotheses = self._generate_hypotheses(raw, focus_question)
        if not hypotheses:
            hypotheses = self._statistical_extraction(raw)

        conclusions = []
        for hyp in hypotheses:
            result = self.laboratory.run_thought_experiment(hyp, raw)
            self._synthesize(hyp, result)
            conclusions.append((hyp, result))

        if conclusions:
            self._self_reflect(conclusions, raw)
        self._induce_principles()
        self.imagination.clear()
        return conclusions

    def _material_summary(self, materials, max_len=2000):
        """安全地将材料列表转为文本摘要"""
        parts = []
        for m in materials[:5]:
            if isinstance(m, dict):
                text = m.get('full_text', '') or m.get('snippet', '') or m.get('title', '')
            else:
                text = str(m)
            parts.append(text[:500])
        return "\n".join(parts)[:max_len]

    def _generate_hypotheses(self, materials, focus=None):
        prompt = self._build_hypothesis_prompt(materials, focus)
        try:
            resp = ollama.generate(model=self.model, prompt=prompt)
            lines = resp['response'].strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip()][:5]
        except Exception as e:
            print(f"LLM假设生成失败，回退统计模式: {e}")
            return []

    def _statistical_extraction(self, materials):
        all_text = ' '.join([m.get('full_text', m.get('snippet', '')) for m in materials if isinstance(m, dict)])
        rules = []
        patterns = re.findall(r'([^，。；\n]{2,20})是([^，。；\n]{2,20})', all_text)
        for a, b in patterns[:5]:
            rules.append(f"{a.strip()}是{b.strip()}")
        words = re.findall(r'[\u4e00-\u9fff]{2,4}', all_text)
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
        for w, c in top:
            if c >= 2:
                rules.append(f"高频概念：{w} (出现{c}次)")
        return rules[:5]

    def _build_hypothesis_prompt(self, materials, focus):
        summary = self._material_summary(materials)
        focus_line = f"请特别关注这个问题：{focus}\n" if focus else ""
        return f"""你是认知科学家。阅读材料，提出3个可验证的规律。
{focus_line}
材料：
{summary}
输出每条一行："""

    def _quick_abstract(self, materials):
        titles = [m.get('title', '') for m in materials[:5] if isinstance(m, dict) and m.get('title')]
        if titles:
            self.cortex.store(
                content=f"[略览] 相关主题: {', '.join(titles[:3])}",
                ktype="impression",
                importance=0.3
            )

    def _synthesize(self, hypothesis, result):
        old = self.cortex.retrieve(hypothesis, top_k=2)
        if old:
            self._dialectical_sublation(hypothesis, result, old)
        else:
            self.cortex.store(
                content=f"[已验证] {hypothesis} (结论: {result})",
                ktype="rule",
                importance=0.6
            )

    def _dialectical_sublation(self, new_hyp, new_res, old_entries):
        old_text = "; ".join([e.get('content', '') for e in old_entries])
        try:
            prompt = f"""你是辩证哲学家。融合新旧知识，给出更高抽象。
旧知: {old_text}
新假设: {new_hyp}
验证结果: {new_res}
请输出一句融合后的规律："""
            resp = ollama.generate(model=self.model, prompt=prompt)
            synth = resp['response'].strip()
            self.cortex.store(content=f"[辩证规律] {synth}", ktype="rule", importance=0.9)
            for old in old_entries:
                old['importance'] *= 0.5
            self.cortex._save()
        except:
            merged = f"{old_text}; {new_hyp} → {new_res}"
            self.cortex.store(content=f"[合并规律] {merged}", ktype="rule", importance=0.7)

    def _self_reflect(self, conclusions, materials):
        if not conclusions:
            return
        material_text = self._material_summary(materials, 1000)
        for hyp, res in conclusions:
            if "不成立" in res or "待验证" in res:
                self.cortex.store(
                    content=f"[待验证] {hyp} (当前结论: {res})",
                    ktype="history",
                    importance=0.5
                )
            try:
                prompt = f"""你是严格的逻辑审查员。针对以下结论，提出1个可能的反驳或例外情况。
结论：{hyp}（验证结果：{res}）
基于材料：{material_text}
请直接列出反驳点："""
                resp = ollama.generate(model=self.model, prompt=prompt)
                critiques = resp['response'].strip()
                if critiques and "无" not in critiques and "没有" not in critiques:
                    self.cortex.store(
                        content=f"[反思] 对 '{hyp[:30]}...' 的反驳: {critiques}",
                        ktype="history",
                        importance=0.7
                    )
                    for mem in self.cortex.memory:
                        if hyp[:20] in mem.get('content', ''):
                            mem['importance'] *= 0.8
                    self.cortex._save()
            except:
                pass

    def _induce_principles(self):
        rules = [m for m in self.cortex.memory if m.get('type') == 'rule']
        if len(rules) < 3:
            return
        recent = sorted(rules, key=lambda x: x.get('last_accessed', 0), reverse=True)[:3]
        contents = "; ".join([r.get('content', '') for r in recent])
        try:
            prompt = f"""将以下规律归纳为一句通用原则：
规律：{contents}
请用一句话表述："""
            resp = ollama.generate(model=self.model, prompt=prompt)
            principle = resp['response'].strip()
            if principle:
                self.cortex.store(content=f"[高层原则] {principle}", ktype="rule", importance=0.95)
                print(f">> 抽象升华：{principle}")
        except:
            combined = " + ".join([r.get('content', '')[:50] for r in recent])
            self.cortex.store(content=f"[归纳] {combined}", ktype="rule", importance=0.6)
