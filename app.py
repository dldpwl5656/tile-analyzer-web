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
            font-size: 1.1rem !important;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        
        .panel-header {
            font-size: 1.2rem !important;
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
if "sample_pts" not in st.session_state:
    st.session_state.sample_pts = []
if "coord_key" not in st.session_state:
    st.session_state.coord_key = 0
if "sample_coord_key" not in st.session_state:
    st.session_state.sample_coord_key = 100

st.markdown("""
    <div class="title-card">
        <h1>🔥 열화상 타일 정밀 충진율 분석 시스템 (Sample Calibration)</h1>
        <p>색상 샘플링 기반 타일 뒷채움 비파괴검사 정밀 이진화</p>
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
        orig_img = full_img.copy()
        img_h, img_w = orig_img.shape[:2]
        
        st.markdown('<div class="sub-instruction">1단계: <b>RGB 타일 영역 4개 모서리 클릭</b> (1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하)</div>', unsafe_allow_html=True)
        
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
            st.markdown('<div class="panel-header">1. 영역 지정 (모서리 4곳)</div>', unsafe_allow_html=True)
            value = streamlit_image_coordinates(
                Image.fromarray(draw_img),
                key=f"mobile_coord_{st.session_state.coord_key}"
            )

            if value is not None:
                point = [value["x"], value["y"]]
                if len(st.session_state.pts) < 4 and point not in st.session_state.pts:
                    st.session_state.pts.append(point)
                    st.rerun()

            st.write(f"📍 모서리 좌표 선택: **{len(st.session_state.pts)} / 4**")
            
            if st.button("🔄 영역 다시 잡기", use_container_width=True):
                st.session_state.pts = []
                st.session_state.sample_pts = []
                st.session_state.coord_key += 1
                st.rerun()

        # 모서리 4개가 모두 지정되었을 때 정면 보정 수행
        if len(st.session_state.pts) == 4:
            TARGET_W = 600
            TARGET_H = 300

            clicked_pts = []
            x_scale = float(img_w) / float(canvas_w)
            y_scale = float(img_h) / float(canvas_h)
            
            for pt in st.session_state.pts:
                clicked_pts.append([int(pt[0] * x_scale), int(pt[1] * y_scale)])

            src_pts = np.float32(clicked_pts)
            dst_pts = np.float32([[0, 0], [TARGET_W, 0], [TARGET_W, TARGET_H], [0, TARGET_H]])
            
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_img = cv2.warpPerspective(orig_img, matrix, (TARGET_W, TARGET_H))
            warped_rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)

            # 정면 보정 이미지에 샘플 포인트 그리기
            draw_warped = warped_rgb.copy()
            for i, sp in enumerate(st.session_state.sample_pts):
                color = (34, 197, 94) if i == 0 else (239, 68, 68)
                label = "충진" if i == 0 else "공복"
                cv2.circle(draw_warped, (sp[0], sp[1]), 10, (255, 255, 255), -1)
                cv2.circle(draw_warped, (sp[0], sp[1]), 8, color, -1)
                cv2.putText(draw_warped, f"{i+1}.{label}", (sp[0]+12, sp[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
                cv2.putText(draw_warped, f"{i+1}.{label}", (sp[0]+12, sp[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            with col2:
                st.markdown('<div class="panel-header">2. 정면 보정 & 샘플 클릭</div>', unsafe_allow_html=True)
                
                if len(st.session_state.sample_pts) == 0:
                    st.info("👆 **[클릭 1회차]** 타일 이미지에서 **가장 확실한 충진(고온) 영역** 1곳을 클릭하세요.")
                elif len(st.session_state.sample_pts) == 1:
                    st.warning("👆 **[클릭 2회차]** 타일 이미지에서 **가장 확실한 공복(저온) 영역** 1곳을 클릭하세요.")
                else:
                    st.success("✅ **기준 샘플 설정 완료!** [분석 실행] 버튼을 눌러주세요.")

                sample_val = streamlit_image_coordinates(
                    Image.fromarray(draw_warped),
                    key=f"sample_coord_{st.session_state.sample_coord_key}"
                )

                if sample_val is not None:
                    s_point = [sample_val["x"], sample_val["y"]]
                    if len(st.session_state.sample_pts) < 2 and s_point not in st.session_state.sample_pts:
                        st.session_state.sample_pts.append(s_point)
                        st.rerun()

                col_s1, col_s2 = st.columns([1, 1])
                with col_s1:
                    if st.button("🔄 샘플 리셋", use_container_width=True):
                        st.session_state.sample_pts = []
                        st.session_state.sample_coord_key += 1
                        st.rerun()
                with col_s2:
                    run_btn = st.button("🚀 분석 실행", disabled=(len(st.session_state.sample_pts) != 2), type="primary", use_container_width=True)

            # ---------------------------------------------------------
            # 🔬 분석 실행 (샘플 기반 유클리드 색상 거리 분류)
            # ---------------------------------------------------------
            if run_btn and len(st.session_state.sample_pts) == 2:
                lab_img = cv2.cvtColor(warped_img, cv2.COLOR_BGR2LAB)
                
                pt_fill = st.session_state.sample_pts[0]
                pt_void = st.session_state.sample_pts[1]

                color_fill = np.mean(lab_img[max(0, pt_fill[1]-1):pt_fill[1]+2, max(0, pt_fill[0]-1):pt_fill[0]+2], axis=(0,1))
                color_void = np.mean(lab_img[max(0, pt_void[1]-1):pt_void[1]+2, max(0, pt_void[0]-1):pt_void[0]+2], axis=(0,1))

                img_pixels = lab_img.astype(np.float32)
                dist_fill = np.linalg.norm(img_pixels - color_fill, axis=2)
                dist_void = np.linalg.norm(img_pixels - color_void, axis=2)

                binary_mask = np.where(dist_fill < dist_void, 255, 0).astype(np.uint8)

                kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                
                binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_close)
                binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_open)
                
                total_pixels = TARGET_W * TARGET_H
                filled_pixels = int(np.sum(binary_mask == 255))
                void_pixels = int(total_pixels - filled_pixels)

                final_ratio = (filled_pixels / total_pixels) * 100.0

                binary_display = cv2.cvtColor(binary_mask, cv2.COLOR_GRAY2RGB)

                with col3:
                    st.markdown('<div class="panel-header">3. 정밀 이진화 결과</div>', unsafe_allow_html=True)
                    st.image(binary_display, use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)

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
                    🔬 <b>이진화 분석 알고리즘:</b> Dual-Point LAB Color Sample Calibration<br>
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
                with col3:
                    st.markdown('<div class="panel-header">3. 정밀 이진화 결과</div>', unsafe_allow_html=True)
                    st.info("2번째 영역에서 [1.충진 / 2.공복] 샘플 클릭 후 분석 실행")

        else:
            with col2:
                st.markdown('<div class="panel-header">2. 정면 보정 & 샘플 클릭</div>', unsafe_allow_html=True)
                st.info("1번 패널에서 4곳 모서리 터치 대기 중")
            with col3:
                st.markdown('<div class="panel-header">3. 정밀 이진화 결과</div>', unsafe_allow_html=True)
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
                        st.session_state.sample_pts = []
                        st.session_state.coord_key += 1
                        st.session_state.sample_coord_key += 1
                        st.rerun()
            else:
                st.caption("저장된 이력이 없습니다.")

else:
    st.session_state.pts = []
    st.session_state.sample_pts = []
    st.info("👈 사이드바에서 열화상 사진을 업로드하세요.")
