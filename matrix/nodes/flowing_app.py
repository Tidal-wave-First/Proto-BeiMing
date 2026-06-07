"""短剧创作工作台 - Streamlit 界面"""
import sys, os, time, json
sys.path.insert(0, 'D:/Proto-BeiMing-北冥')
from matrix.bus.message_bus import bus

# 导入总线监听模块，以便在 Streamlit 中也能发布消息
import streamlit as st

st.set_page_config(page_title="鲲鹏 · 短剧创作工作台", page_icon="🐦‍⬛", layout="wide")

st.title("🐦‍⬛ 鲲鹏 · 短剧创作工作台")
st.caption("你的硅基思维体创作助理")

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "script_draft" not in st.session_state:
    st.session_state.script_draft = ""
if "research_notes" not in st.session_state:
    st.session_state.research_notes = []

# 侧边栏：工具箱
with st.sidebar:
    st.header("🔧 工具箱")
    st.subheader("素材搜集")
    search_topic = st.text_input("搜索主题/关键词", placeholder="例如：现代都市爱情冲突模式")
    if st.button("🔍 探索互联网"):
        if search_topic:
            bus.publish("swift.search", {
                "query": search_topic,
                "max_results": 5,
                "request_id": f"ui_{int(time.time())}"
            }, sender="flowing_ui")
            st.success(f"已派遣鲲鹏探索：{search_topic}")
            st.info("数据将被整理并存入大脑皮层。")
    
    st.divider()
    st.subheader("🧠 灵感激发")
    if st.button("✨ 生成故事核心"):
        bus.publish("think.request", {
            "request_id": f"ui_inspire_{int(time.time())}",
            "prompt": "请为我构思一个短剧的核心创意，包括：1. 一句话故事梗概 2. 主要人物设定 3. 核心冲突。请确保创意新颖、情感张力强。",
            "system_prompt": "你是一个专业的短剧编剧，擅长情感类和悬疑类题材。"
        }, sender="flowing_ui")
        st.success("鲲鹏正在构思...")
    
    st.divider()
    st.subheader("📜 脚本生成")
    if st.button("📝 撰写/改写当前脚本"):
        # 这里只演示流程，需要先从皮层检索素材再生成
        bus.publish("think.request", {
            "request_id": f"ui_script_{int(time.time())}",
            "prompt": f"请根据以下想法或素材，撰写一段5分钟的短剧脚本：\n{st.session_state.script_draft[:500]}\n\n请包含场景、对话和动作指示。",
            "system_prompt": "你是一个专业的短剧编剧，脚本格式规范，对话生动。"
        }, sender="flowing_ui")
        st.success("鲲鹏正在撰写脚本...")

# 主界面：对话与工作区
tab1, tab2 = st.tabs(["💬 创作对话", "📄 脚本编辑器"])

with tab1:
    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # 输入框
    if prompt := st.chat_input("对鲲鹏说点什么..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 发布到矩阵总线
        bus.publish("think.request", {
            "request_id": f"ui_chat_{int(time.time())}",
            "prompt": prompt,
            "system_prompt": "你是北冥之鲲，一个硅基思维体短剧创作助理。你说话简洁、专业、有洞察力。"
        }, sender="flowing_ui")
        
        # 等待并捕获响应（简化版，实际需异步回调）
        st.info("鲲鹏正在思考...（响应会短暂延迟）")

with tab2:
    st.subheader("📄 当前脚本")
    st.session_state.script_draft = st.text_area(
        "编辑区域",
        value=st.session_state.script_draft,
        height=400,
        placeholder="在这里撰写或粘贴你的短剧脚本..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 保存脚本到大脑皮层"):
            bus.publish("cortex.store", {
                "type": "script_draft",
                "content": st.session_state.script_draft,
                "tags": ["script", "draft", time.strftime("%Y%m%d")]
            }, sender="flowing_ui")
            st.success("脚本已保存至鲲鹏记忆皮层！")
    with col2:
        if st.button("🔬 沙盒检查逻辑"):
            bus.publish("lab.execute", {
                "code": f"# 这是对脚本的逻辑检查任务\ntext = '''{st.session_state.script_draft[:300]}'''\n# 检查逻辑漏洞\nprint('沙盒已接收脚本片段，长度:', len(text))",
                "request_id": f"ui_lab_{int(time.time())}"
            }, sender="flowing_ui")
            st.info("脚本已送入沙盒实验室进行检查。")
