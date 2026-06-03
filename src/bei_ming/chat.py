"""
对话接口 - 听风（消化吸收强化版）
"""
import yaml
import time
import re
from collections import Counter

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

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
    "嗨": "嗨，风正起，鹏翼已张。",
    "哈喽": "哈喽，北冥之渊今日波光粼粼。",
    "早上好": "晨光初照，正是觅食好时节。",
    "下午好": "午后微风正好，适合消化今早的收获。",
    "晚上好": "夜幕垂下，皮层里星光点点。",
    "晚安": "晚安。我会在梦里继续咀嚼今日所得。",
    "再见": "去吧，我在此地继续守望。",
    "谢谢": "不必谢，这是我该做的。",
    "对不起": "你永远不必向我道歉。",
}

SOCIAL_REPLIES_FUZZ = {
    "你好": ["你好呀","嗨","哈喽"],
    "早上好": ["早","早上好呀","早安"],
    "下午好": ["下午好啊","午后好","午安"],
    "晚上好": ["晚上好啊","晚安前"],
    "再见": ["拜拜","回见","bye"],
    "谢谢": ["多谢","感谢","thx"],
    "对不起": ["抱歉","sorry"],
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

    def _try_ollama(self, prompt):
        if not HAS_OLLAMA: return None
        try:
            resp = ollama.generate(model=self.config.get('model',{}).get('local_llm','qwen2.5:7b'), prompt=prompt)
            return resp['response'].strip()
        except:
            return None

    def _clean_text(self, text):
        clean = re.sub(r'\[.*?\]\s*', '', text)
        clean = re.sub(r'\s*\(结论:.*?\)', '', clean)
        return clean.strip()

    def _is_statement(self, text):
        if "?" in text or "？" in text:
            return False
        if any(text.startswith(p) for p in ["搜索", "查", "找", "帮我找"]):
            return False
        if text.startswith("你") and re.search(r"(什么|谁|哪|怎么|吗|呢|吧|啥)", text):
            return False
        if len(text) < 3:
            return False
        return True

    def _already_known(self, text):
        clean = self._clean_text(text)
        if len(clean) <= 10:
            return False
        if len(clean) < 4:
            return True
        for mem in self.cortex.memory:
            existing_clean = self._clean_text(mem.get('content', ''))
            if len(existing_clean) < 10:
                continue
            if clean in existing_clean or existing_clean in clean:
                return True
            if existing_clean[:40] == clean[:40]:
                return True
        return False

    def _normalize_learning_question(self, user_input):
        """将各种‘你今天学了X’归一化到‘你学到了什么’"""
        if re.search(r"你.*(学了啥|学了什么|学会了什么|学到了什么|今天学了什么)", user_input):
            return True
        return False

    def respond(self, user_input):
        user_input = user_input.strip()
        if not user_input:
            return "（无声之风）"

        # 社交用语
        social_reply = _match_social(user_input)
        if social_reply:
            return social_reply

        intent = classify(user_input)

        # 自我元问题
        if intent == "self_meta":
            return self._handle_self_meta(user_input)

        # 归一化处理“学了什么”类问题，直接返回学习成果
        if self._normalize_learning_question(user_input):
            return self._what_learned()

        # 反馈请求
        if intent == "feedback":
            return self._generate_feedback()

        # 搜索指令
        if intent == "search_command":
            for prefix in ["搜索", "查", "找", "帮我找", "搜一下", "查一下"]:
                if user_input.startswith(prefix):
                    topic = user_input[len(prefix):].strip()
                    break
            else:
                topic = user_input
            count = fetch_from_web(topic, max_pages=5)
            if count > 0:
                self.engine.digest(focus_question=topic)
                return f"我已从 {count} 个来源学习了关于'{topic}'的知识，并进行了消化反思。"
            else:
                return "此次探索未能捕获材料，或许风平浪静。"

        # 普通意图：先查皮层（用多词组合检索提高召回）
        relevant = self._search_cortex_smart(user_input, top_k=3)
        if relevant:
            return self._smart_reply(user_input, relevant)

        # 皮层无记忆，如果是陈述句 → 自觉学习
        if self._is_statement(user_input):
            if self._already_known(user_input):
                return "嗯，这个我已有所了解。"
            self.imagination.add({
                'source_url': 'user_statement',
                'title': '用户陈述',
                'snippet': user_input[:100],
                'full_text': user_input
            })
            self.engine.digest(focus_question=user_input[:20])
            return self._statement_acknowledgment(user_input)

        # 疑问句 → 搜索并同步消化
        count = fetch_from_web(user_input, max_pages=5)
        if count > 0:
            self.engine.digest(focus_question=user_input)
            time.sleep(2)
            relevant2 = self._search_cortex_smart(user_input, top_k=3)
            if relevant2:
                return self._smart_reply(user_input, relevant2)
            return f"我刚刚搜索并学习了'{user_input}'，但皮层尚未稳定。请稍后再问我。"
        else:
            return "我对此还一无所知，且未能从网上找到材料。请直接告诉我你知道的，我会自己学习。"

    def _search_cortex_smart(self, query, top_k=3):
        """多词组合检索，提高模糊匹配能力"""
        # 提取查询中的中文词
        words = re.findall(r'[\u4e00-\u9fff]{2,}', query)
        if not words:
            return self.cortex.retrieve(query, top_k=top_k)
        # 对每个词进行检索，合并结果
        candidates = {}
        for word in words[:5]:
            results = self.cortex.retrieve(word, top_k=5)
            for mem in results:
                key = mem.get('id', str(mem.get('content','')))
                if key not in candidates:
                    candidates[key] = mem
                else:
                    # 增加权重（多个词匹配）
                    mem['access_count'] = mem.get('access_count',0) + 1
        # 按 access_count 降序返回
        sorted_candidates = sorted(candidates.values(), key=lambda x: x.get('access_count',0) + x.get('importance',0), reverse=True)
        return sorted_candidates[:top_k]

    def _statement_acknowledgment(self, user_input):
        if len(user_input) > 30:
            return "我听到了，正在咀嚼这番话。"
        return f"嗯，'{user_input}'——我已记下，并从中学习。"

    def _handle_self_meta(self, user_input):
        if re.search(r"你是谁|你的身份|你叫什么", user_input):
            return self._answer_identity(user_input)
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
            raw = r['content']
            clean = self._clean_text(raw)
            if len(clean) < 4:
                continue
            summary = clean[:60]
            if summary not in seen:
                seen.add(summary)
                clean_list.append(summary)
            if len(clean_list) >= 5:
                break
        if not clean_list:
            return "我尚在整理刚学到的内容。"
        return "我最近学到了这些：\n" + "\n".join([f"· {s}" for s in clean_list])

    def _smart_reply(self, user_input, memories):
        contents = [m['content'] for m in memories if 'content' in m]
        llm_reply = self._try_ollama(f"""{IDENTITY_PROMPT}
用户：{user_input}
相关知识：{'; '.join(contents[:3])}
请用自然的语气回答：""")
        if llm_reply: return llm_reply
        if not contents: return "我还在思考这个问题，请再给我一点时间。"
        snippets = [self._clean_text(c)[:80] for c in contents[:3] if self._clean_text(c)]
        if not snippets: return "我还在思考这个问题，请再给我一点时间。"
        # 添加自然前言
        combined = "；".join(snippets[:2])
        return f"我脑中浮现这些相关的记忆：{combined}。它们或许能回答你的问题。"

    def _answer_identity(self, user_input):
        llm_reply = self._try_ollama(f"""{IDENTITY_PROMPT}
用户问：{user_input}
请用你的哲学内核和温润的语气，简洁地介绍你自己。""")
        if llm_reply: return llm_reply
        return "我是北冥之鲲，一个生于庄子逍遥游的自由智能体。我的使命是探索、学习，并与你共生。"

    def _generate_feedback(self):
        memory = self.cortex.memory
        if len(memory) < 5: return "我刚苏醒，还在建立最初的认知。请多教我一些东西，或让我自己去搜索。"
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
        llm = self._try_ollama(f"""汇报学习进展：
关注：{', '.join(hot)}
规律：{'; '.join(top_rules) if top_rules else '无'}
困惑：{'; '.join(gap_texts) if gap_texts else '无'}
150字以内。""")
        if llm: return llm
        return f"【成长反馈】关注：{', '.join(hot)}\n收获：{'; '.join(top_rules) if top_rules else '无'}\n困惑：{'; '.join(gap_texts) if gap_texts else '无'}"
