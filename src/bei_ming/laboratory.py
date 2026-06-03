"""
阳光模拟实验室 - 无 LLM 回退版
"""
import os

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

class Laboratory:
    def __init__(self, sandbox_root="./sandbox"):
        self.root = os.path.abspath(sandbox_root)
        os.makedirs(self.root, exist_ok=True)

    def run_experiment(self, code: str):
        pass

    def create_temp_file(self, content):
        path = os.path.join(self.root, "temp.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def run_thought_experiment(self, hypothesis, materials):
        if not HAS_OLLAMA:
            return "待验证：云端无本地大模型，采用统计学习"
        summaries = []
        for m in materials[:5]:
            if isinstance(m, dict):
                text = m.get('full_text', '') or m.get('snippet', '') or m.get('title', '')
            else:
                text = str(m)
            summaries.append(text[:500])
        joined = "\n".join(summaries)
        prompt = f"""你是验证官。判断假设是否合理。
假设: {hypothesis}
材料摘要:
{joined[:2000]}

请回答: 如果假设成立，回复"成立"并给出理由；否则回复"待验证"并指出矛盾点；如果错误，回复"不成立"并解释。
格式: [判定结果] 理由"""
        try:
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            return resp['response'].strip()
        except Exception:
            return "待验证：无法调用验证模型"
