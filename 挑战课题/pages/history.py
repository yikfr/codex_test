import streamlit as st
import pymysql

st.set_page_config(page_title="学习记录", page_icon="📊")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

render_sidebar()

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


def fetch_user_records(username):
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

            sql_select = "SELECT * FROM `user_records` WHERE `username`=%s ORDER BY `record_time` DESC"
            cursor.execute(sql_select, (username,))
            return cursor.fetchall()
    finally:
        conn.close()


records = fetch_user_records(st.session_state.username)

if not records:
    st.info("暂无学习记录，快去生成你的第一个学习规划吧！")
else:
    for r in records:
        time_str = r['record_time'].strftime("%Y-%m-%d %H:%M")

        st.markdown(f"""
        **📅 {time_str}**  
        📖 {r['action_type']}  
        📝 {r['details']}
        """)
        st.markdown("---")
