import streamlit as st
import requests
import pymysql
from streamlit_lottie import st_lottie
import time

st.set_page_config(page_title="AI学习助手", layout="centered")


def get_connection():
    try:
        return pymysql.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            charset="utf8mb4",
            autocommit=True,
            ssl={"ssl": {}}
            init_command="SET time_zone='+08:00'"
        )
    except Exception as e:
        st.error(f"数据库连接失败，详情: {e}")
        st.stop()


def init_db():
    conn = get_connection()
    with conn.cursor() as cursor:
        sql = """
        CREATE TABLE IF NOT EXISTS `users_test` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `username` varchar(50) UNIQUE NOT NULL,
            `password` varchar(50) NOT NULL,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(sql)
    conn.close()


def verify_login(username, password):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM `users_test` WHERE `username`=%s AND `password`=%s"
            cursor.execute(sql, (username, password))
            result = cursor.fetchone()
            return result is not None
    finally:
        conn.close()


def register_user(username, password):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO `users_test` (`username`, `password`) VALUES (%s, %s)"
            cursor.execute(sql, (username, password))
        return True, "注册成功"
    except pymysql.err.IntegrityError:
        return False, "用户名已存在，请换一个"
    except Exception as e:
        return False, f"注册失败: {e}"
    finally:
        conn.close()


init_db()

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stApp {
    background: linear-gradient(135deg,#e6e6fa,#d1e7ff);
}
.block-container {
    max-width: 420px;
    margin: auto;
    padding: 40px;
    border-radius: 18px;
    background: white;
    box-shadow: 0px 12px 30px rgba(0,0,0,0.12);
}
.stButton > button {
    width: 100%;
    height: 45px;
    border-radius: 10px;
    font-size: 16px;
    transition: 0.3s;
}
.stButton > button:hover {
    background-color: #4a90e2;
    color: white;
}
img {
    display: block;
    margin: auto;
    border-radius: 50%;
}
</style>
""", unsafe_allow_html=True)


def load_lottie():
    url = "https://assets2.lottiefiles.com/packages/lf20_usmfx6bp.json"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        return None
    return None


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""


def login_page():
    try:
        st.image("logo.png", width=110)
    except:
        pass

    st.markdown("<h2 style='text-align:center;'>AI学习助手</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        username = st.text_input("用户名", key="login_user")
        password = st.text_input("密码", type="password", key="login_pwd")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("登录"):
            if not username or not password:
                st.warning("请输入账号和密码")
            else:
                lottie = load_lottie()
                with st.spinner("正在验证..."):
                    if lottie:
                        st_lottie(lottie, height=120)

                    is_valid = verify_login(username, password)
                    time.sleep(0.5)

                if is_valid:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("登录成功！即将跳转...")
                    time.sleep(0.5)
                    st.switch_page("pages/chat.py")
                else:
                    st.error("用户名或密码错误")

    with tab2:
        new_user = st.text_input("新用户名", key="reg_user")
        new_pass = st.text_input("新密码", type="password", key="reg_pwd")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("注册"):
            if not new_user or not new_pass:
                st.warning("账号和密码不能为空")
            else:
                with st.spinner("正在向云端注册..."):
                    success, msg = register_user(new_user, new_pass)

                if success:
                    st.success("注册成功！请切换到【登录】页面登录。")
                else:
                    st.error(msg)


if st.session_state.logged_in:
    st.switch_page("pages/chat.py")
else:
    login_page()
