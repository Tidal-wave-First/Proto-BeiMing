"""
阳光模拟实验室 - 鲲之行空（修复版）
"""
import os
import ollama

class Laboratory:
    def __init__(self, sandbox_root="./sandbox"):
        self.root = os.path.abspath(sandbox_root)
        os.makedirs(self.root, exist_ok=True)

    def run_experiment(self, code: str):
        """在沙盒内执行代码（占位）"""
        pass

    def create_temp_file(self, content):
        path = os.path.join(self.root, "temp.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def run_thought_experiment(self, hypothesis, materials):
        """
        思维实验：用逻辑一致性、事实一致性检验假设。
        materials 是字典列表，每个字典包含 title, snippet, full_text 等。
        """
        # 安全提取摘要文本
        summaries = []
        for m in materials[:5]:
            if isinstance(m, dict):
                text = m.get('full_text', '') or m.get('snippet', '') or m.get('title', '')
            else:
                text = str(m)
            summaries.append(text[:500])  # 每条摘要最多500字
        joined_summaries = "\n".join(summaries)
        prompt = f"""你是实验室的验证官。给定一个假设和背景材料，判断该假设是否合理。
假设: {hypothesis}
材料摘要:
{joined_summaries[:2000]}

请回答: 如果假设成立，回复“成立”并给出简要理由；如果存疑，回复“待验证”并指出矛盾点；如果错误，回复“不成立”并解释。
回答格式: [判定结果] 理由"""
        try:
            resp = ollama.generate(model="qwen2.5:7b", prompt=prompt)
            return resp['response'].strip()
        except Exception as e:
            return f"待验证：无法调用验证模型 ({e})"
