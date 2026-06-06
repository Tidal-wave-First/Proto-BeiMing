"""本地 LLM 推理模块 —— 使用 llama-cpp-python（纯 CPU）"""
import os
from llama_cpp import Llama
from thinking_core.ethics_council import get_ethics_council

class LocalLLM:
    def __init__(self, model_path: str = "D:/SwiftAssistant/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"):
        self.ethics = get_ethics_council()
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件未找到: {model_path}。请先下载模型。")
        # 强制 CPU，不加载任何 GPU 层
        self.llm = Llama(model_path=model_path, n_ctx=512, n_gpu_layers=0, verbose=False)

    def chat(self, prompt: str, system_prompt: str = "") -> str:
        if self.ethics.judge(prompt).status.value != "approved":
            return "我不能回答这个问题。"

        full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n"
        try:
            output = self.llm(full_prompt, max_tokens=150, stop=["<|user|>", "<|system|>"], echo=False)
            reply = output["choices"][0]["text"].strip()
            if self.ethics.judge(reply).status.value != "approved":
                return "我产生了一些不合适的内容，已将其过滤。"
            return reply if reply else "我还在思考，你能换个方式问我吗？"
        except Exception as e:
            return f"本地模型暂时不可用: {e}"
