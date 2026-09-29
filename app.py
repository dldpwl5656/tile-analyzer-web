import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

# 페이지 레이아웃 및 브라우저 탭 설정
st.set_page_config(
    page_title="LH 열화상 타일 정밀 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일링
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-size: 1.2rem !important;
        }
        .stApp { background-color: #f8fafc; color: #0f172a; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
        .title-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
            padding: 1.5rem 2rem;
            border-radius: 14px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
            margin-bottom: 1.5rem;
        }
        .title-card h1 { color: #ffffff !important; font-size: 2.2rem !important; font-weight: 800 !important; margin: 0 !important; }
        .title-card p { color: #dbeafe !important; font-size: 1.15rem !important; margin-top: 0.5rem !important; }
        .sub-instruction {
            background-color: #ffffff;
            padding: 1rem 1.2rem;
            border-radius: 10px;
            border-left: 6px solid #2563eb;
            font-weight: 700;
            color: #1e293b;
            font-size: 1.3rem !important;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stButton>button {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            padding: 0.7rem 1.5rem !important;
            border-radius: 8px !important;
        }
        h5 {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            margin-bottom: 0.8rem !important;
        }
        h3, .stSubheader {
            font-size: 1.6rem !important;
            font-weight: 800 !important;
        }
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
        [data-testid="column"] { background: #ffffff; padding: 1.2rem; border-radius: 12px; border: 1px solid #cbd5e1; }
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
        <h1>🔥 열화상 타일 정밀 충진율 분석 시스템</h1>
        <p>열화상 정밀 이진화 채널 분석 및 충진율 진단 솔루션</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 이미지 파일 선택")
uploaded_file = st.sidebar.file_uploader("열화상 사진 선택", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    full_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if full_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        full_h, full_w = full_img.shape[:2]
        
        # 통이미지 형태 대응 (상단 RGB 영역 추출)
        if full_h > full_w:
            orig_img = full_img[0:int(full_h * 0.33), :]
        else:
            orig_img = full_img
            
        img_h, img_w = orig_img.shape[:2]
        
        col_main, col_history = st.columns([8, 4])
        
        with col_main:
            st.markdown('<div class="sub-instruction">📌 <b>RGB 타일 영역 4개 모서리 클릭:</b> 1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하</div>', unsafe_allow_html=True)
            
            canvas_w = 360
            canvas_h = int(img_h * (canvas_w / img_w))
            
            bg_img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(bg_img_rgb).resize((canvas_w, canvas_h))
            
            draw_img = np.array(pil_image).copy()
            for i, p in enumerate(st.session_state.pts):
                cv2.circle(draw_img, (p[0], p[1]), 7, (255, 255, 255), -1)
                cv2.circle(draw_img, (p[0], p[1]), 5, (239, 68, 68), -1)
                cv2.putText(draw_img, str(i+1), (p[0]+10, p[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                cv2.putText(draw_img, str(i+1), (p[0]+10, p[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("##### 1. RGB 타일 (영역 지정)")
                value = streamlit_image_coordinates(
                    Image.fromarray(draw_img),
                    key=f"mobile_coord_{st.session_state.coord_key}"
                )

                if value is not None:
                    point = [value["x"], value["y"]]
                    if len(st.session_state.pts) < 4 and point not in st.session_state.pts:
                        st.session_state.pts.append(point)
                        st.rerun()

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                st.write(f"📍 좌표 선택: **{len(st.session_state.pts)} / 4**")
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
                TARGET_W, TARGET_H = 600, 300
                dst_pts = np.float32([[0, 0], [TARGET_W, 0], [TARGET_W, TARGET_H], [0, TARGET_H]])
                
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped_img = cv2.warpPerspective(orig_img, matrix, (TARGET_W, TARGET_H))
                warped_rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)
                
                # =========================================================
                # 📌 [열화상 HSV 채널 정밀 분할 및 역전 방지 보정 알고리즘]
                # =========================================================
                hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
                
                # 1. 충진(고온) 영역: 빨강, 주황, 노랑 계열 (Hue: 0~45 및 140~180)
                # 노란색/연두색 경계면 포함 정밀 임계값 설정
                lower_fill1 = np.array([0, 50, 80])
                upper_fill1 = np.array([42, 255, 255])
                
                lower_fill2 = np.array([140, 50, 80])
                upper_fill2 = np.array([180, 255, 255])
                
                mask_fill1 = cv2.inRange(hsv, lower_fill1, upper_fill1)
                mask_fill2 = cv2.inRange(hsv, lower_fill2, upper_fill2)
                mask_filled = cv2.bitwise_or(mask_fill1, mask_fill2)
                
                # 2. 비충진(저온/공극) 영역: 초록~파랑 계열 (Hue: 43~135)
                lower_void = np.array([43, 40, 40])
                upper_void = np.array([135, 255, 255])
                mask_void = cv2.inRange(hsv, lower_void, upper_void)
                
                # 노이즈 제거
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                mask_filled = cv2.morphologyEx(mask_filled, cv2.MORPH_OPEN, kernel)
                mask_void = cv2.morphologyEx(mask_void, cv2.MORPH_OPEN, kernel)
                
                count_filled = np.count_nonzero(mask_filled == 255)
                count_void = np.count_nonzero(mask_void == 255)
                total_valid = count_filled + count_void
                
                # 유효 열화상 영역 내 충진 비율 계산
                if total_valid > 0:
                    final_ratio = (count_filled / total_valid) * 100.0
                else:
                    total_pixels = TARGET_W * TARGET_H
                    final_ratio = (count_filled / total_pixels) * 100.0

                display_mask = cv2.cvtColor(mask_filled, cv2.COLOR_GRAY2BGR)

                with col2:
                    st.markdown("##### 2. 정면 보정")
                    st.image(warped_rgb, use_container_width=True)
                
                with col3:
                    st.markdown("##### 3. 진단 마스크 (BW)")
                    st.image(display_mask, use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if final_ratio >= 80.0:
                    st.success(f"🎉 **[기준 80% 만족 (합격)]** 최종 충진율: **{final_ratio:.2f}%**")
                else:
                    st.error(f"🚨 **[기준 80% 미달 (불합격)]** 최종 충진율: **{final_ratio:.2f}%**")

                now = datetime.now()
                new_record = {
                    "사진 이름": uploaded_file.name,
                    "시간": now.strftime("%H:%M:%S"),
                    "충진율": f"{final_ratio:.2f}%"
                }
                
                if not st.session_state.history or st.session_state.history[0]["시간"] != new_record["시간"]:
                    st.session_state.history.insert(0, new_record)

            else:
                with col2:
                    st.markdown("##### 2. 정면 보정")
                    st.info("4곳 터치 후 분석 버튼 클릭")
                with col3:
                    st.markdown("##### 3. 진단 마스크")
                    st.info("분석 대기 중")

        with col_history:
            st.subheader("📋 분석 이력")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                st.dataframe(df, use_container_width=True)
                
                csv_data = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("💾 CSV 다운로드", data=csv_data, file_name="tile_history.csv", mime="text/csv", use_container_width=True)
                if st.button("🧹 이력 초기화", use_container_width=True):
                    st.session_state.history = []
                    st.session_state.pts = []
                    st.session_state.coord_key += 1
                    st.rerun()
            else:
                st.caption("기록 없음")

else:
    st.session_state.pts = []
    st.info("👈 사이드바에서 열화상 사진을 업로드하세요.")
