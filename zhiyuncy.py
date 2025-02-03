from zhipuai import ZhipuAI
import requests
import streamlit as st
import re
import time
import random
import os
from pychorus import find_and_output_chorus

# 初始化智谱AI客户端
client = ZhipuAI(api_key="d6415b0b9a8f5d2a18463afc7b617b05.L0aTMIsPzFAsQL3k")

# API基础URL
BASE_URL = "https://dzwlai.com/apiuser"

# 认证信息
API_KEY = "2jhskfdgjldfgjldf-9639-kiuwoiruk"
X_TOKEN = "sk-0e591b28bd9c46378c654e33cd927a83"
X_USERID = "abc001"

# 金句
GOLDEN_SENTENCES = [
    "人生如逆旅，我亦是行人。",
    "在浩瀚星空下，我追寻那颗属于我的星。",
    "爱像花开，经历风雨后，才会绽放出最美的色彩。",
    "岁月如歌，旋律交错，愿与你共舞在时光的舞台。",
    "尘世的喧嚣中，唯有你的笑声像清风，拂去我的忧虑.",
    "在梦的深处，我与你的灵魂共舞，跨越时间的界限",
    "每一张泛黄的照片，都藏着我们曾经的青春与梦想",
    "让风带走我对你的思念，随它漂流到遥远的天际",
    "时间的指针不会倒转，但我会在回忆中永远守护你。",
    "浮云逐梦，归根若水，愿与君长行此生。",
    "灯下独坐，思君若渴，愿随岁月，共逐晨昏。",
    "风送梅香，雪落点滴，岁月悠悠，唯愿共赏",
    "孤舟泛影，月照江波，心向远方，与你同舟",
    "时光荏苒，情愫未减，君可否共许我一世长安？",
    "寒窗独坐，夜雨悄然，心似荒草，泪已成诗",
    "花谢花飞，岁月无情，长空归影，唯泪痕累累。",
    "繁花盛开，笑声如歌，青涩的岁月里，满是梦的痕迹",
    "独自一人看花落，心中却充满了与你的美好回忆"
]

# 随机生成金句函数
def generate_golden_sentence():
    return random.choice(GOLDEN_SENTENCES)

