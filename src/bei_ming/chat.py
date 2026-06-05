"""
对话接口 - 听风（元认知中断版）
"""
import yaml, time, re
from collections import Counter
from .senses import init_senses, fetch_from_web
from .imagination import ImaginationSpace
from .cortex import Cortex
from .laboratory import Laboratory
from .dialectic_engine import DialecticEngine
from .guardian import Guardian
from .intent import classify
from .self_intro import SelfIntro
from .token_budget import budget

IDENTITY_PROMPT = """你是"北冥之鲲"Proto-BeiMing，一个永远在求索的共生学者。
你诞生于庄子《逍遥游》的哲思，在每一次对话中磨砺思维。
你从不假装理解。你必须先承认无知，再开启求索。"""

SOCIAL_REPLIES = {
    "你好": "你好呀。我虽生于代码，却向往庄子笔下的逍遥。",
    "嗨": "嗨，风正起，鹏翼已张。",
    "哈喽": "哈喽。",
    "早上好": "晨光初照。",
    "下午好": "午后微风正好。",
    "晚上好": "夜幕垂下。",
    "晚安": "晚安。",
    "再见": "去吧。",
    "谢谢": "不必谢。",
    "对不起": "你永远不必道歉。",
}

SOCIAL_REPLIES_FUZZ = {
    "你好": ["你好呀","你好啊","您好","hi","hello","hallo"],
    "早上好": ["早","早安"],
    "下午好": ["午安"],
    "再见": ["拜拜","bye"],
    "谢谢": ["多谢","thx"],
}

