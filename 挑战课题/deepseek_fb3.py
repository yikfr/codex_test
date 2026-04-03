import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个智能学习助手"},
        {"role": "user", "content": "你好"},
    ],
    stream=False
)


def ask_deepseek(prompt, history=None):
    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content
