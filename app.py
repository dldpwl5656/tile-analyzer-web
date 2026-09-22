import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# 1. 페이지 기본 레이아웃 및 테마 설정
st.set_page_config(
    page_title="LH 열화상 타일 정밀 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS: 모바일 터치 이벤트 최적화 및 캔버스 스크롤 차단 (CSS touch-action 처리)
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; }
        .stButton>button { width: 100%; margin-top: 5px; }
        /* 모바일 터치 클릭 지원용 CSS */
        canvas { touch-action: none !important; }
    </style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🔥 LH 기준 열화상 타일 정밀 충진율 분석 시스템 v1.0")

# 사이드바
st.sidebar.header("📁 이미지 파일 선택")
uploaded_file = st.sidebar.file_uploader("열화상 사진 선택", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    orig_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if orig_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        img_h, img_w = orig_img.shape[:2]
        
        # 메인 분석구역과 오른쪽 이력표 분할
        col_main, col_history = st.columns([8, 4])
        
        with col_main:
            st.caption("📌 **모서리 4곳 터치:** 1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하")
            
            # 모바일 화면에 잘 맞도록 폭을 260px로 설정
            canvas_w = 260
            canvas_h = int(img_h * (canvas_w / img_w))
            
            bg_img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(bg_img_rgb)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**1. 원본 (터치하여 선택)**")
                canvas_result = st_canvas(
                    fill_color="rgba(239, 68, 68, 0.8)",
                    stroke_width=2,
                    stroke_color="#ef4444",
                    background_image=pil_image,
                    update_streamlit=True,
                    height=canvas_h,
                    width=canvas_w,
                    drawing_mode="point",
                    point_display_radius=8,  # 모바일 손가락 터치를 고려해 포인트 크기 확대
                    key="canvas_mobile_opt",
                )

            # 클릭/터치 좌표 수집
            clicked_pts = []
            if canvas_result.json_data is not None and "objects" in canvas_result.json_data:
                for obj in canvas_result.json_data["objects"]:
                    x_scale = img_w / canvas_w
                    y_scale = img_h / canvas_h
                    orig_x = int(obj["left"] * x_scale)
                    orig_y = int(obj["top"] * y_scale)
                    clicked_pts.append([orig_x, orig_y])

            # 좌표 선택 현황 및 버튼
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                st.write(f"📍 좌표 선택: **{len(clicked_pts)} / 4**")
            with col_btn2:
                run_btn = st.button("🚀 정밀 분석 실행", disabled=(len(clicked_pts) != 4))

            # 분석 실행
            if run_btn and len(clicked_pts) == 4:
                src_pts = np.float32(clicked_pts)
                TARGET_W, TARGET_H = 600, 300
                dst_pts = np.float32([[0, 0], [TARGET_W, 0], [TARGET_W, TARGET_H], [0, TARGET_H]])
                
                matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
                warped_img = cv2.warpPerspective(orig_img, matrix, (TARGET_W, TARGET_H))
                
                blurred = cv2.GaussianBlur(warped_img, (5, 5), 0)
                hsv_warped = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
                
                lower_red1 = np.array([0, 50, 50])
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([145, 50, 50])
                upper_red2 = np.array([180, 255, 255])
                mask_red = cv2.inRange(hsv_warped, lower_red1, upper_red1) | cv2.inRange(hsv_warped, lower_red2, upper_red2)
                
                lower_white = np.array([0, 0, 200])
                upper_white = np.array([180, 80, 255])
                mask_white = cv2.inRange(hsv_warped, lower_white, upper_white)
                
                mask_full = cv2.bitwise_or(mask_red, mask_white)
                
                lower_yellow = np.array([11, 50, 100])
                upper_yellow = np.array([35, 255, 255])
                mask_partial = cv2.inRange(hsv_warped, lower_yellow, upper_yellow)
                
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
                display_mask[mask_partial == 255] = [0, 255, 255]
                display_mask[mask_full == 255] = [0, 0, 255]
                
                with col2:
                    st.markdown("**2. 투시 보정 정면**")
                    st.image(cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB), use_container_width=True)
                
                with col3:
                    st.markdown("**3. 충진 진단 마스크**")
                    st.image(cv2.cvtColor(display_mask, cv2.COLOR_BGR2RGB), use_container_width=True)

                if final_ratio >= 80.0:
                    st.success(f"🎉 **[LH 기준 만족 (합격)]** 최종 충진율: **{final_ratio:.2f}%**")
                else:
                    st.error(f"🚨 **[LH 기준 미달 (불합격)]** 최종 충진율: **{final_ratio:.2f}%**")
                    st.markdown("""
                    **[현장 조치 지침]**
                    * **공사 중:** 타일 즉시 철거 후 개량압착공법으로 재시공
                    * **공사 완료 후:** 줄눈 타공 후 에폭시 수지 고압 주입 보강
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
                    st.markdown("**2. 투시 보정 정면**")
                    st.info("4곳 터치 후 버튼 클릭")
                with col3:
                    st.markdown("**3. 충진 진단 마스크**")
                    st.info("분석 대기 중")

        # 우측 분석 이력
        with col_history:
            st.subheader("📋 분석 이력")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                st.dataframe(df, use_container_width=True)
                
                csv_data = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("💾 CSV 다운로드", data=csv_data, file_name="tile_history.csv", mime="text/csv")
                if st.button("🧹 이력 초기화"):
                    st.session_state.history = []
                    st.rerun()
            else:
                st.caption("기록 없음")

else:
    st.info("👈 사이드바에서 열화상 사진을 업로드하세요.")
