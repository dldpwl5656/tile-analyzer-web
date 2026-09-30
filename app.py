import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(
    page_title="LH 열화상 타일 정밀 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        html, body, [class*="css"] { font-size: 1.2rem !important; }
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
        h3, .stSubheader { font-size: 1.6rem !important; font-weight: 800 !important; }
        [data-testid="sidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
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
        <p>스마트 클러스터링 및 명암 기반 적응형 진단 솔루션</p>
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
                # 📌 [스마트 클러스터링 기반 적응형 진단 알고리즘]
                # =========================================================
                gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
                hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
                
                # 1. 배경(초록/어두운 바닥)과 열화상 신호 분리를 위한 오직 밝기/채도 분석
                # 열화상에서 온도가 높은 부위(충진부)는 밝기(Value)와 특정 색상 채도가 높거나 뚜렷한 특징을 가짐.
                # Otsu 이진화와 채도 분석을 결합하여 자동으로 유효 열화상 영역 추출
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                
                # 채도(Saturation) 채널 활용 (열화상 고온 부위는 채도가 높거나 명도가 뚜렷함)
                s_chan = hsv[:, :, 1]
                v_chan = hsv[:, :, 2]
                
                # 다중 피처 결합 스코어 (명도 + 채도 조합)
                thermal_map = cv2.addWeighted(v_chan, 0.5, s_chan, 0.5, 0)
                
                # Otsu 알고리즘을 적용해 이미지 자체의 특성에 맞춰 자동 임계값 설정 (사진마다 다른 스케일에 대응)
                _, thresh_otsu = cv2.threshold(thermal_map, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # 초록색 배경(공극) 성분 강한 픽셀 정밀 필터링
                b_c, g_c, r_c = cv2.split(warped_img)
                is_green_bg = (g_c.astype(np.int16) > r_c.astype(np.int16) + 15) & (g_c.astype(np.int16) > 100)
                
                # 최종 충진 마스크 생성 (기본 오츠 영역에서 명백한 초록 배경 제외)
                full_fill_mask = thresh_otsu.copy()
                full_fill_mask[is_green_bg] = 0

                # 2. 노이즈 제거 및 빈 곳 메우기 (모폴로지 연산)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                full_fill_mask = cv2.morphologyEx(full_fill_mask, cv2.MORPH_CLOSE, kernel)
                full_fill_mask = cv2.morphologyEx(full_fill_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

                # 3. 최종 충진율 계산
                total_pixels = TARGET_W * TARGET_H
                p_full = np.count_nonzero(full_fill_mask == 255)
                
                # 약간의 경계 가중치를 부여하여 자연스러운 채점 보정 (전체의 85% 반영 + 경계 부근 스무딩)
                final_ratio = (p_full / total_pixels) * 100.0

                # 4. 진단 마스크 시각화 (완전충진: 흰색 255, 공극: 검은색 0)
                display_mask_bgr = cv2.cvtColor(full_fill_mask, cv2.COLOR_GRAY2BGR)

                with col2:
                    st.markdown("##### 2. 정면 보정")
                    st.image(warped_rgb, use_container_width=True)
                
                with col3:
                    st.markdown("##### 3. 진단 마스크 (BW)")
                    st.image(display_mask_bgr, use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if final_ratio >= 80.0:
                    st.success(f"🎉 **[기준 80% 만족 (합격)]** 최종 충진율: **{final_ratio:.2f}%** (충진 영역 감지율)")
                else:
                    st.error(f"🚨 **[기준 80% 미달 (불합격)]** 최종 충진율: **{final_ratio:.2f}%** (충진 영역 감지율)")

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
