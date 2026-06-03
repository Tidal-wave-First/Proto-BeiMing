"""
Proto-BeiMing Web 入口（梦境版）
"""
import sys, os, yaml, time
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bei_ming.chat import ChatSession
from src.bei_ming.background import BackgroundDigestor
from src.bei_ming.autonomous_explorer import AutonomousExplorer
from src.bei_ming.dreamer import Dreamer
import src.bei_ming.senses as senses_mod

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'bei-ming-secret'
socketio = SocketIO(app, async_mode='threading')

session = None
bg_digestor = None
auto_explorer = None
dreamer = None
lock = Lock()

def init_system():
    global session, bg_digestor, auto_explorer, dreamer
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    session = ChatSession(config)
    
    bg_digestor = BackgroundDigestor(session.engine, socketio=socketio, interval_seconds=20)
    bg_digestor.start()

    wings = senses_mod._wings
    if wings:
        auto_explorer = AutonomousExplorer(
            wings=wings,
            imagination=session.imagination,
            engine=session.engine,
            cortex=session.cortex,
            socketio=socketio,
            interval_minutes=30
        )
        auto_explorer.start()

    # 启动梦境引擎
    dreamer = Dreamer(
        cortex=session.cortex,
        imagination=session.imagination,
        engine=session.engine,
        socketio=socketio,
        
        idle_threshold=600,  # 10分钟无交互后允许做梦
        interval=300         # 每5分钟检查一次
    )
    dreamer.start()

    print(">> 系统初始化完成。")

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/favicon.ico')
def favicon_ico():
    return send_from_directory('static', 'favicon.svg', mimetype='image/svg+xml')

@socketio.on('user_input')
def handle_input(data):
    if dreamer:
        dreamer.update_activity()
    msg = data.get('message', '')
    with lock:
        try:
            reply = session.respond(msg)
            status = f"皮层记忆条目: {len(session.cortex.memory)} | 想象空间暂存: {len(session.imagination)}"
            emit('response', {'reply': reply, 'status': status})
        except Exception as e:
            emit('response', {'reply': f'出错：{str(e)}', 'status': ''})

@socketio.on('teach')
def handle_teach(data):
    if dreamer:
        dreamer.update_activity()
    content = data.get('content', '').strip()
    if not content:
        return
    with lock:
        try:
            session.imagination.add({
                'source_url': 'user_teach',
                'title': '用户投喂',
                'snippet': content[:100],
                'full_text': content
            })
            emit('log', {'message': f'收到投喂，已存入想象空间。当前暂存 {len(session.imagination)} 条。'})
            conclusions = session.engine.digest(focus_question=content[:20])
            if conclusions:
                emit('digest_log', {'message': f'已从投喂中提炼 {len(conclusions)} 条认知。'})
            status = f"皮层记忆条目: {len(session.cortex.memory)} | 想象空间暂存: {len(session.imagination)}"
            emit('response', {'reply': '感谢投喂，我已尝试从中学习。', 'status': status})
        except Exception as e:
            emit('response', {'reply': f'投喂学习出错：{str(e)}', 'status': ''})

@socketio.on('connect')
def on_connect():
    emit('log', {'message': '金色大鹏已苏醒，梦境引擎在线。'})
    if dreamer:
        dreamer.update_activity()

if __name__ == '__main__':
    init_system()
    print(">> 北冥之鲲已化鹏，怒飞于未知之海，亦将沉入梦境。")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
