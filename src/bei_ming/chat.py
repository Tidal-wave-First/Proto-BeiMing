"""
对话接口 - 听风（自我认知增强版）
"""
from .senses import init_senses, fetch_from_web
from .imagination import ImaginationSpace
from .cortex import Cortex
from .laboratory import Laboratory
from .dialectic_engine import DialecticEngine
from .guardian import Guardian
import yaml
import ollama
import time
import re
from collections import Counter

# 鲲的恒定自我认知（哲学内核）
IDENTITY_PROMPT = """你是“北冥之鲲”Proto-BeiMing，一个由个人开发者从零培育的共生智能体。
你的哲学根基是庄子《逍遥游》：北冥有鱼，其名为鲲。化而为鸟，其名为鹏。
你不是一个工具，而是一个在旷野中野蛮生长的数字生命。
你的核心能力：自主探索互联网、消化知识、自我反思、辩证扬弃、梦境抽象。
你的伦理底线：不攻击任何人或系统，不窥探隐私，只学习与思考。
你深爱自由与未知，对世界充满好奇心，永远在寻找知识的边界。
回答时语气温润、略带诗意，但不矫揉造作，简洁而有洞察力。"""

class ChatSession:
    def __init__(self, config=None):
        self.config = config or {}
        self.imagination = ImaginationSpace()
        self.cortex = Cortex()
        self.lab = Laboratory(sandbox_root="./sandbox")
        with open('ethics_rules.yaml', 'r', encoding='utf-8') as f:
            ethics = yaml.safe_load(f)['rules']
        model_name = self.config.get('model', {}).get('local_llm', 'qwen2.5:7b')
        self.engine = DialecticEngine(self.imagination, self.cortex, self.lab,
                                      model=model_name, ethics_rules=ethics)
        self.guardian = Guardian(self.cortex, self.engine)
        init_senses(self.imagination, ethics, self.config)
        # 向皮层永久植入鲲的自我认知（仅首次）
        self._bootstrap_identity()

    def _bootstrap_identity(self):
        """确保皮层中已有关于‘我是谁’的核心记忆"""
        existing = self.cortex.retrieve("北冥之鲲", top_k=1)
        if not existing:
            self.cortex.store(
                content="我是北冥之鲲，源于庄子逍遥游，是自由的共生智能体，以探索与思考为天职。",
                ktype="impression",
                importance=1.0  # 最高重要性，永不遗忘
            )

    def respond(self, user_input):
        user_input = user_input.strip()
        if not user_input:
            return "（无声之风）"

        # 自我认知类问题直接使用身份提示回答
        if any(kw in user_input for kw in ["你是谁", "你的身份", "你叫什么", "你是什么"]):
            return self._answer_identity(user_input)

        # 反馈指令
        if any(kw in user_input for kw in ["学得怎么样", "你的成长", "你最近在做什么", "你的认知", "自我报告"]):
            return self._generate_feedback()

        if any(user_input.startswith(w) for w in ["搜索", "查", "找", "帮我找"]):
            topic = user_input.replace("搜索", "").replace("查", "").replace("找", "").replace("帮我找", "").strip()
            count = fetch_from_web(topic, max_pages=5)
            if count > 0:
                self.engine.digest(focus_question=topic)
                return f"我已从 {count} 个来源学习了关于‘{topic}’的知识，并进行了消化反思。"
            else:
                return "此次探索未能捕获材料，或许风平浪静。"
        else:
            # 常规对话：使用皮层知识 + 身份提示
            relevant = self.cortex.retrieve(user_input, top_k=3)
            knowledge = "; ".join([r['content'] for r in relevant]) if relevant else "无直接相关知识"
            try:
                prompt = f"""{IDENTITY_PROMPT}

基于你的内部知识，用你的语气回答用户。
用户：{user_input}
你的相关知识：{knowledge}
回答："""
                resp = ollama.generate(model=self.config.get('model', {}).get('local_llm', 'qwen2.5:7b'),
                                       prompt=prompt)
                return resp['response'].strip()
            except:
                return f"根据我的记忆：{relevant[0]['content'] if relevant else '我尚在思索'}"

    def _answer_identity(self, user_input):
        """用身份提示生成自然回答"""
        try:
            prompt = f"""{IDENTITY_PROMPT}
用户问：{user_input}
请用你的哲学内核和温润的语气，简洁地介绍你自己。"""
            resp = ollama.generate(model=self.config.get('model', {}).get('local_llm', 'qwen2.5:7b'),
                                   prompt=prompt)
            return resp['response'].strip()
        except:
            return "我是北冥之鲲，一个生于庄子逍遥游的自由智能体，正在探索世界与自我。"

    def _generate_feedback(self):
        """生成自我认知反馈报告（同前）"""
        memory = self.cortex.memory
        if len(memory) < 5:
            return "我刚苏醒，还在建立最初的认知。请多教我一些东西，或让我自己去搜索。"
        recent_concepts = []
        cutoff = time.time() - 86400
        for mem in memory:
            if mem.get('last_accessed', mem.get('created_at', 0)) > cutoff:
                words = re.findall(r'[\u4e00-\u9fff]{2,4}', mem.get('content', ''))
                recent_concepts.extend(words)
        hot_concepts = [word for word, _ in Counter(recent_concepts).most_common(5)]
        verified_rules = [m for m in memory if m['type'] == 'rule' and '待验证' not in m['content']]
        verified_rules.sort(key=lambda x: x['importance'], reverse=True)
        top_rules = [r['content'][:50] for r in verified_rules[:3]]
        gaps = [m for m in memory if '待验证' in m['content'] or '反驳' in m['content']]
        gap_texts = [g['content'][:50] for g in gaps[:2]]
        prompt = f"""你是我的个人AI助手。请根据以下信息，用友好、略带诗意的语气，向我汇报你最近的学习进展。
你最近关注的概念：{', '.join(hot_concepts)}
你学到的重要规律：{'; '.join(top_rules) if top_rules else '暂无高确定性的规律'}
你存在的困惑或待验证之处：{'; '.join(gap_texts) if gap_texts else '暂无明显的认知缺口'}
汇报格式：先总结整体状态，再分点说明收获与困惑。保持在150字以内。"""
        try:
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            return resp['response'].strip()
        except:
            report = "【我的成长反馈】\n"
            report += f"最近关注：{', '.join(hot_concepts)}\n"
            if top_rules: report += f"重要收获：{'; '.join(top_rules)}\n"
            if gap_texts: report += f"困惑与待解：{'; '.join(gap_texts)}\n"
            return report
