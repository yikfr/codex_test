import streamlit as st

st.set_page_config(page_title="学习记录", page_icon="📊")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

st.title("📊 学习记录")

records = [
    {"date": "2026-03-01", "task": "高数学习", "time": "2h"},
    {"date": "2026-03-02", "task": "英语单词", "time": "1h"},
]

for r in records:
    st.markdown(f"""
    **📅 {r['date']}**  
    📖 {r['task']}  
    ⏱️ {r['time']}
    """)