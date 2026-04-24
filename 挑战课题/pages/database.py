import pymysql
import streamlit as st

class DBManager:
    def _get_conn(self):
        return pymysql.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            charset="utf8mb4",
            autocommit=True,
            ssl={"ssl": {}},
            init_command="SET time_zone='+08:00'" 
        )

    def save_chat_message(self, username, role, content):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO user_records (username, action_type, details) VALUES (%s, %s, %s)"
                cursor.execute(sql, (username, f"chat_{role}", content))
        finally:
            conn.close()

    def get_chat_history(self, username):
        conn = self._get_conn()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT action_type, details 
                FROM user_records 
                WHERE username=%s AND action_type LIKE 'chat_%%' 
                ORDER BY record_time ASC
                """
                cursor.execute(sql, (username,))
                return cursor.fetchall()
        finally:
            conn.close()
    def delete_chat_history(self, username):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM user_records WHERE username=%s AND action_type LIKE 'chat_%'"
                cursor.execute(sql, (username,))
            conn.commit()
        finally:
            conn.close(）
    def upgrade_membership(self, username, new_level):
        conn = self._get_conn()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE users_test SET membership=%s WHERE username=%s"
                cursor.execute(sql, (new_level, username))
            conn.commit()
        finally:
            conn.close()
