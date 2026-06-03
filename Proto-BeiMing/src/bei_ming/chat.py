from .senses import init_senses, fetch_from_web
from .imagination import ImaginationSpace
from .cortex import Cortex
from .laboratory import Laboratory
from .dialectic_engine import DialecticEngine
from .guardian import Guardian
import yaml
import ollama

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

    def respond(self, user_input):
        user_input = user_input.strip()
        if not user_input:
            return "（无声之风）"
        if any(user_input.startswith(w) for w in ["搜索","查","找","帮我找"]):
            topic = user_input.replace("搜索","").replace("查","").replace("找","").replace("帮我找","").strip()
            count = fetch_from_web(topic, max_pages=5)
            if count > 0:
                self.engine.digest(focus_question=topic)
                return f"我已从 {count} 个来源学习了关于‘{topic}’的知识，并进行了消化反思。"
            else:
                return "此次探索未能捕获材料，或许风平浪静。"
        else:
            relevant = self.cortex.retrieve(user_input, top_k=3)
            if relevant:
                knowledge = "; ".join([r['content'] for r in relevant])
                try:
                    prompt = f"你是Proto-BeiMing。基于内部知识回答用户。\n用户：{user_input}\n相关知识：{knowledge}\n回答："
                    resp = ollama.generate(model=self.config.get('model',{}).get('local_llm','qwen2.5:7b'), prompt=prompt)
                    return resp['response'].strip()
                except:
                    return f"根据我的记忆：{relevant[0]['content']}"
            else:
                count = fetch_from_web(user_input, max_pages=5)
                if count > 0:
                    self.engine.digest(focus_question=user_input)
                    return "我对此进行了即时学习，已存入记忆。你可以再问我一遍试试。"
                else:
                    return "我尚不知此问题，且未能找到材料。愿闻其详？"
