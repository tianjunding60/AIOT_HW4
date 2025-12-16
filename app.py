import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient
import textwrap
import os
import requests  # 記得 import requests

# 1. 設定頁面
st.set_page_config(page_title="熊貓迷因產生器", page_icon="🐼")
st.title("🐼 嘲諷熊貓迷因產生器 (SDXL 強力版)")
st.write("輸入一句話，讓 AI 幫你生成專屬的嘲諷熊貓梗圖！")

# 2. 自動下載字型 (修正版：使用 requests，確保能成功下載)
def download_font():
    font_path = "NotoSansTC-Bold.otf"
    if not os.path.exists(font_path):
        with st.spinner("正在下載中文字型..."):
            try:
                url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Bold.otf"
                r = requests.get(url)
                with open(font_path, "wb") as f:
                    f.write(r.content)
                st.success("字型下載完成！")
            except Exception as e:
                st.warning(f"字型下載失敗，將使用預設字體。錯誤：{e}")

download_font()

# 3. 初始化 Hugging Face Client
# 使用 stabilityai/stable-diffusion-xl-base-1.0 (目前最強免費模型)
client = InferenceClient(token=st.secrets["HF_TOKEN"])

# 4. 加字函數 (優化版：強制轉 RGB)
def add_caption(image, text, font_path='NotoSansTC-Bold.otf'):
    # 強制轉為 RGB 模式，避免格式不相容導致破圖
    image = image.convert("RGB")
    
    original_width, original_height = image.size
    temp_draw = ImageDraw.Draw(image)
    
    # 字體大小設定
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
        with st.spinner("AI 正在繪製中 (使用 SDXL 1.0 模型)..."):
            try:
                # 設定 Prompt
                prompt = "close up of a panda head with a funny human man face, smug expression, trolling face, meme style, simple black and white line art, vector art, flat color, white background, looking at viewer"
                negative_prompt = "body, paws, claws, realistic fur, 3d, shading, gradient, grey, fuzzy, blurry, realistic, photo, cute, animal face, sleeping, lying down"
                
                # 呼叫官方 SDK 生圖
                image = client.text_to_image(
                    prompt, 
                    negative_prompt=negative_prompt,
                    model="stabilityai/stable-diffusion-xl-base-1.0"
                )
                
                # 優化：縮小圖片以節省記憶體並避免破圖 (SDXL 原圖 1024x1024 太大了)
                image = image.resize((512, 512))
                
                # 加字
                final_image = add_caption(image, user_text)
                
                # 顯示圖片 (明確指定 output_format 為 PNG)
                st.image(final_image, caption="你的專屬梗圖完成啦！", output_format="PNG")
                
            except Exception as e:
                st.error("生成失敗，請稍後再試。")
                st.write(e)
