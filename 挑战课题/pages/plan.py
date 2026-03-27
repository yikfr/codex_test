import streamlit as st
from deepseek_fb3 import ask_deepseek


st.set_page_config(page_title="学习计划", page_icon="📅")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("app.py")

if "stop_generate" not in st.session_state:
    st.session_state.stop_generate = False

st.title("📅 AI学习计划生成")

st.markdown("### 🎯 定制你的专属学习计划")

goal = st.text_area(
    "你的学习目标",
    placeholder="例如：我要在7天内掌握高数导数，并能熟练做题",
)

col1, col2 = st.columns(2)

with col1:
    days = st.slider("学习周期（天）", 3, 30, 7)

with col2:
    style = st.selectbox("学习强度", ["轻松", "标准", "高强度"])

daily_time = st.text_input(
    "每天学习时间",
    placeholder="例如：每天2小时"
)

col1, col2 = st.columns(2)

with col1:
    generate_btn = st.button("🚀 生成学习计划")

with col2:
    if st.button("⛔ 停止生成"):
        st.session_state.stop_generate = True

if generate_btn:

    st.session_state.stop_generate = False

    placeholder = st.empty()
    full_text = ""
    prompt = f"""
    请帮我制定学习计划：
    目标：{goal}
    学习周期：{days}天
    每天时间：{daily_time}
    学习强度：{style}
    """

    try:
        from deepseek_fb3 import ask_deepseek_stream

        for chunk in ask_deepseek_stream(prompt):

            if st.session_state.stop_generate:
                break

            full_text += chunk
            placeholder.markdown(full_text)

        st.session_state.plan = full_text

    except Exception as e:
        st.error("生成失败")

if "plan" in st.session_state:
    st.markdown("## 📌 你的学习计划")

    st.markdown("""
    <style>
    .plan-box {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 6px 15px rgba(0,0,0,0.1);
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="plan-box">{st.session_state.plan}</div>', unsafe_allow_html=True)

    st.download_button(
        "📥 下载学习计划",
        st.session_state.plan,
        file_name="study_plan.txt"
    )