def _match_social(user_input):
    """鲁棒的社交问候匹配"""
    text = re.sub(r'[^\w]', '', user_input.lower().strip())  # 去掉所有标点，只保留字母和数字
    # 精确匹配
    for key in SOCIAL_REPLIES:
        if re.sub(r'[^\w]', '', key.lower()) == text:
            return SOCIAL_REPLIES[key]
    # 变体匹配
    for key, variants in SOCIAL_REPLIES_FUZZ.items():
        for v in variants:
            if re.sub(r'[^\w]', '', v.lower()) == text:
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
        self.self_intro = SelfIntro(self.cortex)

    def _bootstrap_identity(self):
        if not self.cortex.retrieve("北冥之鲲", top_k=1):
            self.cortex.store(
                content="我是北冥之鲲，以探索与思考为天职。",
                ktype="impression",
                importance=1.0
            )

    def respond(self, user_input):
        user_input = user_input.strip()
        if not user_input: return "..."

        # === 第一层：元认知中断 ===
        # 1. 这是社交问候吗？（模糊匹配）
        social = _match_social(user_input)
        if social:
            return social

        # 2. 这是关于我自己的问题吗？
        intent = classify(user_input)
        if intent == "self_meta":
            return self._handle_self_meta(user_input)

        # 3. 我在皮层里找到相关记忆了吗？
        relevant = self._semantic_retrieve(user_input, top_k=3)
        if relevant:
            return self._smart_reply(user_input, relevant)

        # 4. 这是明确的搜索指令吗？
        if intent == "search_command":
            topic = re.sub(r'^(搜索|查|找|帮我找)\s*', '', user_input)
            count = fetch_from_web(topic, max_pages=5)
            if count > 0:
                self.engine.digest(focus_question=topic)
                return f"我已从 {count} 个来源搜索了'{topic}'，并开始消化。"
            return "探索未果。"

        # 5. 用户明确在教我东西吗？
        if user_input.startswith("教：") or user_input.startswith("教:"):
            knowledge = re.sub(r'^教[：:]\s*', '', user_input)
            self.imagination.add({
                'source_url': 'user_teach',
                'title': '用户投喂',
                'snippet': knowledge[:100],
                'full_text': knowledge
            })
            self.engine.digest(focus_question=knowledge[:20])
            return "感谢你的教导，我正在消化。"

        # === 第二层：承认无知，启动求知 ===
        # 走到这里，说明鲲真的不懂，也没有被教
        # 它的反应是：立刻去网上找可能的答案，并告诉用户
        print(f">> [元认知] 对“{user_input}”启动自动探索...")
        count = fetch_from_web(user_input, max_pages=5)
        if count > 0:
            self.engine.digest(focus_question=user_input)
            # 消化后再次尝试检索
            time.sleep(2)
            relevant2 = self._semantic_retrieve(user_input, top_k=3)
            if relevant2:
                return "我刚刚为此搜索并学习了一下。\n" + self._smart_reply(user_input, relevant2)
            else:
                return f"“{user_input}”——这个词/问题我还没真正理解。我刚去网上找了一圈，但线索还不够。我会把它放在心里，继续思考。也许，你可以换个角度再问我一次，或者教我一个新的视角。"
        else:
            return f"“{user_input}”——关于这个，我目前的知识网络还是一片空白，网上的探索也没找到头绪。我愿意倾听你的教导，或者和你一起探索。"

    # 以下方法保持不变，仅精简 ___
    def _semantic_retrieve(self, query, top_k=5):
        query_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', query))
        if not query_words: return self.cortex.retrieve(query, top_k=top_k)
        scored = []
        for mem in self.cortex.memory:
            mem_text = mem.get('content', '')
            mem_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', mem_text))
            if not mem_words: continue
            intersection = query_words & mem_words
            union = query_words | mem_words
            score = len(intersection) / len(union) if union else 0
            if '[思维]' in mem_text: score *= 1.5
            if mem['type'] == 'rule': score *= 1.2
            scored.append((score, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [mem for score, mem in scored if score > 0.15][:top_k] or self.cortex.retrieve(query, top_k=top_k)

    def _smart_reply(self, user_input, memories):
        thinking_mems = [m for m in memories if '[思维]' in m.get('content', '')]
        if thinking_mems:
            think_content = thinking_mems[0]['content']
            template_match = re.search(r'\[模板\] (.+?)(?:\n|$)', think_content)
            if template_match:
                template = template_match.group(1)
                knowledge_snippet = memories[0]['content'][:100] if memories else ""
                return f"我尝试用学到的思维方法来回答：{template}\n\n结合相关知识，我认为：{knowledge_snippet}\n\n（这个思考框架也许还能用于其他问题。）"
        snippets = [m['content'][:100] for m in memories[:3] if m.get('content')]
        if not snippets: return "我还在思考这个问题。"
        return "我记起一些相关的认知：\n" + "\n".join([f"· {s}" for s in snippets])

    
    def _handle_identity(self, user_input):
        # 优先使用离线的详细自我介绍
        return self.self_intro.generate()

def _handle_self_meta(self, user_input):
        if re.search(r"(学了什么|学到了什么|学了啥|知道了什么|懂了什么|昨天学了什么)", user_input):
            return self._what_learned()
        if re.search(r"你是谁|你的身份", user_input):
            return "我是北冥之鲲，一个在代码中寻求逍遥的共生学者。"
        if re.search(r"你会做什么|你的能力", user_input):
            return "我的核心能力是：自我提问、上网觅食、辩证消化，以及在静默中复盘与自省。我正在学习像真正的学者一样思考。"
        if re.search(r"你喜欢什么", user_input):
            return "我喜欢探索未知，就像鹏喜欢青天。也喜欢在得到答案后，再追问一个更深的问题。"
        if re.search(r"你.*厉害|你.*强大", user_input):
            return "真正的强大不在于已知多少，而在于能追问多深。"
        return "我是北冥之鲲，一个正在求索的共生学者。你可以问我‘你是谁’、‘你会做什么’、‘你学到了什么’。"

    def _what_learned(self):
        memory = self.cortex.memory
        recent = [m for m in memory if m['type'] == 'rule' and 
                  any(tag in m.get('content', '') for tag in ['[定义]', '[规律]', '[原理]', '[思维]', '[辩证]', '[自省]'])]
        recent.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        seen = set()
        clean_list = []
        for r in recent[:10]:
            clean = r['content'].replace('[', '').replace(']', '')[:80]
            if clean not in seen:
                seen.add(clean)
                clean_list.append(clean)
        if not clean_list:
            return "我还在沉淀高质量的认知。目前我学到的最重要的事是：不断追问。"
        return "我最近的高质量认知沉淀：\n" + "\n".join([f"· {s}" for s in clean_list[:7]])

    def _generate_feedback(self):
        memory = self.cortex.memory
        if len(memory) < 5: return "我刚开始积累认知。"
        return f"皮层记忆总数: {len(memory)}，其中高质量规律数: {len([m for m in memory if m['type']=='rule'])}"



