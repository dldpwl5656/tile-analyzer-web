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
        <h1>🔥 열화상 타일 정밀 충진율 분석 시스템 (K-Means Auto)</h1>
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
            TARGET_W = 600
            TARGET_H = 300

            clicked_pts = []
            x_scale = img_w / canvas_w
            y_scale = img_h / canvas_h
            for pt in st.session_state.pts:
                clicked_pts.append([int(pt[0] * x_scale), int(pt[1] * y_scale)])

            src_pts = np.float32(clicked_pts)
            dst_pts = np.float32([[0, 0], [TARGET_W, 0], [TARGET_W, TARGET_H], [0, TARGET_H]])
            
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_img = cv2.warpPerspective(orig_img, matrix, (TARGET_W, TARGET_H))
            warped_rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)
            
            # ---------------------------------------------------------
            # 🔬 완전 자동 K-Means 군집화 기반 정밀 이진화 (수동 조절 X)
            # ---------------------------------------------------------
            # LAB B-channel 변환 및 필터링
            lab = cv2.cvtColor(warped_img, cv2.COLOR_BGR2LAB)
            _, _, b_channel = cv2.split(lab)
            filtered = cv2.bilateralFilter(b_channel, 9, 75, 75)
            
            # K-Means 클러스터링 (k=2: 충진 / 미충진 자동 구분)
            pixel_vals = filtered.reshape((-1, 1)).astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, labels, centers = cv2.kmeans(pixel_vals, 2, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # 더 높은 밝기 값을 가진 군집을 충진(1) 영역으로 설정
            if centers[0] > centers[1]:
                filled_cluster = 0
            else:
                filled_cluster = 1
                
            binary_mask = (labels == filled_cluster).astype(np.uint8) * 255
            binary_mask = binary_mask.reshape((TARGET_H, TARGET_W))
            
            # 노이즈 제거
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_close)
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_open)
            
            total_pixels = TARGET_W * TARGET_H
            filled_pixels = int(np.sum(binary_mask == 255))
            void_pixels = int(total_pixels - filled_pixels)

            final_ratio = (filled_pixels / total_pixels) * 100.0

            binary_display = cv2.cvtColor(binary_mask, cv2.COLOR_GRAY2RGB)

            with col2:
                st.markdown('<div class="panel-header">2. 정면 보정 (RGB)</div>', unsafe_allow_html=True)
                st.image(warped_rgb, use_container_width=True)
            
            with col3:
                st.markdown('<div class="panel-header">3. 정밀 이진화 마스크</div>', unsafe_allow_html=True)
                st.image(binary_display, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ---------------------------------------------------------
            # 📊 하단 결과 출력
            # ---------------------------------------------------------
            if final_ratio >= 80.0:
                st.success(f"🎉 **[기준 80% 만족 (합격)]** 최종 정밀 이진화 충진율: **{final_ratio:.2f}%**")
            else:
                st.error(f"🚨 **[기준 80% 미달 (불합격)]** 최종 정밀 이진화 충진율: **{final_ratio:.2f}%**")
                st.markdown("""
                **[현장 조치 지침]**
                * **공사 중:** 재시공 필요, 타일 즉시 철거 후 개량압착공법으로 재시공
                * **공사 완료 후:** 보강 필요, 줄눈 타공 후 에폭시 수지 고압 주입 보강
                """)

            st.markdown(f"""
            <div class="info-card-box">
                🔬 <b>이진화 분석 알고리즘:</b> Automatic K-Means Color Segmentation (LAB B-Channel)<br>
                💡 <b>픽셀 개수:</b> 충진 영역(흰색): <b>{filled_pixels:,} px ({final_ratio:.1f}%)</b> | 미충진/공복(검은색): <b>{void_pixels:,} px ({100-final_ratio:.1f}%)</b>
            </div>
            """, unsafe_allow_html=True)

            now = datetime.now()
            new_record = {
                "사진 이름": uploaded_file.name,
                "시간": now.strftime("%H:%M:%S"),
                "최종 충진율": f"{final_ratio:.2f}%",
                "충진 픽셀": f"{filled_pixels:,} px",
                "공복 픽셀": f"{void_pixels:,} px"
            }
            
            if not st.session_state.history or st.session_state.history[0]["시간"] != new_record["시간"]:
                st.session_state.history.insert(0, new_record)

        else:
            with col2:
                st.markdown('<div class="panel-header">2. 정면 보정 (RGB)</div>', unsafe_allow_html=True)
                st.info("4곳 터치 후 분석 버튼 클릭")
            with col3:
                st.markdown('<div class="panel-header">3. 정밀 이진화 마스크</div>', unsafe_allow_html=True)
                st.info("분석 대기 중")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📋 **분석 이력 기록 열기 / 닫기**", expanded=False):
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                st.dataframe(df, use_container_width=True)
                
                col_exp1, col_exp2 = st.columns([1, 1])
                with col_exp1:
                    csv_data = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("💾 CSV 다운로드", data=csv_data, file_name="tile_history.csv", mime="text/csv", use_container_width=True)
                with col_exp2:
                    if st.button("🧹 이력 초기화", use_container_width=True):
                        st.session_state.history = []
                        st.session_state.pts = []
                        st.session_state.coord_key += 1
                        st.rerun()
            else:
                st.caption("저장된 이력이 없습니다.")

else:
    st.session_state.pts = []
    st.info("👈 사이드바에서 열화상 사진을 업로드하세요.")
