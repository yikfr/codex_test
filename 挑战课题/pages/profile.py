import streamlit as st
import pymysql
from utils import render_sidebar

st.set_page_config(page_title="个人主页", page_icon="👤", layout="centered")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("log_in.py")

render_sidebar(active_page="chat")

def get_db():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"], 
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"], 
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"], 
        charset="utf8mb4",
        ssl={"ssl": {}}
    )

conn = get_db()
cursor = conn.cursor(pymysql.cursors.DictCursor)

cursor.execute("SELECT * FROM users_test WHERE username=%s", (st.session_state.username,))
user = cursor.fetchone()

cursor.execute("SELECT COUNT(*) FROM user_records WHERE username=%s AND action_type='📅 生成学习计划'", (st.session_state.username,))
plans_count = cursor.fetchone()['COUNT(*)']

cursor.execute("SELECT COUNT(*) FROM user_records WHERE username=%s AND action_type='📝 完成习题测试'", (st.session_state.username,))
quiz_count = cursor.fetchone()['COUNT(*)']

conn.close()

membership_colors = {
    "start": "#A0A0A0", 
    "go": "#4b6cb7",    
    "pro": "#8e44ad",   
    "ultra": "#f1c40f"  
}
color = membership_colors.get(user['membership'], "#666666")

st.markdown(f"""
<div style="background: linear-gradient(90deg, #2c3e50 0%, #000000 100%); 
            padding: 30px; border-radius: 15px; color: white; text-align: center;">
    <h1 style="color: white;">{user['display_name']}</h1>
    <p><i>{user['bio']}</i></p>
    <div style="display: inline-block; background: {color}; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
        💎 会员等级：{user['membership'].upper()}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
col1.metric("📅 学习规划已生成", f"{plans_count} 次")
col2.metric("📝 习题测试已完成", f"{quiz_count} 次")

st.markdown("---")

tab1, tab2 = st.tabs(["✏️ 编辑资料", "🚪 账号设置"])

with tab1:
    with st.form("update_profile"):
        new_name = st.text_input("修改昵称", value=user['display_name'])
        new_bio = st.text_area("个性签名", value=user['bio'])
        if st.form_submit_button("保存资料"):
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users_test SET display_name=%s, bio=%s WHERE username=%s", 
                               (new_name, new_bio, st.session_state.username))
            conn.commit()
            conn.close()
            st.success("资料已更新！")
            st.rerun()

with tab2:
    st.write(f"登录账号: `{st.session_state.username}`")
    if st.button("退出登录", type="primary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
