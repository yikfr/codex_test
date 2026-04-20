import streamlit as st
import pymysql
from utils import render_sidebar

st.set_page_config(page_title="个人主页", page_icon="👤", layout="centered")

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
current_membership = user.get('membership', 'start')
color = membership_colors.get(current_membership, "#666666")

st.markdown(f"""
<div style="background: linear-gradient(90deg, #2c3e50 0%, #000000 100%); 
            padding: 30px; border-radius: 15px; color: white; text-align: center;">
    <h1 style="color: white;">{user['display_name']}</h1>
    <p><i>{user['bio']}</i></p>
    <div style="display: inline-block; background: {color}; padding: 5px 15px; border-radius: 20px; font-weight: bold; color: white;">
        💎 会员等级：{current_membership.upper()}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
col1.metric("📅 学习规划已生成", f"{plans_count} 次")
col2.metric("📝 习题测试已完成", f"{quiz_count} 次")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["✏️ 编辑资料", "💎 会员中心", "🚪 账号设置"])

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
    st.subheader("💎 升级你的会员权益")
    
    tiers = {
        "start": {"price": "¥0/月", "desc": "基础体验，畅享基础AI助手功能", "color": "#A0A0A0"},
        "go": {"price": "¥19.9/月", "desc": "基础加速，更快的响应速度", "color": "#4b6cb7"},
        "pro": {"price": "¥49.9/月", "desc": "全能模型，优先队列，超长上下文", "color": "#8e44ad"},
        "ultra": {"price": "¥99.9/月", "desc": "极致尊享，定制模型，专属通道", "color": "#f1c40f"}
    }

    @st.dialog("扫码支付订阅")
    def payment_dialog(tier, price):
        st.write(f"您正在开通 **{tier.upper()} 会员**")
        st.write(f"应付金额: :red[**{price}**]")
        st.image("qr_code.png", width=200, caption="请使用微信/支付宝扫码")
        
        if st.button("我已支付"):
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users_test SET membership=%s WHERE username=%s", 
                               (tier, st.session_state.username))
            conn.commit()
            conn.close()
            st.success("支付核验成功！")
            st.balloons()
            time.sleep(1)
            st.rerun()

    cols = st.columns(4)
    for i, (tier, info) in enumerate(tiers.items()):
        with cols[i]:
            st.markdown(f"""
            <div style="border: 2px solid {info['color']}; padding: 15px; border-radius: 10px; text-align: center; height: 250px;">
                <h3 style="color: {info['color']};">{tier.upper()}</h3>
                <p style="font-size: 20px; font-weight: bold;">{info['price']}</p>
                <p style="font-size: 12px; color: #666;">{info['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"开通 {tier.upper()}", key=f"btn_{tier}"):
                payment_dialog(tier, info['price'])

with tab3:
    st.write(f"登录账号: `{st.session_state.username}`")
    if st.button("退出登录", type="primary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
