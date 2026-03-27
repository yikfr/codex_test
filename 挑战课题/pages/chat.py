import streamlit as st
import time
from deepseek_fb3 import ask_deepseek

st.set_page_config(page_title="AI聊天", page_icon="🤖")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("请先登录")
    st.switch_page("log_in.py")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 AI学习助手")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.button("🧹 清空对话"):
    st.session_state.messages = []
    st.rerun()

user_input = st.chat_input("请输入你的问题...")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):

        placeholder = st.empty()

        full_response = ""

        response = ask_deepseek(user_input, st.session_state.messages)
        st.markdown(response, unsafe_allow_html=True)

        for char in response:
            full_response += char
            placeholder.markdown(full_response)
            time.sleep(0.02)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })
