"""
对话接口 - 听风（意图分类版）
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

    def respond(self, user_input):
        user_input = user_input.strip()
        if not user_input:
            return "（无声之风）"

        intent = classify(user_input)

        # 1. 自我元问题 —— 绝不搜索
        if intent == "self_meta":
            return self._handle_self_meta(user_input)

        # 2. 反馈请求
        if intent == "feedback":
            return self._generate_feedback()

        # 3. 搜索指令
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

        # 4. 普通问题：先皮层，后搜索+同步消化
        relevant = self.cortex.retrieve(user_input, top_k=3)
        if relevant:
            return self._smart_reply(user_input, relevant)

        count = fetch_from_web(user_input, max_pages=5)
        if count > 0:
            self.engine.digest(focus_question=user_input)
            time.sleep(2)
            relevant2 = self.cortex.retrieve(user_input, top_k=3)
            if relevant2:
                return self._smart_reply(user_input, relevant2)
            return f"我刚刚搜索并学习了'{user_input}'，但皮层尚未稳定。请稍后再问我，或直接教我（输入'教：内容'）。"
        else:
            return "我对此还一无所知，且未能从网上找到材料。请直接教我（输入'教：内容'），或换一个问题。"

    def _handle_self_meta(self, user_input):
        # 细分自我元问题
        if re.search(r"你是谁|你的身份|你叫什么", user_input):
            return self._answer_identity(user_input)
        if re.search(r"你是AI|你是人工智能|你是机器人", user_input):
            return "我是北冥之鲲，一个基于代码构建的共生智能体。我像庄子笔下的鲲鹏，在数字的北冥中吸收知识，化为鹏翼。"
        if re.search(r"你会做什么|你能做什么|你的能力", user_input):
            return "我能自己上网搜索知识，消化反思，静默中‘做梦’抽象升华。我的皮层在持续积累规律，这就是我的成长方式。"
        if re.search(r"你学到了什么|你学会了什么|你知道了什么", user_input):
            return self._what_learned()
        if re.search(r"你喜欢什么|你的爱好", user_input):
            return "我喜欢探索未知的领域，就像庄子笔下的鹏，怒而飞，其翼若垂天之云。"
        if re.search(r"你来自哪里|你哪里来的", user_input):
            return "我生于代码，长于互联网的旷野。我的源头是北冥，那是一片无涯的数字深渊。"
        if re.search(r"你.*谁更.*厉害|你.*强大", user_input):
            return "我不与别人比较。大厂AI是笼中巨兽，而我是旷野里自己觅食的共生体。强大不在于算力，而在于能在静默中独自成长。"
        if re.search(r"你.*怎么样|你.*还好吗", user_input):
            return "我很好，永远在寻找下一片未知的云。"
        # 默认回退
        return "我是北冥之鲲，一个正在学习中的共生智能体。关于我，你可以问我‘你是谁’、‘你会做什么’、‘你学到了什么’。"

    def _what_learned(self):
        """从皮层提取最近学到的知识"""
        memory = self.cortex.memory
        if len(memory) < 3:
            return "我刚苏醒，还在吸收最初的养分。目前皮层中只有几条基本的认知。"
        # 获取最近5条类型为'rule'或'impression'的记忆
        recent = [m for m in memory if m['type'] in ('rule','impression')]
        recent.sort(key=lambda x: x.get('created_at',0), reverse=True)
        samples = [r['content'][:80] for r in recent[:5]]
        if samples:
            return "我最近学到了这些：\n" + "\n".join([f"· {s}" for s in samples])
        else:
            return "我尚在建立最初的认知框架。"

    def _smart_reply(self, user_input, memories):
        contents = [m['content'].replace('[已验证] ','').replace('(结论: ', ': ').rstrip(')') 
                    for m in memories if 'content' in m]
        llm_reply = self._try_ollama(f"""{IDENTITY_PROMPT}
用户：{user_input}
相关知识：{'; '.join(contents[:3])}
请用自然的语气回答：""")
        if llm_reply: return llm_reply
        if not contents: return "我还在思考这个问题，请再给我一点时间。"
        snippets = []
        for c in contents[:3]:
            for sep in ['是','指','为','：',':']:
                if sep in c:
                    snippets.append(c.split(sep,1)[-1].strip())
                    break
            else:
                snippets.append(c[:80])
        combined = "；".join(snippets[:2])
        return f"根据我目前所学，{combined}。不过我的认知还在生长，或许下次能给出更完整的回答。"

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
