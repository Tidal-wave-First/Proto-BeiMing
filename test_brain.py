import sys
sys.path.insert(0, 'D:/SwiftAssistant')
from thinking_core.local_llm import LocalLLM

model_path = 'D:/SwiftAssistant/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf'
print(f'>>> 点火程序启动，目标模型: {model_path}')

try:
    print('>>> 正在加载模型到内存...')
    llm = LocalLLM(model_path=model_path)
    print('>>> 模型加载成功！微型大脑已激活。')
    
    print('>>> 正在进行思维范式测试...')
    prompt = '用一句话解释什么是"试错学习"'
    print(f'>>> 输入: {prompt}')
    response = llm.think(prompt)
    print(f'>>> 输出: {response}')
    print('>>> 微型大脑功能验证通过。')
    
except Exception as e:
    print(f'>>> 点火失败，错误信息: {e}')
    print('>>> 可能的原因: 模型文件路径错误，或缺少 llama-cpp-python 等依赖库。')
