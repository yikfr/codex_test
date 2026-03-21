import streamlit as st

st.set_page_config(page_title="习题生成", page_icon="✍️")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

st.title("✍️ 习题生成")

subject = st.selectbox("科目", ["高数", "英语", "计算机"])
difficulty = st.selectbox("难度", ["简单", "中等", "困难"])
question_type = st.selectbox("题型", ["选择题", "填空题", "简答题"])

if st.button("生成题目"):

    with st.spinner("正在生成题目..."):
        import time
        time.sleep(1)

    questions = [
        {"q": "1+1=?", "a": "2"},
        {"q": "2+2=?", "a": "4"}
    ]

    st.session_state.questions = questions

if "questions" in st.session_state:

    st.subheader("📚 题目")

    for i, q in enumerate(st.session_state.questions):
        st.write(f"{i+1}. {q['q']}")
        st.text_input("你的答案", key=f"ans_{i}")

    if st.button("提交答案"):
        st.success("已提交！（后端可批改）")

    if st.button("查看答案"):
        for i, q in enumerate(st.session_state.questions):
            st.write(f"{i+1} 正确答案：{q['a']}")