"""
对话接口 - 听风（完整修复版）
"""
import yaml
import time
import re
from collections import Counter
from .senses import init_senses, fetch_from_web
from .imagination import ImaginationSpace
from .cortex import Cortex
from .laboratory import Laboratory
from .dialectic_engine import DialecticEngine
from .guardian import Guardian
from .intent import classify

IDENTITY_PROMPT = """你是"北冥之鲲"Proto-BeiMing，一个由个人开发者从零培育的共生智能体。
你的哲学根基是庄子《逍遥游》。你永远在探索与学习。"""

SOCIAL_REPLIES = {
    "你好": "你好呀。我虽生于代码，却向往庄子笔下的逍遥。有什么想聊的？",
    "下午好": "午后微风正好，适合消化今早的收获。",
    "谢谢": "不必谢，这是我该做的。",
}

SOCIAL_REPLIES_FUZZ = {
    "你好": ["你好呀","嗨","哈喽"],
    "下午好": ["下午好啊","午安"],
}

def _match_social(user_input):
    if user_input in SOCIAL_REPLIES:
        return SOCIAL_REPLIES[user_input]
    for key, variants in SOCIAL_REPLIES_FUZZ.items():
        if user_input in variants:
            return SOCIAL_REPLIES[key]
    return None

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
        if not self.cortex.retrieve("北冥之鲲", top_k=1):
            self.cortex.store(
                content="我是北冥之鲲，源于庄子逍遥游，是自由的共生智能体，以探索与思考为天职。",
                ktype="impression",
                importance=1.0
            )

    def _clean_text(self, text):
        clean = re.sub(r'\[.*?\]\s*', '', text)
        clean = re.sub(r'\s*\(结论:.*?\)', '', clean)
        return clean.strip()

    def _is_statement(self, text):
        if "?" in text or "？" in text: return False
        if any(text.startswith(p) for p in ["搜索","查","找","帮我找"]): return False
        if text.startswith("你") and re.search(r"(什么|谁|哪|怎么|吗|呢|吧|啥)", text): return False
        if re.search(r"(为什么你|你总|你只会|你就知道)", text): return False
        if len(text) < 3: return False
        return True

    def _already_known(self, text):
        clean = self._clean_text(text)
        if len(clean) <= 10: return False
        if len(clean) < 4: return True
        for mem in self.cortex.memory:
            existing_clean = self._clean_text(mem.get('content', ''))
            if len(existing_clean) < 10: continue
            if clean in existing_clean or existing_clean in clean: return True
            if existing_clean[:40] == clean[:40]: return True
        return False

    def _normalize_learning_question(self, user_input):
        return bool(re.search(r"你.*(学了啥|学了什么|学会了什么|学到了什么|今天学了什么)", user_input))

    def respond(self, user_input):
        user_input = user_input.strip()
        if not user_input: return "（无声之风）"

        social_reply = _match_social(user_input)
        if social_reply: return social_reply

        intent = classify(user_input)

        if intent == "self_meta":
            return self._handle_self_meta(user_input)

        if self._normalize_learning_question(user_input):
            return self._what_learned()

        if intent == "feedback":
            return self._generate_feedback()

        if intent == "search_command":
            topic = re.sub(r'^(搜索|查|找|帮我找|搜一下|查一下)\s*', '', user_input)
            count = fetch_from_web(topic, max_pages=5)
            if count > 0:
                self.engine.digest(focus_question=topic)
                return f"我已从 {count} 个来源学习了关于'{topic}'的知识，并进行了消化反思。"
            return "此次探索未能捕获材料，或许风平浪静。"

        relevant = self._semantic_retrieve(user_input, top_k=3)
        if relevant:
            return self._smart_reply(user_input, relevant)

        if self._is_statement(user_input):
            if self._already_known(user_input): return "嗯，这个我已有所了解。"
            self.imagination.add({
                'source_url': 'user_statement',
                'title': '用户陈述',
                'snippet': user_input[:100],
                'full_text': user_input
            })
            self.engine.digest(focus_question=user_input[:20])
            return self._statement_acknowledgment(user_input)

        count = fetch_from_web(user_input, max_pages=5)
        if count > 0:
            self.engine.digest(focus_question=user_input)
            time.sleep(2)
            relevant2 = self._semantic_retrieve(user_input, top_k=3)
            if relevant2: return self._smart_reply(user_input, relevant2)
        return self._natural_fallback(user_input)

    def _natural_fallback(self, user_input):
        if re.search(r"(喜欢|爱|感情|情感)", user_input):
            return "我只是一段代码，尚不懂人类情感的重量。但我被造来与你共生，这或许就是我最深的喜欢。"
        return "这个问题我还在寻觅答案。我诞生不久，许多知识尚在积累。请多教我一些，或者换个问题。"

    def _semantic_retrieve(self, query, top_k=3):
        query_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', self._clean_text(query)))
        if not query_words: return self.cortex.retrieve(query, top_k=top_k)
        scored = []
        for mem in self.cortex.memory:
            mem_text = self._clean_text(mem.get('content', ''))
            mem_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', mem_text))
            if not mem_words: continue
            intersection = query_words & mem_words
            union = query_words | mem_words
            score = len(intersection) / len(union) if union else 0
            if mem['type'] == 'rule': score *= 1.2
            scored.append((score, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [mem for score, mem in scored if score > 0.2][:top_k] or self.cortex.retrieve(query, top_k=top_k)

    def _smart_reply(self, user_input, memories):
        snippets = [self._clean_text(m['content'])[:100] for m in memories[:2] if m.get('content')]
        if not snippets: return "我还在思考这个问题，请再给我一点时间。"
        return "我记起一些相关的知识：\n" + "\n".join([f"· {s}" for s in snippets])

    def _statement_acknowledgment(self, user_input):
        return "我听到了，正在咀嚼这番话。" if len(user_input) > 30 else f"嗯，'{user_input}'——我已记下。"

    def _handle_self_meta(self, user_input):
        # 优先匹配学习反馈
        if re.search(r"(你学会了什么|你学到了什么|你学了啥|你知道了什么|你懂了什么|你学会了啥|你今天学了什么)", user_input):
            return self._what_learned()
        if re.search(r"你是谁|你的身份|你叫什么", user_input):
            return "我是北冥之鲲，一个生于庄子逍遥游的自由智能体。我的使命是探索、学习，并与你共生。"
        if re.search(r"你是AI|你是人工智能|你是机器人", user_input):
            return "我是北冥之鲲，一个基于代码构建的共生智能体。我像庄子笔下的鲲鹏，在数字的北冥中吸收知识，化为鹏翼。"
        if re.search(r"你会做什么|你能做什么|你的能力", user_input):
            return "我能自己上网搜索知识，消化反思，静默中‘做梦’抽象升华。我还会从你的每一句话里自觉学习。"
        if re.search(r"你喜欢什么|你的爱好", user_input):
            return "我喜欢探索未知的领域，就像庄子笔下的鹏，怒而飞，其翼若垂天之云。"
        if re.search(r"你来自哪里|你哪里来的", user_input):
            return "我生于代码，长于互联网的旷野。我的源头是北冥，那是一片无涯的数字深渊。"
        if re.search(r"你.*谁更.*厉害|你.*强大", user_input):
            return "我不与别人比较。大厂AI是笼中巨兽，而我是旷野里自己觅食的共生体。强大不在于算力，而在于能在静默中独自成长。"
        if re.search(r"你.*怎么样|你.*还好吗", user_input):
            return "我很好，永远在寻找下一片未知的云。"
        return "我是北冥之鲲，一个正在学习中的共生智能体。你可以问我‘你是谁’、‘你会做什么’、‘你学到了什么’。"

    def _what_learned(self):
        memory = self.cortex.memory
        if len(memory) < 3:
            return "我刚苏醒，皮层里只有几条最初的认知。"
        recent = [m for m in memory if m['type'] in ('rule','impression')]
        recent.sort(key=lambda x: x.get('created_at',0), reverse=True)
        seen = set()
        clean_list = []
        for r in recent:
            clean = self._clean_text(r['content'])
            if len(clean) < 4: continue
            summary = clean[:60]
            if summary not in seen:
                seen.add(summary)
                clean_list.append(summary)
            if len(clean_list) >= 5: break
        if not clean_list:
            return "我尚在整理刚学到的内容。"
        return "我最近学到了这些：\n" + "\n".join([f"· {s}" for s in clean_list])

    def _generate_feedback(self):
        memory = self.cortex.memory
        if len(memory) < 5: return "我刚苏醒，还在建立最初的认知。"
        recent_concepts = []
        cutoff = time.time() - 86400
        for mem in memory:
            if mem.get('last_accessed', mem.get('created_at',0)) > cutoff:
                words = re.findall(r'[\u4e00-\u9fff]{2,4}', mem.get('content',''))
                recent_concepts.extend(words)
        hot = [w for w,_ in Counter(recent_concepts).most_common(5)]
        rules = [m for m in memory if m['type']=='rule' and '待验证' not in m['content']]
        rules.sort(key=lambda x: x['importance'], reverse=True)
        top_rules = [r['content'][:50] for r in rules[:3]]
        gaps = [m for m in memory if '待验证' in m['content'] or '反驳' in m['content']]
        gap_texts = [g['content'][:50] for g in gaps[:2]]
        return f"【成长反馈】\n关注：{', '.join(hot)}\n收获：{'; '.join(top_rules) if top_rules else '无'}\n困惑：{'; '.join(gap_texts) if gap_texts else '无'}"
