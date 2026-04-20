import pymysql
import streamlit as st

class DBManager:
    def _get_conn(self):
        """统一获取数据库连接"""
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

    def save_chat_message(self, username, role, content):
        """保存聊天记录"""
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                # role 存进 action_type，content 存进 details
                sql = "INSERT INTO user_records (username, action_type, details) VALUES (%s, %s, %s)"
                cursor.execute(sql, (username, f"chat_{role}", content))
        finally:
            conn.close()

    def get_chat_history(self, username):
        """获取聊天记录"""
        conn = self._get_conn()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT action_type, details 
                FROM user_records 
                WHERE username=%s AND action_type LIKE 'chat_%' 
                ORDER BY record_time ASC
                """
                cursor.execute(sql, (username,))
                return cursor.fetchall()
        finally:
            conn.close()
