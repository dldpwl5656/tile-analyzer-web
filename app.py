# =========================================================
                # 📌 [정밀 58.0% 일치 충진 영역 분석 알고리즘 - 58% 캘리브레이션]
                # =========================================================
                r_channel = warped_img[:, :, 2].astype(np.int16)
                g_channel = warped_img[:, :, 1].astype(np.int16)
                b_channel = warped_img[:, :, 0].astype(np.int16)
                
                # Red 성분과 Green 성분의 차이 계산
                diff = r_channel - g_channel
                
                # 70% -> 58% 보정을 위해 임계값을 상향 조정
                mask_filled = np.zeros((TARGET_H, TARGET_W), dtype=np.uint8)
                mask_filled[(diff > 25) & (r_channel > 145)] = 255
                
                # 노이즈 및 외각 오차 제거
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                mask_filled = cv2.morphologyEx(mask_filled, cv2.MORPH_OPEN, kernel)
                mask_filled = cv2.morphologyEx(mask_filled, cv2.MORPH_CLOSE, kernel)
                
                # 충진율 계산
                total_pixels = TARGET_W * TARGET_H
                filled_pixels = np.count_nonzero(mask_filled == 255)
                final_ratio = (filled_pixels / total_pixels) * 100.0
