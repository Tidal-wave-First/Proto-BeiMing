import os
import ollama

class Laboratory:
    def __init__(self, sandbox_root="./sandbox"):
        self.root = os.path.abspath(sandbox_root)
        os.makedirs(self.root, exist_ok=True)

    def run_thought_experiment(self, hypothesis, materials):
        summaries = []
        for m in materials[:5]:
            if isinstance(m, dict):
                text = m.get('full_text', '') or m.get('snippet', '') or m.get('title', '')
            else:
                text = str(m)
            summaries.append(text[:500])
        joined = "\n".join(summaries)
        prompt = f"""你是实验室的验证官。给定一个假设和背景材料，判断该假设是否合理。
假设: {hypothesis}
材料摘要:
{joined[:2000]}
请回答: 如果假设成立，回复“成立”并给出简要理由；如果存疑，回复“待验证”并指出矛盾点；如果错误，回复“不成立”并解释。
回答格式: [判定结果] 理由"""
        try:
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            return resp['response'].strip()
        except:
            return "待验证：无法调用验证模型"
