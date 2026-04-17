import streamlit as st
import pymysql
from utils import render_sidebar

st.set_page_config(page_title="个人主页", page_icon="👤", layout="centered")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

render_sidebar()

def get_user_stats(username):
    conn = pymysql.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        charset="utf8mb4",
        ssl={"ssl": {}}
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM user_records WHERE username=%s AND action_type='📅 生成学习计划'", (username,))
            plans = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM user_records WHERE username=%s AND action_type='📝 完成习题测试'", (username,))
            quizzes = cursor.fetchone()[0]
        return plans, quizzes
    except Exception:
        return 0, 0
    finally:
        conn.close()

plans_count, quizzes_count = get_user_stats(st.session_state.username)

st.markdown(f"""
<div style="background: linear-gradient(90deg, #e6e6fa 0%, #d1e7ff 100%);
            padding: 30px; border-radius: 15px; color: white; text-align: center;">
    <h1 style="color: white; margin-bottom: 0px;">你好， {st.session_state.username}</h1>
    <p>好好学习，天天向上，董书予，加油！</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("📊 你的学习成就")
col1, col2 = st.columns(2)
col1.metric("📅 学习规划", f"{plans_count} 次")
col2.metric("📝 习题测试", f"{quizzes_count} 次")

st.markdown("---")

st.subheader("⚙️ 设置")
with st.expander("🚪 账号安全"):
    if st.button("安全退出登录", type="primary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
