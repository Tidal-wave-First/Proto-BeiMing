"""
阳光模拟实验室 - 支持沙盒内代码执行
"""
import os, sys, io
import subprocess

class Laboratory:
    def __init__(self, sandbox_root="./sandbox"):
        self.root = os.path.abspath(sandbox_root)
        os.makedirs(self.root, exist_ok=True)

    def run_experiment(self, code: str):
        """在沙盒中安全执行一段Python代码，仅允许print输出，禁止文件操作"""
        restricted_builtins = {
            'print': print,
            'range': range,
            'len': len,
            'int': int,
            'str': str,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'abs': abs,
            'all': all,
            'any': any,
            'enumerate': enumerate,
            'zip': zip,
            'sorted': sorted,
            'reversed': reversed,
            'min': min,
            'max': max,
            '__import__': None,  # 禁止导入模块
            'open': None,        # 禁止文件操作
            'exec': None,
            'eval': None,
        }
        try:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            exec(code, {"__builtins__": restricted_builtins}, {})
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            if output:
                print(f">> [沙盒] 实验输出：{output[:200]}")
            return output
        except Exception as e:
            sys.stdout = old_stdout
            print(f">> [沙盒] 实验异常：{e}")
            return str(e)

    def create_temp_file(self, content):
        path = os.path.join(self.root, "temp.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def run_thought_experiment(self, hypothesis, materials):
        # 保留原有逻辑，但不必依赖ollama
        return "待验证：使用逍遥游引擎独立处理"
