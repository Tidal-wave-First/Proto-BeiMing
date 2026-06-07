import sys, os
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
os.chdir('D:/Proto-BeiMing-北冥')

print(f'当前工作目录: {os.getcwd()}')
env_path = '.env'
print(f'正在检查文件: {os.path.abspath(env_path)}')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        print('文件内容:')
        for line in f:
            print(f'  {line.rstrip()}')
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
                if 'KEY' in key:
                    print(f'[诊断] 已设置环境变量: {key.strip()} = {value.strip()[:12]}...')
else:
    print(f'错误: 文件不存在 - {os.path.abspath(env_path)}')

key = os.environ.get('DEEPSEEK_API_KEY', '未找到')
print(f'[结果] DEEPSEEK_API_KEY = {key[:15]}... (长度: {len(key)})')
