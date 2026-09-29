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

# 시인성 최우선 라이트/모던 테마 커스텀 CSS
st.markdown("""
    <style>
        /* 전체 배경 및 기본 폰트 설정 */
        .stApp {
            background-color: #f8fafc;
            color: #1e293b;
        }
        
        /* 상단 여백 확보 및 패딩 조정 */
        .block-container { 
            padding-top: 2rem !important; 
            padding-bottom: 2rem !important; 
        }
        
        /* 타이틀 배너 카드 디자인 (잘림 완벽 방지) */
        .title-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            padding: 1.2rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.2rem;
        }
        .title-card h1 {
            color: #ffffff !important;
            font-size: 1.5rem !important;
            font-weight: 800 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.3 !important;
            white-space: normal !important;
            word-break: keep-all !important;
        }
        .title-card p {
            color: #dbeafe !important;
            font-size: 0.85rem !important;
            margin: 0.3rem 0 0 0 !important;
        }

        /* Sub-caption 안내 문구 스타일 */
        .sub-instruction {
            background-color: #ffffff;
            padding: 0.6rem 1rem;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            font-weight: 600;
            color: #334155;
            font-size: 0.9rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        /* 일반 버튼 스타일링 */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 700 !important;
            transition: all 0.2s ease !important;
            height: 2.6rem !important;
        }

        /* 사이드바 스타일링 */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }

        /* 이미지 컨테이너 카드화 */
        [data-testid="column"] {
            background: #ffffff;
            padding: 0.8rem;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 및 키 카운터 초기화
if "history" not in st.session_state:
    st.session_state.history = []
if "pts" not in st.session_state:
    st.session_state.pts = []
if "coord_key" not in st.session_state:
    st.session_state.coord_key = 0

# 깔끔한 타이틀 배너 출력
st.markdown("""
    <div class="title-card">
        <h1>🔥 타일 열화상 충진율 분석 시스템</h1>
        <p> 열화상 색상 분석 및 정밀 충진율 진단 솔루션</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 이미지 파일 선택")
uploaded_file = st.sidebar.file_uploader("열화상 사진 선택", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    orig_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if orig_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        img_h, img_w = orig_img.shape[:2]
        
        col_main, col_history = st.columns([8, 4])
        
        with col_main:
            st.markdown('<div class="sub-instruction">📌 <b>모서리 4곳 터치 지정:</b> 1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하</div>', unsafe_allow_html=True)
            
            canvas_w = 280
            canvas_h = int(img_h * (canvas_w / img_w))
            
            bg_img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(bg_img_rgb).resize((canvas_w, canvas_h))
            
            # 찍은 좌표 점 및 순서 숫자 그리기 (빨간 원 + 흰색 테두리)
            draw_img = np.array(pil_image).copy()
            for i, p in enumerate(st.session_state.pts):
                cv2.circle(draw_img, (p[0], p[1]), 7, (255, 255, 255), -1)
                cv2.circle(draw_img, (p[0], p[1]), 5, (239, 68, 68), -1)
                cv2.putText(draw_img, str(i+1), (p[0]+9, p[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
                cv2.putText(draw_img, str(i+1), (p[0]+9, p[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("##### 1. 원본 (터치 좌표 지정)")
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
                st.write(f"📍 선택된 좌표: **{len(st.session_state.pts)} / 4**")
                if st.button("🔄 좌표 리셋", use_container_width=True):
                    st.session_state.pts = []
                    st.session_state.coord_key += 1
                    st.rerun()
                    
            with col_btn2:
                run_btn = st.button("🚀 정밀 분석 실행", disabled=(len(st.session_state.pts) != 4), type="primary", use_container_width=True)

            # 분석 실행
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
                
                blurred = cv2.GaussianBlur(warped_img, (5, 5), 0)
                hsv_warped = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
                
                # --- [1. 완전 충진 영역 검출] ---
                # A. 연두색/초록색 영역
                lower_green = np.array([35, 40, 40])
                upper_green = np.array([85, 255, 255])
                mask_green = cv2.inRange(hsv_warped, lower_green, upper_green)
                
                # B. 노란색 영역
                lower_yellow = np.array([15, 40, 100])
                upper_yellow = np.array([34, 255, 255])
                mask_yellow = cv2.inRange(hsv_warped, lower_yellow, upper_yellow)
                
                # C. 흰색 영역
                lower_white = np.array([0, 0, 200])
                upper_white = np.array([180, 80, 255])
                mask_white = cv2.inRange(hsv_warped, lower_white, upper_white)
                
                mask_full = mask_green | mask_yellow | mask_white
                
                # --- [2. 경계/부분 충진 영역 검출] ---
                # A. 주황색 영역
                lower_orange = np.array([10, 50, 50])
                upper_orange = np.array([14, 255, 255])
                mask_orange = cv2.inRange(hsv_warped, lower_orange, upper_orange)
                
                # B. 빨간색 영역
                lower_red1 = np.array([0, 50, 50])
                upper_red1 = np.array([9, 255, 255])
                lower_red2 = np.array([145, 50, 50])
                upper_red2 = np.array([180, 255, 255])
                mask_red = cv2.inRange(hsv_warped, lower_red1, upper_red1) | cv2.inRange(hsv_warped, lower_red2, upper_red2)
                
                mask_partial = mask_red | mask_orange
                
                kernel = np.ones((5, 5), np.uint8)
                mask_full = cv2.morphologyEx(mask_full, cv2.MORPH_CLOSE, kernel)
                mask_partial = cv2.morphologyEx(mask_partial, cv2.MORPH_CLOSE, kernel)
                
                total_pixels = TARGET_W * TARGET_H
                full_pixels = np.sum(mask_full == 255)
                partial_pixels = np.sum(mask_partial == 255)
                
                WEIGHT_FULL = 1.0
                WEIGHT_PARTIAL = 0.45
                weighted_filled_pixels = (full_pixels * WEIGHT_FULL) + (partial_pixels * WEIGHT_PARTIAL)
                final_ratio = (weighted_filled_pixels / total_pixels) * 100
                
                display_mask = np.ones_like(warped_img) * 255
                display_mask[mask_partial == 255] = [0, 0, 255]     # BGR: 빨간색 (경계/부분)
                display_mask[mask_full == 255] = [0, 255, 0]        # BGR: 초록/연두색 (완전충진)
                
                with col2:
                    st.markdown("##### 2. 투시 보정 정면")
                    st.image(cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB), use_container_width=True)
                
                with col3:
                    st.markdown("##### 3. 충진 진단 마스크")
                    st.image(cv2.cvtColor(display_mask, cv2.COLOR_BGR2RGB), use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if final_ratio >= 80.0:
                    st.success(f"🎉 **[기준 80% 만족 (합격)]** 최종 충진율: **{final_ratio:.2f}%**")
                else:
                    st.error(f"🚨 **[기준 80% 미달 (불합격)]** 최종 충진율: **{final_ratio:.2f}%**")
                    st.markdown("""
                    **[현장 조치 지침]**
                    * **공사 중:** 재시공 필요, 타일 즉시 철거 후 개량압착공법으로 재시공
                    * **공사 완료 후:** 보강 필요, 줄눈 타공 후 에폭시 수지 고압 주입 보강
                    """)

                now = datetime.now()
                new_record = {
                    "사진 이름": uploaded_file.name,
                    "시간": now.strftime("%H:%M:%S"),
                    "충진율": f"{final_ratio:.2f}%"
                }
                
                if not st.session_state.history or st.session_state.history[0]["사진 이름"] != uploaded_file.name:
                    st.session_state.history.insert(0, new_record)

            else:
                with col2:
                    st.markdown("##### 2. 투시 보정 정면")
                    st.info("4곳 터치 후 분석 버튼 클릭")
                with col3:
                    st.markdown("##### 3. 충진 진단 마스크")
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
