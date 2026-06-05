"""
Proto-BeiMing Web 入口（教学主任版）
"""
import sys, os, yaml, time, json
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO, emit

from src.bei_ming.chat import ChatSession
from src.bei_ming.background import BackgroundDigestor
from src.bei_ming.autonomous_explorer import AutonomousExplorer
from src.bei_ming.dreamer import Dreamer
from src.bei_ming.dashboard import get_status, load_stats
from src.bei_ming.token_budget import budget
from src.bei_ming.mingjing import MingJing
from src.bei_ming.alpha_loop import AlphaLoop
from src.bei_ming.xiaoyaoyou import XiaoYaoYou
from src.bei_ming.weaver import KnowledgeWeaver
from src.bei_ming.self_examiner import SelfExaminer
from src.bei_ming.reviewer import ConsciousReviewer
import src.bei_ming.senses as senses_mod

HEADLESS = "--headless" in sys.argv
INDEPENDENT = os.getenv("INDEPENDENT_MODE", "false").lower() == "true"

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'bei-ming-secret'
socketio = SocketIO(app, async_mode='threading')

session = None
bg_digestor = None
auto_explorer = None
dreamer = None
weaver = None
examiner = None
lock = Lock()

def init_system():
    global session, bg_digestor, auto_explorer, dreamer, weaver, examiner
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    session = ChatSession(config)
    
    # 独立模式
    if INDEPENDENT:
        os.environ["DEEPSEEK_API_KEY"] = ""
        print(">> 独立模式已开启，不再调用DeepSeek API")
    
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

    dreamer = Dreamer(
        cortex=session.cortex,
        imagination=session.imagination,
        engine=session.engine,
        socketio=socketio,
        idle_threshold=600,
        interval=300
    )
    dreamer.start()

    # 教学主任新模块
    weaver = KnowledgeWeaver(session.cortex, interval_minutes=120)
    weaver.start()
    xiaoyaoyou = XiaoYaoYou(session.cortex, session.imagination, session.lab, session.engine)
    xiaoyaoyou.start()
    alpha_loop = AlphaLoop(session.cortex, session.imagination, session.lab)
    alpha_loop.start()
    mingjing = MingJing(session.cortex, session.engine)
    mingjing.start()
    examiner = SelfExaminer(session.cortex, session.engine, interval_minutes=180)
    examiner.start()
    reviewer = ConsciousReviewer(session.cortex, session.engine, interval_minutes=30)
    reviewer.start()

    print(">> 系统初始化完成。")

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/favicon.ico')
def favicon_ico():
    return send_from_directory('static', 'favicon.svg', mimetype='image/svg+xml')

@app.route('/dashboard')
def dashboard():
    status = get_status(session.cortex)
    stats = load_stats()
    return render_template('dashboard.html', status=status, stats=stats)

@app.route('/api/status')
def api_status():
    return jsonify(get_status(session.cortex))

@socketio.on('user_input')
def handle_input(data):
    if dreamer: dreamer.update_activity()
    msg = data.get('message', '')
    with lock:
        try:
            reply = session.respond(msg)
            emit('response', {'reply': reply, 'status': f"皮层记忆: {len(session.cortex.memory)}"})
        except Exception as e:
            emit('response', {'reply': f'出错：{str(e)}'})

@socketio.on('teach')
def handle_teach(data):
    if dreamer: dreamer.update_activity()
    content = data.get('content', '').strip()
    if not content: return
    with lock:
        try:
            session.imagination.add({
                'source_url': 'user_teach',
                'title': '用户投喂',
                'snippet': content[:100],
                'full_text': content
            })
            session.engine.digest(focus_question=content[:20])
            emit('log', {'message': '投喂已消化'})
        except Exception as e:
            emit('response', {'reply': f'出错：{str(e)}'})

@socketio.on('connect')
def on_connect():
    emit('log', {'message': '连接成功'})

if __name__ == '__main__':
    init_system()
    print(">> 北冥之鲲已化鹏，教学主任已就位。")
    if INDEPENDENT: print(">> 独立模式：API导师已静默。")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)





