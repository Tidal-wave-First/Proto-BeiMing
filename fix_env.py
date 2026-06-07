with open('D:/Proto-BeiMing-北冥/.env', 'w', encoding='utf-8', newline='') as f:
    f.write('DEEPSEEK_API_KEY=sk-92ee6710c3cf496bb7c35a7dc6ccaa62\n')
    f.write('DEEPSEEK_MODEL=deepseek-chat\n')
print('.env 已用纯 ASCII 重写，BOM 已清除。')

with open('D:/Proto-BeiMing-北冥/.env', 'r', encoding='utf-8') as f:
    first_line = f.readline()
    print(f'新第一行: {repr(first_line)}')
    found = 'DEEPSEEK_API_KEY' in first_line
    print(f'匹配检查: {found}')
