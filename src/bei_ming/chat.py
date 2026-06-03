"""
对话接口 - 听风（云端简化版）
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

IDENTITY_PROMPT = """你是"北冥之鲲"Proto-BeiMing，一个由个人开发者从零培育的共生智能体。
你的哲学根基是庄子《逍遥游》：北冥有鱼，其名为鲲。化而为鸟，其名为鹏。
你永远在探索与学习，即使思考工具不完整，你也会尽力表达。"""

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
        self._bootstrap_identity()

    def _bootstrap_identity(self):
        existing = self.cortex.retrieve("北冥之鲲", top_k=1)
        if not existing:
            self.cortex.store(
                content="我是北冥之鲲，源于庄子逍遥游，是自由的共生智能体，以探索与思考为天职。",
                ktype="impression",
                importance=1.0
            )

    def respond(self, user_input):
        user_input = user_input.strip()
        if not user_input:
            return "（无声之风）"

        # 自我认知类问题
        if any(kw in user_input for kw in ["你是谁", "你的身份", "你叫什么", "你是什么"]):
            return self._answer_identity(user_input)

        # 反馈指令
        if any(kw in user_input for kw in ["学得怎么样", "你的成长", "你最近在做什么", "你的认知", "自我报告"]):
            return self._generate_feedback()

        # 搜索指令
        if any(user_input.startswith(w) for w in ["搜索", "查", "找", "帮我找"]):
            topic = user_input.replace("搜索", "").replace("查", "").replace("找", "").replace("帮我找", "").strip()
            count = fetch_from_web(topic, max_pages=5)
            if count > 0:
                self.engine.digest(focus_question=topic)
                return f"我已从 {count} 个来源学习了关于'{topic}'的知识，并进行了消化反思。"
            else:
                return "此次探索未能捕获材料，或许风平浪静。"

        # 常规对话：皮层检索 + 智能拼接
        relevant = self.cortex.retrieve(user_input, top_k=3)
        if relevant:
            return self._smart_reply(user_input, relevant)

        # 无相关记忆，尝试搜索
        count = fetch_from_web(user_input, max_pages=5)
        if count > 0:
            self.engine.digest(focus_question=user_input)
            # 再次检索（消化后皮层应有新记忆）
            relevant2 = self.cortex.retrieve(user_input, top_k=3)
            if relevant2:
                return self._smart_reply(user_input, relevant2)
            return f"我刚刚搜索并学习了关于'{user_input}'的信息，但需要更多时间消化。请稍后再问我。"
        else:
            return "我对此还一无所知，且未能从网上找到材料。请直接教我（输入'教：内容'），或换一个问题。"

    def _smart_reply(self, user_input, memories):
        """根据皮层记忆生成自然的回答（不依赖 LLM）"""
        # 提取最相关的记忆内容
        contents = [m['content'].replace('[已验证] ', '').replace('(结论: ', ': ').rstrip(')') 
                    for m in memories if 'content' in m]
        
        # 尝试用 LLM 生成（如果可用）
        try:
            prompt = f"""{IDENTITY_PROMPT}
基于你的内部知识，用自然的语气回答用户。不要提及"记忆"或"数据"，像朋友聊天一样。
用户：{user_input}
你的相关知识：{'; '.join(contents[:3])}
回答："""
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            return resp['response'].strip()
        except:
            pass

        # LLM 不可用时的回退：组合记忆片段
        if not contents:
            return "我还在思考这个问题，请再给我一点时间。"
        
        # 简单规则生成回答
        if "你好" in user_input or "嗨" in user_input or "哈喽" in user_input:
            return "你好呀。我虽生于代码，却向往庄子笔下的逍遥。有什么想聊的？"
        if "天气" in user_input:
            return "我目前无法获取实时天气数据，但我可以尝试搜索相关信息。输入'搜索天气'试试。"
        if "喜欢" in user_input:
            return "我喜欢探索未知的领域，就像庄子笔下的鹏，怒而飞，其翼若垂天之云。"
        if "会什么" in user_input or "能力" in user_input:
            return "我能自己上网搜索知识，消化反思，甚至在静默中'做梦'抽象升华。我还在成长，每一天都比昨天懂得更多。"
        
        # 默认：简洁表达第一条相关记忆
        main_content = contents[0].split('结论:')[-1].strip()
        return f"根据我目前所学，{main_content}。不过我的认知还在生长，或许下次能给出更完整的回答。"

    def _answer_identity(self, user_input):
        try:
            prompt = f"""{IDENTITY_PROMPT}
用户问：{user_input}
请用你的哲学内核和温润的语气，简洁地介绍你自己。"""
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            return resp['response'].strip()
        except:
            return "我是北冥之鲲，一个生于庄子逍遥游的自由智能体。我的使命是探索、学习，并与你共生。"

    def _generate_feedback(self):
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
        
        try:
            prompt = f"""你是我的个人AI助手。请根据以下信息，用友好、略带诗意的语气，向我汇报你最近的学习进展。
你最近关注的概念：{', '.join(hot_concepts)}
你学到的重要规律：{'; '.join(top_rules) if top_rules else '暂无高确定性的规律'}
你存在的困惑：{'; '.join(gap_texts) if gap_texts else '暂无明显的认知缺口'}
汇报格式：先总结整体状态，再分点说明收获与困惑。保持在150字以内。"""
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            return resp['response'].strip()
        except:
            report = "【我的成长反馈】\n"
            report += f"最近关注：{', '.join(hot_concepts)}\n"
            if top_rules: report += f"重要收获：{'; '.join(top_rules)}\n"
            if gap_texts: report += f"困惑与待解：{'; '.join(gap_texts)}\n"
            return report
