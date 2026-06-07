import sys, time
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.bus.message_bus import bus
from matrix.nodes.think_node import ThinkNode
from matrix.nodes.cortex_node import CortexNode
from matrix.nodes.swift_node import SwiftNode

received_scripts = []

def on_cortex_result(payload, sender):
    results = payload.get('results', [])
    if results:
        print(f'>>> 皮层返回 {len(results)} 条记录:')
        for r in results:
            content = r.get('content', '')
            rtype = r.get('type', '')
            print(f'    [{rtype}] {content[:200]}...')
            received_scripts.append(content)

bus.subscribe('cortex.result', on_cortex_result)

think = ThinkNode(bus)
cortex = CortexNode(bus)
swift = SwiftNode(bus)

think.on_start()
cortex.on_start()
swift.on_start()

print('>>> 本地短剧创作矩阵已启动')
print('>>> 发送创作指令: 深夜便利店...')

bus.publish('swift.generate_prompt', {
    'topic': '深夜便利店，一个顾客和一个店员，意外发现彼此的秘密',
    'request_id': 'test_final_03'
}, sender='test')

time.sleep(10)

print('>>> 主动检索皮层中的最终剧本:')
bus.publish('cortex.retrieve', {'tag': 'final'}, sender='test')
time.sleep(3)

if not received_scripts:
    print('>>> 未检索到剧本，请检查 think_node 日志。')
else:
    print('>>> 短剧创作测试成功！')
