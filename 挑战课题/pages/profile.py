import streamlit as st
import pymysql
from utils import render_sidebar

st.set_page_config(page_title="个人中心", layout="wide")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("log_in.py")

render_sidebar(active_page="profile")

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

def fetch_user_info():
    conn = get_db()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM users_test WHERE username=%s", (st.session_state.username,))
        return cursor.fetchone()
    conn.close()

def update_profile(display_name, bio):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE users_test SET display_name=%s, bio=%s WHERE username=%s", 
                       (display_name, bio, st.session_state.username))
    conn.commit()
    conn.close()

user_info = fetch_user_info()

st.markdown(f"""
<div style="padding: 20px; border-radius: 10px; background-color: #f0f2f6;">
    <h1>{user_info['display_name']}</h1>
    <p><i>"{user_info['bio']}"</i></p>
    <span style="background: gold; padding: 5px 10px; border-radius: 5px; font-weight: bold;">
        💎 {user_info['membership']}
    </span>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["✏️ 编辑资料", "💎 会员中心", "🚪 账号设置"])

with tab1:
    st.subheader("修改个人信息")
    with st.form("edit_profile"):
        new_name = st.text_input("昵称", value=user_info['display_name'])
        new_bio = st.text_area("个性签名", value=user_info['bio'])
        if st.form_submit_button("保存修改"):
            update_profile(new_name, new_bio)
            st.success("信息已更新！")
            st.rerun()

with tab2:
    st.subheader("会员尊享权益")
    st.write(f"您当前的级别是：**{user_info['membership']}**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("✅ 基础功能使用")
        st.info("✅ 历史记录查询")
    with col2:
        st.warning("🔒 更多高级功能（即将上线）")
        
    if user_info['membership'] == '普通会员':
        if st.button("🚀 升级为高级会员"):
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users_test SET membership='高级会员' WHERE username=%s", (st.session_state.username,))
            conn.commit()
            conn.close()
            st.balloons()
            st.rerun()

with tab3:
    st.subheader("安全设置")
    if st.button("安全退出登录", type="primary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
