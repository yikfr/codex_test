import streamlit as st
import pymysql
from utils import render_sidebar
from datetime import timedelta  # 引入 timedelta 修复时区问题

st.set_page_config(page_title="学习记录", page_icon="📊")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

render_sidebar(active_page="history")

st.title("📊 学习记录")

def get_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        port=st.secrets["mysql"]["port"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        charset="utf8mb4",
        autocommit=True,
        ssl={"ssl": {}}
    )

def fetch_user_records(username, search_query=""):
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql_create = """
            CREATE TABLE IF NOT EXISTS `user_records` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `username` VARCHAR(50) NOT NULL,
                `action_type` VARCHAR(50) NOT NULL,
                `details` TEXT,
                `record_time` DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(sql_create)

            if search_query:
                sql_select = "SELECT * FROM `user_records` WHERE `username`=%s AND (`action_type` LIKE %s OR `details` LIKE %s) ORDER BY `record_time` DESC"
                like_pattern = f"%{search_query}%"
                cursor.execute(sql_select, (username, like_pattern, like_pattern))
            else:
                sql_select = "SELECT * FROM `user_records` WHERE `username`=%s ORDER BY `record_time` DESC"
                cursor.execute(sql_select, (username,))
            
            return cursor.fetchall()
    finally:
        conn.close()

search_term = st.text_input("🔍 搜索历史记录（输入关键词后回车，例如：高数、英语、生成计划...）")

records = fetch_user_records(st.session_state.username, search_term)

if not records:
    if search_term:
        st.info(f"没有找到包含 '{search_term}' 的记录，请尝试其他关键词。")
    else:
        st.info("暂无学习记录，快去生成你的第一个学习规划吧！")
else:
    for r in records:
        local_time = r['record_time'] + timedelta(hours=8)
        time_str = local_time.strftime("%Y-%m-%d %H:%M")
        
        st.markdown(f"""
        **📅 {time_str}**
        📖 {r['action_type']}
        📝 {r['details']}
        """)
        st.markdown("---")
