import streamlit as st
import torch
from diffusers import StableDiffusionPipeline, UniPCMultistepScheduler
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# 1. 設定頁面配置
st.set_page_config(page_title="熊貓迷因產生器", page_icon="🐼")
st.title("🐼 嘲諷熊貓迷因產生器")
st.write("輸入一句話，讓 AI 幫你生成專屬的嘲諷熊貓梗圖！")

# 2. 自動下載字型 (如果找不到檔案的話)
# 這樣部署到雲端時才不會因為缺字型而報錯
def download_font():
    if not os.path.exists("NotoSansTC-Bold.otf"):
        st.info("正在下載中文字型，請稍候...")
        os.system("wget -O NotoSansTC-Bold.otf https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Bold.otf")
        st.success("字型下載完成！")

download_font()

# 3. 載入模型 (使用 @st.cache_resource 讓它只載入一次，不用每次生圖都重跑)
@st.cache_resource
def load_model():
    model_id = "Lykon/DreamShaper" # 或者你選擇的 runwayml/stable-diffusion-v1-5
    
    # 根據你的環境自動選擇 CPU 或 GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id, 
        torch_dtype=dtype,
        # use_safetensors=True # DreamShaper 如果報錯就註解掉這行
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to(device)
    return pipe

# 顯示載入狀態
with st.spinner("正在啟動 AI 繪圖引擎... (第一次啟動會比較久)"):
    pipe = load_model()

# 4. 定義加字函數 (新版：下方增加留白區域)
def add_caption(image, text, font_path='NotoSansTC-Bold.otf'):
    # 取得原始圖片尺寸
    original_width, original_height = image.size
    
    # 準備一個暫時的畫筆來計算文字大小
    temp_draw = ImageDraw.Draw(image)
    
    # 字體大小設定
    font_size = int(original_width / 10)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        # 如果真的沒字型，用預設的(不支援中文，但至少不會報錯)
        font = ImageFont.load_default()
    
    # 自動換行 (這裡設定一行約 10 個字，可以依需求調整)
    lines = textwrap.wrap(text, width=10)
    
    # --- 計算需要的白色區域高度 ---
    if lines:
        # 計算單行文字高度
        bbox = temp_draw.textbbox((0, 0), lines[0], font=font)
        line_height = bbox[3] - bbox[1]
        # 總高度 = (行高 + 行距) * 行數 + 上下邊距
        text_area_height = (line_height + 10) * len(lines) + 20
    else:
        # 如果沒輸入文字，就不留白
        text_area_height = 0

    # --- 創造新畫布並組合 ---
    # 新高度 = 原圖高度 + 文字區高度
    new_height = original_height + text_area_height
    # 創造一張全白的新圖
    final_image = Image.new('RGB', (original_width, new_height), color=(255, 255, 255))
    # 把原本的熊貓圖貼在最上面 (座標 0,0)
    final_image.paste(image, (0, 0))
    
    # --- 開始寫字 ---
    draw = ImageDraw.Draw(final_image)
    
    # 文字起始 Y 座標：從原圖下方邊緣再往下個 10px 開始寫
    y_text = original_height + 10 

    for line in lines:
        # 計算寬度以置中
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x_text = (original_width - line_width) / 2
        
        # 因為背景是全白，不需要描邊了，直接寫黑字
        draw.text((x_text, y_text), line, font=font, fill=(0, 0, 0))
        
        # 往下移動到下一行
        y_text += line_height + 10

    return final_image

# 5. 使用者介面 (UI)
# 這裡就是把「寫死」改成「自訂」的關鍵！
user_text = st.text_input("請輸入梗圖文字：", "大家不要出聲\n讓他一個人尷尬")

if st.button("生成梗圖"):
    if not user_text:
        st.warning("請先輸入文字喔！")
    else:
        with st.spinner("AI 正在繪製嘲諷熊貓中..."):
            # 設定 Prompt (你之前調教好的)
            prompt = "close up of a panda head with a funny human man face, smug expression, trolling face, meme style, simple black and white line art, vector art, flat color, white background, looking at viewer"
            negative_prompt = "body, paws, claws, realistic fur, 3d, shading, gradient, grey, fuzzy, blurry, realistic, photo, cute, animal face, sleeping, lying down"
            
            # 生圖
            image = pipe(
                prompt=prompt, 
                negative_prompt=negative_prompt,
                height=512, 
                width=512, 
                num_inference_steps=20,
                guidance_scale=7.5
            ).images[0]
            
            # 加字
            final_image = add_caption(image, user_text)
            
            # 顯示
            st.image(final_image, caption="你的專屬梗圖完成啦！")
