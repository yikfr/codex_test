import streamlit as st

st.set_page_config(page_title="学习计划", page_icon="📅")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

st.title("📅 学习计划生成")

st.subheader("输入你的学习需求")

col1, col2 = st.columns(2)

with col1:
    subject = st.selectbox("科目", ["高数", "英语", "计算机", "物理"])
    level = st.selectbox("难度", ["基础", "中等", "强化"])

with col2:
    days = st.slider("学习周期（天）", 3, 30, 7)
    daily_time = st.slider("每天学习时间（小时）", 1, 8, 2)

goal = st.text_area("你的目标（可选）")

if st.button("生成学习计划"):

    with st.spinner("正在生成学习计划..."):
        import time
        time.sleep(1)

    plan = f"""
Day1: 学习基础概念  
Day2: 做习题  
Day3: 复习  
...
"""

    st.success("生成成功！")

    st.subheader("📌 你的学习计划")
    st.code(plan)

    st.download_button("下载计划", plan, file_name="plan.txt")