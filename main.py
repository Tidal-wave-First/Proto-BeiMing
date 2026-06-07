"""Proto-BeiMing Web 入口 —— 融合矩阵生态与 Flask 界面"""
import sys, os, yaml, time, json, threading
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit

# 矩阵核心
from matrix.bus.message_bus import bus
from matrix.nodes.think_node import ThinkNode
from matrix.nodes.cortex_node import CortexNode
from matrix.nodes.swift_node import SwiftNode

HEADLESS = "--headless" in sys.argv

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'bei-ming-secret'
socketio = SocketIO(app, async_mode='threading')

# 全局节点引用
think_node = None
cortex_node = None
swift_node = None
lock = Lock()

def start_matrix_nodes():
    global think_node, cortex_node, swift_node
    print("[Flask] 正在启动矩阵节点...")
    think_node = ThinkNode(bus)
    cortex_node = CortexNode(bus)
    swift_node = SwiftNode(bus)
    think_node.on_start()
    cortex_node.on_start()
    swift_node.on_start()
    print("[Flask] 矩阵节点已全部启动。")

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/favicon.ico')
def favicon_ico():
    return send_from_directory('static', 'favicon.svg', mimetype='image/svg+xml')

@app.route('/health')
def health():
    return jsonify({"status": "alive", "nodes": ["think", "cortex", "swift"]})

@socketio.on('user_input')
def handle_input(data):
    msg = data.get('message', '')
    with lock:
        try:
            # 通过矩阵总线生成短剧
            request_id = f"web_{int(time.time())}"
            # 订阅 cortex 结果，通过 SocketIO 推送给前端
            def on_script_ready(payload, sender):
                script = payload.get('script', '')
                emit('response', {'reply': script})
            bus.subscribe('swift.script_ready', on_script_ready)
            # 发送创作指令
            bus.publish('swift.generate_prompt', {
                'topic': msg,
                'request_id': request_id
            }, sender='web_ui')
        except Exception as e:
            emit('response', {'reply': f'出错：{str(e)}'})

@socketio.on('connect')
def on_connect():
    emit('log', {'message': '连接成功，短剧工作台已就绪。'})

if __name__ == '__main__':
    # 启动矩阵节点（后台线程）
    start_matrix_nodes()
    print(">> 鲲鹏短剧工作台已启动，访问 http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
