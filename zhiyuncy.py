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
    "Life is like a journey against the current, and I am also a passer - by.",
    "Under the vast starry sky, I pursue the star that belongs to me.",
    "Love is like a flower blooming. Only after experiencing wind and rain can it bloom in the most beautiful colors.",
    "Time is like a song, with melodies intertwined. I wish to dance with you on the stage of time.",
    "In the hustle and bustle of the world, only your laughter is like a gentle breeze, sweeping away my worries.",
    "In the depths of my dreams, my soul dances with yours,跨越 the boundaries of time.",
    "Every yellowed photo holds our youth and dreams of the past.",
    "Let the wind carry my yearning for you and drift it to the distant sky.",
    "The hands of time will not turn back, but I will always guard you in my memories.",
    "Floating clouds chase dreams, and return to water as their roots. I wish to walk with you throughout this life.",
    "Sitting alone under the lamp, I miss you eagerly. I wish to follow the years and share the morning and evening with you.",
    "The wind sends the fragrance of plum blossoms, and snowflakes fall bit by bit. Time passes slowly, and I only wish to enjoy it with you.",
    "A solitary boat casts a shadow, and the moon shines on the river waves. My heart is towards the distance, and I wish to be in the same boat with you.",
    "As time goes by, my feelings remain unchanged. Can you promise me a lifetime of peace?",
    "Sitting alone in the cold window, with the night rain falling quietly. My heart is like withered grass, and my tears have become a poem.",
    "Flowers fade and fly, time is ruthless. The returning shadow in the sky only leaves traces of tears.",
    "Flowers are in full bloom, and laughter is like a song. In the youthful years, there are full of traces of dreams.",
    "Watching the flowers fall alone, my heart is filled with beautiful memories of you."
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
                "content": "As a Chinese - language lyric - writing expert, please write a song for me."
            }, {
                "role": "assistant",
                "content": "Of course, to create lyrics, please tell me some of your ideas."
            }, {
                "role": "user",
                "content": f"Please generate lyrics according to the following requirements: Theme: {theme}, Requirements: {demand} Please note that rhyming is the most important!!!"
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Failed to generate lyrics: {str(e)}")
        return None


# 音乐创作（自定义模式）
def create_music_custom(prompt, tags="", title="", continueClipId="", continueAt="", mvVersion="chirp - v4"):
    url = BASE_URL + "/_open/suno/music/generate"
    headers = {
        "key": API_KEY,
        "x - token": X_TOKEN,
        "x - userId": X_USERID
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
        st.error(f"Music creation request failed, status code: {response.status_code}, error message: {response.text}")
        return None


# 获取音乐生成状态并提取音频地址
def get_music_state(taskBatchId):
    url = BASE_URL + f"/_open/suno/music/getState?taskBatchId={taskBatchId}"
    headers = {
        "x - token": X_TOKEN,
        "x - userId": X_USERID
    }
    mp3_urls = []

    while True:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            result = response.json()

            if 'data' not in result:
                st.error("The response format for getting the music state is incorrect: The 'data' field was not found.")
                break

            for item in result['data'].get('items', []):
                if item['status'] == 30:
                    mp3_urls.append(item.get('cld2AudioUrl'))
            if all(item['status'] == 30 for item in result['data']['items']):
                st.success("All music generation tasks have been successfully completed.")
                break
            elif any(item['status'] == 40 for item in result['data']['items']):
                st.error("Some music generation tasks failed.")
                break
            time.sleep(10)
        else:
            st.error(f"Error getting the music state, status code: {response.status_code}, error message: {response.text}")
            break
    if not mp3_urls:
        st.warning("There is no generated audio.")
    return mp3_urls


# 合并整首歌
def concat_whole_song(clipId):
    url = BASE_URL + f"/_open/suno/music/concat?clipId={clipId}"
    headers = {
        "x - token": X_TOKEN,
        "x - userId": X_USERID
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Request to concatenate the whole song failed, status code: {response.status_code}, error message: {response.text}")
        return None


# 创建人声伴奏分离任务
def create_stems_task(clipId):
    url = BASE_URL + f"/_open/suno/music/stems?clipId={clipId}"
    headers = {
        "x - token": X_TOKEN,
        "x - userId": X_USERID
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to create the vocal - accompaniment separation task, status code: {response.status_code}, error message: {response.text}")
        return None


# 辅助函数获取clipId
def get_clip_id(audio_url):
    match = re.search(r'([\w - ]+)\.mp3', audio_url)
    if match:
        return match.group(1)
    return None


# 获取人声伴奏分离状态
def get_stems_state(taskBatchId):
    url = BASE_URL + f"/_open/suno/music/stemsState?taskBatchId={taskBatchId}"
    headers = {
        "x - token": X_TOKEN,
        "x - userId": X_USERID
    }
    while True:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if 'data' not in result:
                st.error("The response format for getting the separation state is incorrect: The 'data' field was not found.")
                break

            if result['data']['status'] == 1:  # 成功
                st.success("The vocal - accompaniment separation task is completed!")
                return result['data']['audioUrls']
            elif result['data']['status'] == 2:  # 失败
                st.error("The vocal - accompaniment separation task failed.")
                break
            time.sleep(10)
        else:
            st.error(f"Error getting the separation state, status code: {response.status_code}, error message: {response.text}")
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
    st.title("ZhiYun Music Creation")

    # 创建左右两列，调整比例使得音乐生成部分略大
    col1, col2 = st.columns([2, 3])

    # 歌词生成部分（左列）
    with col1:
        st.header("Lyric Generation")
        theme = st.text_input("Theme", placeholder="Please enter the theme, such as love, dreams, etc.")
        demand = st.text_area("Other Requirements", placeholder="Please enter other requirements, such as lyric structure, style, etc.")

        # 按钮禁用逻辑
        if theme and demand:
            generate_button = st.button("Generate Lyrics")
        else:
            generate_button = st.button("Generate Lyrics", disabled=True)

        st.markdown('<hr>', unsafe_allow_html=True)
        if generate_button:
            with st.spinner("Generating lyrics..."):
                lyrics = generate_lyrics(theme, demand)
                if lyrics:
                    st.text_area("Generated Lyrics", value=lyrics, height=300)
                else:
                    st.warning("Failed to generate lyrics. Please try again later.")

    # 音乐生成部分（右列）
    with col2:
        st.header("Music Generation")
        prompt = st.text_area("Enter Lyrics", placeholder="Please enter the lyrics", height=300)  # 调整高度为300像素
        title = st.text_input("Song Name", placeholder="Please enter the song name")

        # 按钮禁用逻辑
        if prompt and title:
            music_button = st.button("Create Music")
        else:
            music_button = st.button("Create Music", disabled=True)

        if music_button:
            # 自定义模式创作音乐
            creation_result = create_music_custom(prompt, title=title)
            if creation_result:
                task_batch_id = creation_result['data'].get('taskBatchId')
                if task_batch_id:
                    st.write(f"Music generation is in progress. {task_batch_id}")
                    # 获取音乐生成状态并获取音频地址
                    mp3_urls = get_music_state(task_batch_id)
                    if mp3_urls:
                        st.write("Play MP3 Audio:")
                        for url in mp3_urls:
                            st.audio(url)

                        # 仅在音乐生成成功后显示合并整首歌和人声伴奏分离按钮
                        if st.button("Concatenate the Whole Song"):
                            clip_id = get_clip_id(mp3_urls[0])
                            if clip_id:
                                concat_result = concat_whole_song(clip_id)
                                if concat_result:
                                    st.write("The task of concatenating the whole song has been started. Task information:", concat_result)

                        if st.button("Separate Vocals and Accompaniment"):
                            clip_id = get_clip_id(mp3_urls[0])
                            if clip_id:
                                stems_result = create_stems_task(clip_id)
                                if stems_result:
                                    task_batch_id = stems_result['data'].get('taskBatchId')
                                    if task_batch_id:
                                        st.write("The vocal - accompaniment separation task has been started. Processing...")
                                        # 获取人声伴奏分离状态并播放分离后的音频
                                        audio_urls = get_stems_state(task_batch_id)
                                        if audio_urls:
                                            st.write("Separation Results:")
                                            for audio_url in audio_urls:
                                                st.audio(audio_url)
                                        else:
                                            st.error("Vocal - accompaniment separation failed. Please try again later.")
                                    else:
                                        st.error("The vocal - accompaniment separation task ID was not found in the response.")
                                else:
                                    st.error("Failed to create the vocal - accompaniment separation task.")
                    else:
                        st.warning("There is no generated audio.")
                else:
                    st.error("The task batch ID was not found in the response.")
            else:
                st.error("Music creation request failed. Please check your input or contact the administrator.")

    # 高潮提取模块
    st.header("Ringtone Making")
    uploaded_file = st.file_uploader("Please select a music file to upload", type=['mp3', 'wav'])
    highlight_duration = st.number_input('Duration of the ringtone part (seconds)', min_value=1, value=15)

    if st.button('Click to Make Ringtone'):
        output_folder = r"C:\Users\12819\Music\help"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        extracted_file_path = extract_music_highlights(uploaded_file, output_folder, highlight_duration)

        if extracted_file_path:
            st.success(f"Successfully extracted the highlight part of the music. The file is saved at: {extracted_file_path}")
            # 在线播放提取的音频
            st.audio(extracted_file_path)
        else:
            st.error("Failed to extract the highlight part of the music.")

    # 金句框架部分
    st.header("Golden Sentence Recommendation")
    if st.button("Generate Golden Sentence"):
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
st.markdown("<footer>© 2024 最终版权 刘昱樟所有 </footer>", unsafe_allow_html=True)