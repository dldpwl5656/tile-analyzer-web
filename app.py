import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(
    page_title="열화상 타일 정밀 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 🎨 레이아웃 CSS Custom
# ---------------------------------------------------------
st.markdown("""
    <style>
        html, body, [class*="css"] { font-size: 1.1rem !important; }
        .stApp { background-color: #f8fafc; color: #0f172a; }
        .block-container { 
            padding-top: 1.5rem !important; 
            padding-bottom: 2rem !important; 
            max-width: 96% !important; 
        }
        
        .title-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
            padding: 1.2rem 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
            margin-bottom: 1.2rem;
        }
        .title-card h1 { color: #ffffff !important; font-size: 2.0rem !important; font-weight: 800 !important; margin: 0 !important; }
        .title-card p { color: #dbeafe !important; font-size: 1.05rem !important; margin-top: 0.3rem !important; margin-bottom: 0 !important; }
        
        .sub-instruction {
            background-color: #ffffff;
            padding: 0.8rem 1.2rem;
            border-radius: 8px;
            border-left: 5px solid #2563eb;
            font-weight: 700;
            color: #1e293b;
            font-size: 1.15rem !important;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        
        .panel-header {
            font-size: 1.25rem !important;
            font-weight: 800 !important;
            color: #1e293b !important;
            margin-bottom: 0.8rem !important;
            min-height: 2rem;
            display: flex;
            align-items: center;
        }
        
        [data-testid="column"] { 
            background: #ffffff; 
            padding: 1.2rem; 
            border-radius: 12px; 
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
            display: flex;
            flex-direction: column;
        }
        
        .stButton>button {
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            height: 2.8rem !important;
        }

        .info-card-box {
            background-color: #f1f5f9;
            padding: 0.8rem 1rem;
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            margin-top: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "pts" not in st.session_state:
    st.session_state.pts = []
if "coord_key" not in st.session_state:
    st.session_state.coord_key = 0

st.markdown("""
    <div class="title-card">
        <h1>🔥 열화상 타일 정밀 충진율 분석 시스템 (정밀 이진화)</h1>
        <p>열화상 이미지를 이용한 타일 뒷채움 비파괴검사</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 📌 사이드바
# ---------------------------------------------------------
st.sidebar.header("📁 이미지 업로드")
uploaded_file = st.sidebar.file_uploader("열화상 사진 선택", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    full_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if full_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        orig_img = full_img
        img_h, img_w = orig_img.shape[:2]
        
        st.markdown('<div class="sub-instruction">📌 <b>RGB 타일 영역 4개 모서리 클릭:</b> 1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하</div>', unsafe_allow_html=True)
        
        MAX_W = 400
        if img_w > MAX_W:
            canvas_w = MAX_W
            canvas_h = int(img_h * (MAX_W / img_w))
        else:
            canvas_w = img_w
            canvas_h = img_h
        
        bg_img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(bg_img_rgb).resize((canvas_w, canvas_h))
        
        draw_img = np.array(pil_image).copy()
        for i, p in enumerate(st.session_state.pts):
            cv2.circle(draw_img, (p[0], p[1]), 8, (255, 255, 255), -1)
            cv2.circle(draw_img, (p[0], p[1]), 6, (239, 68, 68), -1)
            cv2.putText(draw_img, str(i+1), (p[0]+12, p[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(draw_img, str(i+1), (p[0]+12, p[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown('<div class="panel-header">1. RGB 타일 (영역 지정)</div>', unsafe_allow_html=True)
            value = streamlit_image_coordinates(
                Image.fromarray(draw_img),
                key=f"mobile_coord_{st.session_state.coord_key}"
            )

            if value is not None:
                point = [value["x"], value["y"]]
                if len(st.session_state.pts) < 4 and point not in st.session_state.pts:
                    st.session_state.pts.append(point)
                    st.rerun()

            st.write(f"📍 좌표 선택: **{len(st.session_state.pts)} / 4**")
            
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("🔄 리셋", use_container_width=True):
                    st.session_state.pts = []
                    st.session_state.coord_key += 1
                    st.rerun()
                    
            with col_btn2:
                run_btn = st.button("🚀 분석 실행", disabled=(len(st.session_state.pts) != 4), type="primary", use_container_width=True)

        if run_btn and len(st.session_state.pts) == 4:
            clicked_pts = []
            x_scale = img_w / canvas_w
            y_scale = img_h / canvas_h
            for pt in st.session_state.pts:
                clicked_pts.append([int(pt[0] * x_scale), int(pt[1] * y_scale)])

            src_pts = np.float32(clicked_pts)
            TARGET_W, TARGET_H = 600
