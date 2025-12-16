import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os

# 1. 設定頁面
st.set_page_config(page_title="熊貓迷因產生器", page_icon="🐼")
st.title("🐼 嘲諷熊貓迷因產生器 (Cloud API 版)")
st.write("輸入一句話，讓 AI 幫你生成專屬的嘲諷熊貓梗圖！")

# 2. 自動下載字型 (改用 requests)
def download_font():
    font_path = "NotoSansTC-Bold.otf"
    if not os.path.exists(font_path):
        with st.spinner("正在下載中文字型..."):
            url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Bold.otf"
            r = requests.get(url)
            with open(font_path, "wb") as f:
                f.write(r.content)
download_font()

# [cite_start]3. 定義 Hugging Face API 函數 (取代原本的 pipe) [cite: 8]
# 這裡使用 secrets 來保護你的 key，稍後教你設定
API_URL = "https://api-inference.huggingface.co/models/Lykon/DreamShaper"
headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

def query_huggingface(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content

# 4. 加字函數 (保持不變，直接沿用你寫好的)
def add_caption(image, text, font_path='NotoSansTC-Bold.otf'):
    original_width, original_height = image.size
    temp_draw = ImageDraw.Draw(image)
    font_size = int(original_width / 10)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    
    lines = textwrap.wrap(text, width=10)
    if lines:
        bbox = temp_draw.textbbox((0, 0), lines[0], font=font)
        line_height = bbox[3] - bbox[1]
        text_area_height = (line_height + 10) * len(lines) + 20
    else:
        text_area_height = 0

    new_height = original_height + text_area_height
    final_image = Image.new('RGB', (original_width, new_height), color=(255, 255, 255))
    final_image.paste(image, (0, 0))
    
    draw = ImageDraw.Draw(final_image)
    y_text = original_height + 10 
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x_text = (original_width - line_width) / 2
        draw.text((x_text, y_text), line, font=font, fill=(0, 0, 0))
        y_text += line_height + 10
    return final_image

# 5. UI 介面
user_text = st.text_input("請輸入梗圖文字：", "大家不要出聲\n讓他一個人尷尬")

if st.button("生成梗圖"):
    if not user_text:
        st.warning("請先輸入文字喔！")
    else:
        with st.spinner("呼叫遠端 AI 繪圖中 (API)..."):
            # 設定 Prompt
            prompt = "close up of a panda head with a funny human man face, smug expression, trolling face, meme style, simple black and white line art, vector art, flat color, white background, looking at viewer"
            negative_prompt = "body, paws, claws, realistic fur, 3d, shading, gradient, grey, fuzzy, blurry, realistic, photo, cute, animal face, sleeping, lying down"
            
            # 呼叫 API
            image_bytes = query_huggingface({
                "inputs": prompt,
                "parameters": {"negative_prompt": negative_prompt}
            })
            
            try:
                # 將回傳的 bytes 轉成圖片
                image = Image.open(io.BytesIO(image_bytes))
                
                # 加字
                final_image = add_caption(image, user_text)
                st.image(final_image, caption="你的專屬梗圖完成啦！")
                
            except Exception as e:
                st.error("生成失敗，可能是 API 忙碌中，請稍後再試。")
                st.write(e)