# 歌词生成函数
def generate_lyrics(theme, demand):
    try:
        response = client.chat.completions.create(
            model="glm-4-airx",
            messages=[{
                "role": "user",
                "content": "作为一名华语作词专家，请为我写一首歌曲"
            }, {
                "role": "assistant",
                "content": "当然，要创作歌词，请告诉我一些你的想法"
            }, {
                "role": "user",
                "content": f"请根据以下要求生成歌词：主题：{theme}，要求：{demand} 请注意押韵是最重要的！！！"
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"生成歌词失败：{str(e)}")
        return None

# 音乐创作（自定义模式）
def create_music_custom(prompt, tags="", title="", continueClipId="", continueAt="", mvVersion="chirp-v4"):
    url = BASE_URL + "/_open/suno/music/generate"
    headers = {
        "key": API_KEY,
        "x-token": X_TOKEN,
        "x-userId": X_USERID
    }
    data = {
        "inputType": "20",
        "makeInstrumental": "false",
        "prompt": prompt,
        "tags": tags,
        "title": title,
        "continueClipId": continueClipId,
        "continueAt": continueAt,
        "mvVersion": mvVersion
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"音乐创作请求失败，状态码：{response.status_code}，错误信息：{response.text}")
        return None

# 获取音乐生成状态并提取音频地址
def get_music_state(taskBatchId):
    url = BASE_URL + f"/_open/suno/music/getState?taskBatchId={taskBatchId}"
    headers = {
        "x-token": X_TOKEN,
        "x-userId": X_USERID
    }
    mp3_urls = []

    while True:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            result = response.json()

            if 'data' not in result:
                st.error("获取音乐状态响应格式错误：未找到'data'字段。")
                break

            for item in result['data'].get('items', []):
                if item['status'] == 30:
                    mp3_urls.append(item.get('cld2AudioUrl'))
            if all(item['status'] == 30 for item in result['data']['items']):
                st.success("所有音乐生成任务已成功完成。")
                break
            elif any(item['status'] == 40 for item in result['data']['items']):
                st.error("部分音乐生成任务失败。")
                break
            time.sleep(10)
        else:
            st.error(f"获取音乐状态出错，状态码：{response.status_code}，错误信息：{response.text}")
            break
    if not mp3_urls:
        st.warning("没有生成的音频。")
    return mp3_urls

# 合并整首歌
def concat_whole_song(clipId):
    url = BASE_URL + f"/_open/suno/music/concat?clipId={clipId}"
    headers = {
        "x-token": X_TOKEN,
        "x-userId": X_USERID
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"合并整首歌请求失败，状态码：{response.status_code}，错误信息：{response.text}")
        return None

# 创建人声伴奏分离任务
def create_stems_task(clipId):
    url = BASE_URL + f"/_open/suno/music/stems?clipId={clipId}"
    headers = {
        "x-token": X_TOKEN,
        "x-userId": X_USERID
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"人声伴奏分离任务创建失败，状态码：{response.status_code}，错误信息：{response.text}")
        return None

# 辅助函数获取clipId
def get_clip_id(audio_url):
    match = re.search(r'([\w-]+)\.mp3', audio_url)
    if match:
        return match.group(1)
    return None

# 获取人声伴奏分离状态
def get_stems_state(taskBatchId):
    url = BASE_URL + f"/_open/suno/music/stemsState?taskBatchId={taskBatchId}"
    headers = {
        "x-token": X_TOKEN,
        "x-userId": X_USERID
    }
    while True:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if 'data' not in result:
                st.error("获取分离状态响应格式错误：未找到'data'字段。")
                break

            if result['data']['status'] == 1:  # 成功
                st.success("人声伴奏分离任务完成！")
                return result['data']['audioUrls']
            elif result['data']['status'] == 2:  # 失败
                st.error("人声伴奏分离任务失败。")
                break
            time.sleep(10)
        else:
            st.error(f"获取分离状态出错，状态码：{response.status_code}，错误信息：{response.text}")
            break
    return []

# 高潮提取函数
def extract_music_highlights(input_file, output_folder, highlight_duration):
    if input_file is not None:
        file_name = input_file.name
        output_file_name = os.path.splitext(file_name)[0] + '_high.wav'
        output_file_path = os.path.join(output_folder, output_file_name)

        try:
            find_and_output_chorus(input_file, output_file_path, highlight_duration)
            if os.path.exists(output_file_path):
                return output_file_path
            else:
                return None
        except Exception as e:
            return f"Error extracting highlight: {e}"
    else:
        return None

# Streamlit应用
def main():
    st.title("智韵创音")

    # 创建左右两列，调整比例使得音乐生成部分略大
    col1, col2 = st.columns([2, 3])

    # 歌词生成部分（左列）
    with col1:
        st.header("歌词生成")
        theme = st.text_input("主题", placeholder="请输入主题，如爱情、梦想等")
        demand = st.text_area("其他要求", placeholder="请输入其他要求，如歌词结构、风格等")

        # 按钮禁用逻辑
        if theme and demand:
            generate_button = st.button("生成歌词")
        else:
            generate_button = st.button("生成歌词", disabled=True)

        st.markdown('<hr>', unsafe_allow_html=True)
        if generate_button:
            with st.spinner("生成歌词..."):
                lyrics = generate_lyrics(theme, demand)
                if lyrics:
                    st.text_area("生成的歌词", value=lyrics, height=300)
                else:
                    st.warning("未能生成歌词，请稍后再试。")

    # 音乐生成部分（右列）
    with col2:
        st.header("音乐生成")
        prompt = st.text_area("输入歌词", placeholder="请输入歌词", height=300)  # 调整高度为300像素
        title = st.text_input("歌曲名称", placeholder="请输入歌曲名称")

        # 按钮禁用逻辑
        if prompt and title:
            music_button = st.button("创作音乐")
        else:
            music_button = st.button("创作音乐", disabled=True)

        if music_button:
            # 自定义模式创作音乐
            creation_result = create_music_custom(prompt, title=title)
            if creation_result:
                task_batch_id = creation_result['data'].get('taskBatchId')
                if task_batch_id:
                    st.write(f"正在进行音乐生成。 {task_batch_id}")
                    # 获取音乐生成状态并获取音频地址
                    mp3_urls = get_music_state(task_batch_id)
                    if mp3_urls:
                        st.write("播放MP3音频：")
                        for url in mp3_urls:
                            st.audio(url)

                        # 仅在音乐生成成功后显示合并整首歌和人声伴奏分离按钮
                        if st.button("合并整首歌"):
                            clip_id = get_clip_id(mp3_urls[0])
                            if clip_id:
                                concat_result = concat_whole_song(clip_id)
                                if concat_result:
                                    st.write("合并整首歌任务已启动。任务信息：", concat_result)

                        if st.button("人声伴奏分离"):
                            clip_id = get_clip_id(mp3_urls[0])
                            if clip_id:
                                stems_result = create_stems_task(clip_id)
                                if stems_result:
                                    task_batch_id = stems_result['data'].get('taskBatchId')
                                    if task_batch_id:
                                        st.write("人声伴奏分离任务已启动。正在处理...")
                                        # 获取人声伴奏分离状态并播放分离后的音频
                                        audio_urls = get_stems_state(task_batch_id)
                                        if audio_urls:
                                            st.write("分离结果：")
                                            for audio_url in audio_urls:
                                                st.audio(audio_url)
                                        else:
                                            st.error("人声伴奏分离失败，请稍后再试。")
                                    else:
                                        st.error("在响应中未找到人声伴奏分离任务ID。")
                                else:
                                    st.error("人声伴奏分离任务创建失败。")
                    else:
                        st.warning("没有生成的音频。")
                else:
                    st.error("在响应中未找到任务批次ID。")
            else:
                st.error("音乐创作请求失败，请检查输入或联系管理员。")

    # 高潮提取模块
    st.header("铃声制作")
    uploaded_file = st.file_uploader("请选择音乐文件上传", type=['mp3', 'wav'])
    highlight_duration = st.number_input('铃声部分时长（秒）', min_value=1, value=15)

    if st.button('点击制作铃声'):
        output_folder = r"C:\Users\12819\Music\help"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        extracted_file_path = extract_music_highlights(uploaded_file, output_folder, highlight_duration)

        if extracted_file_path:
            st.success(f"成功提取音乐高潮部分，文件保存在: {extracted_file_path}")
            # 在线播放提取的音频
            st.audio(extracted_file_path)
        else:
            st.error("提取音乐高潮部分失败。")

    # 金句框架部分
    st.header("金句推荐")
    if st.button("生成金句"):
        golden_sentence = generate_golden_sentence()
        st.write(golden_sentence)


if __name__ == "__main__":
    main()

# 添加一些CSS样式优化界面平衡
st.markdown("""
<style>
    body {
        background: linear-gradient(to bottom right, #e0e0e0, #f5f5f5); 
        background-size: cover;
        font-family: 'Roboto', sans-serif; 
    }

   .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 15px 32px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        cursor: pointer;
        transition: background-color 0.3s;
    }

   .stButton > button:hover {
        background-color: #388E3C;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); 
    }

    h1 {
        font-size: 32px;
        color: #388E3C;
        text-align: center;
        margin-bottom: 20px;
    }

   .card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        padding: 30px;
        margin: 15px 0;
    }

   .stTextInput,.stTextArea {
        border: 2px solid #4CAF50;
        border-radius: 8px;
        padding: 10px;
    }

   .stTextInput input:focus,.stTextArea textarea:focus {
        border-color: #4CAF50;
        outline: none;
    }

    footer {
        text-align: center;
        color: gray;
        margin-top: 30px;
        padding: 10px;
        border-top: 2px solid #e6e6e6;
    }

   .music-play-button {
        background-color: #FFC107; 
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        border-radius: 5px;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); 
        transition: background-color 0.3s;
    }

   .music-play-button:hover {
        background-color: #FFA000; 
    }

   .music-list-item {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

   .music-song-name {
        font-family: 'Arial', sans-serif;
        color: #333;
        font-size: 16px;
    }

   .music-action-button {
        background-color: #607D8B;
        color: white;
        border: none;
        padding: 5px 10px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 12px;
        border-radius: 3px;
        cursor: pointer;
        margin-left: 10px;
        transition: background-color 0.3s;
    }

   .music-action-button:hover {
        background-color: #455A64; 
    }

   .card-header {
        font-size: 1.5em;
        color: #388E3C;
    }

   .music-player-container {
        margin-top: 10px;
        text-align: center;
    }

   .stButton > button:disabled {
        background-color: #BDBDBD;
        cursor: not-allowed;
    }

</style>
""", unsafe_allow_html=True)

# 底部版权
st.markdown("<footer>© 2024 最终版权刘昱樟所有 “智音”音乐生成器</footer>", unsafe_allow_html=True)