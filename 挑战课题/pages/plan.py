import streamlit as st
from deepseek_fb3 import ask_deepseek

st.set_page_config(page_title="学习计划", page_icon="📅")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("app.py")

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

if st.button("🚀 生成学习计划"):

    if goal.strip() == "":
        st.warning("请输入学习目标")
    else:

        with st.spinner("AI正在为你制定学习计划..."):

            prompt = f"""
            请帮我制定一个详细学习计划：

            学习目标：{goal}
            学习周期：{days}天
            每天时间：{daily_time}
            学习强度：{style}

            要求：
            1. 按“Day1, Day2...”格式输出
            2. 每天内容具体
            3. 包含学习 + 练习 + 复习
            4. 简洁清晰
            """

            try:
                response = ask_deepseek(prompt)
                st.session_state.plan = response
            except Exception as e:
                st.error("生成失败，请检查API或网络")

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
