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

# 커스텀 CSS
st.markdown("""
    <style>
        html, body, [class*="css"] { font-size: 1.2rem !important; }
        .stApp { background-color: #f8fafc; color: #0f172a; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 95% !important; }
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
        <p>고온/충진 스펙트럼 정밀 보정 및 색상 범주 기반 분석 솔루션</p>
    </div>
""", unsafe_allow_html=True)

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
            
            # ---------------------------------------------------------
            # 🔬 고온/충진 스펙트럼 정밀 보정 (붉은색/주황색/노란색 영역 전면 추출)
            # ---------------------------------------------------------
            hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
            
            # 1. 완전 충진 영역 (붉은색 ~ 주황색 ~ 노란색 전체 스펙트럼 통합)
            # 붉은색은 HSV에서 0~10 및 170~180 양쪽에 걸쳐 있으므로 모두 포괄
            mask_red1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([12, 255, 255]))
            mask_red2 = cv2.inRange(hsv, np.array([168, 50, 50]), np.array([180, 255, 255]))
            mask_orange_yellow = cv2.inRange(hsv, np.array([13, 50, 50]), np.array([35, 255, 255]))
            
            mask_full_fill = cv2.bitwise_or(mask_red1, mask_red2)
            mask_full_fill = cv2.bitwise_or(mask_full_fill, mask_orange_yellow)

            # 2. 부분 충진 영역 (연한 노랑 ~ 연한 초록 중간 전이대)
            mask_mid_fill = cv2.inRange(hsv, np.array([36, 40, 40]), np.array([65, 255, 255]))

            # 중복 영역 제거 (고온 영역 우선)
            mask_mid_fill = cv2.bitwise_and(mask_mid_fill, cv2.bitwise_not(mask_full_fill))

            # 모폴로지 연산으로 노이즈 정제
            kernel = np.ones((3, 3), np.uint8)
            mask_full_fill = cv2.morphologyEx(mask_full_fill, cv2.MORPH_OPEN, kernel)
            mask_mid_fill = cv2.morphologyEx(mask_mid_fill, cv2.MORPH_OPEN, kernel)

            # 진단 마스크 생성 (완전충진: 흰색(255), 부분충진: 회색(128), 미충진: 검은색(0))
            display_mask_gray = np.zeros((TARGET_H, TARGET_W), dtype=np.uint8)
            display_mask_gray[mask_mid_fill == 255] = 128  # 회색 (부분 충진 - 70%)
            display_mask_gray[mask_full_fill == 255] = 255 # 흰색 (완전 충진 - 100%)

            full_pixels = np.sum(mask_full_fill == 255)
            mid_pixels = np.sum(mask_mid_fill == 255)
            total_pixels = TARGET_W * TARGET_H

            full_pct = (full_pixels / total_pixels) * 100.0
            mid_pct = (mid_pixels / total_pixels) * 100.0

            # 최종 가중치 충진율 산출 (완전충진 100%, 부분충진 70%)
            final_ratio = min(full_pct + (mid_pct * 0.70), 100.0)

            with col2:
                st.markdown("##### 2. 정면 보정")
                st.image(warped_rgb, use_container_width=True)
            
            with col3:
                st.markdown("##### 3. 진단 마스크 (Grayscale)")
                st.image(display_mask_gray, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if final_ratio >= 80.0:
                st.success(f"🎉 **[기준 80% 만족 (합격)]** 최종 가중 충진율: **{final_ratio:.2f}%**")
            else:
                st.error(f"🚨 **[기준 80% 미달 (불합격)]** 최종 가중 충진율: **{final_ratio:.2f}%**")
                st.markdown("""
                **[현장 조치 지침]**
                * **공사 중:** 재시공 필요, 타일 즉시 철거 후 개량압착공법으로 재시공
                * **공사 완료 후:** 보강 필요, 줄눈 타공 후 에폭시 수지 고압 주입 보강
                """)

            saved_title = uploaded_file.name

            now = datetime.now()
            new_record = {
                "사진 이름": saved_title,
                "날짜시간": now.strftime("%Y-%m-%d %H:%M:%S"),
                "최종 충진율": f"{final_ratio:.2f}%",
                "warped_img": warped_rgb,
                "mask_img": display_mask_gray
            }
            
            if not st.session_state.history or st.session_state.history[0].get("날짜시간") != new_record["날짜시간"]:
                st.session_state.history.insert(0, new_record)

        else:
            with col2:
                st.markdown("##### 2. 정면 보정")
                st.info("4곳 터치 후 분석 버튼 클릭")
            with col3:
                st.markdown("##### 3. 진단 마스크")
                st.info("분석 대기 중")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📋 **분석 이력 기록 열기 / 닫기**", expanded=False):
            if st.session_state.history:
                df_display = pd.DataFrame([{k: v for k, v in item.items() if k not in ["warped_img", "mask_img"]} for item in st.session_state.history])
                st.dataframe(df_display, use_container_width=True)
                
                st.markdown("🔍 **이력 상세 보기 (아래에서 기록을 선택하세요)**")
                selected_idx = st.selectbox(
                    "확인할 분석 이력 선택", 
                    range(len(st.session_state.history)), 
                    format_func=lambda i: f"[{st.session_state.history[i]['날짜시간']}]: {st.session_state.history[i]['사진 이름']} ({st.session_state.history[i]['최종 충진율']})"
                )
                
                if selected_idx is not None:
                    rec = st.session_state.history[selected_idx]
                    h_col1, h_col2 = st.columns(2)
                    with h_col1:
                        st.text("보정된 원본 이미지")
                        st.image(rec["warped_img"], use_container_width=True)
                    with h_col2:
                        st.text("당시 생성된 진단 마스크")
                        st.image(rec["mask_img"], use_container_width=True)
                
                col_exp1, col_exp2 = st.columns([1, 1])
                with col_exp1:
                    csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
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
