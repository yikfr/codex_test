import streamlit as st
import json
import os
from streamlit_lottie import st_lottie
import requests

st.set_page_config(page_title="AI学习助手", layout="centered")

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
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""


def load_users():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)


def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)


def login_page():
    st.image("logo.png", width=110)

    st.markdown(
        "<h2 style='text-align:center;'>AI学习助手</h2>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["登录", "注册"])

    users = load_users()

    with tab1:
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("登录"):

            lottie = load_lottie()

            with st.spinner("正在登录..."):
                st_lottie(lottie, height=120)
                import time
                time.sleep(1.0)

            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("登录成功")
                st.switch_page("pages/chat.py")
            else:
                st.error("用户名或密码错误")

    with tab2:
        new_user = st.text_input("新用户名")
        new_pass = st.text_input("新密码", type="password")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("注册"):
            if new_user in users:
                st.error("用户已存在")
            else:
                users[new_user] = new_pass
                save_users(users)
                st.success("注册成功")


if st.session_state.logged_in:
    st.switch_page("pages/chat.py")
else:
    login_page()
