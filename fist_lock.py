import cv2
import mediapipe as mp
import subprocess
import time
import math

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def dist_xy(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def lock_screen():
    try:
        subprocess.run(["loginctl", "lock-session"])
    except Exception as e:
        print("Kilit hatası:", e)


def hand_center_px(hand_landmarks, w, h):
    xs = [lm.x for lm in hand_landmarks.landmark]
    ys = [lm.y for lm in hand_landmarks.landmark]
    cx = int(sum(xs) / len(xs) * w)
    cy = int(sum(ys) / len(ys) * h)
    return cx, cy


def hand_is_stable(current_center, previous_center, threshold=16):
    if previous_center is None:
        return True

    movement = dist_xy(
        current_center[0], current_center[1],
        previous_center[0], previous_center[1]
    )
    return movement < threshold


def is_hand_in_region(center_x, center_y, x1, y1, x2, y2):
    return x1 <= center_x <= x2 and y1 <= center_y <= y2


def is_strong_fist(hand_landmarks):
    lm = hand_landmarks.landmark

    # Avuç merkezi yaklaşık hesap
    palm_x = (lm[0].x + lm[5].x + lm[9].x + lm[13].x + lm[17].x) / 5
    palm_y = (lm[0].y + lm[5].y + lm[9].y + lm[13].y + lm[17].y) / 5

    # Parmak uçları avuç merkezine yakın mı?
    tip_ids = [4, 8, 12, 16, 20]
    palm_close_count = 0

    for tip_id in tip_ids:
        d = dist_xy(lm[tip_id].x, lm[tip_id].y, palm_x, palm_y)
        if d < 0.17:
            palm_close_count += 1

    # Parmaklar gerçekten kıvrılmış mı?
    thumb_closed = dist_xy(lm[4].x, lm[4].y, lm[2].x, lm[2].y) < 0.16
    index_closed = lm[8].y > lm[6].y
    middle_closed = lm[12].y > lm[10].y
    ring_closed = lm[16].y > lm[14].y
    pinky_closed = lm[20].y > lm[18].y

    all_closed = all([
        thumb_closed,
        index_closed,
        middle_closed,
        ring_closed,
        pinky_closed
    ])

    # Parmak uçları kendi dip noktalarına da yakın olmalı
    folded_count = 0
    base_pairs = [(4, 2), (8, 5), (12, 9), (16, 13), (20, 17)]

    for tip_id, base_id in base_pairs:
        d = dist_xy(lm[tip_id].x, lm[tip_id].y, lm[base_id].x, lm[base_id].y)
        if d < 0.22:
            folded_count += 1

    return all_closed and palm_close_count >= 5 and folded_count >= 4


cap = cv2.VideoCapture(0)

fist_frames = 0
last_lock_time = 0
previous_center = None

REQUIRED_FRAMES = 55
COOLDOWN_SECONDS = 5

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.80,
    min_tracking_confidence=0.80
) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kamera görüntüsü alınamadı.")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # SAĞ ÜST KİLİT BÖLGESİ
        region_x1 = int(w * 0.65)
        region_y1 = int(h * 0.05)
        region_x2 = int(w * 0.95)
        region_y2 = int(h * 0.35)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        status_text = "El yok"

        # Bölge kutusunu çiz
        cv2.rectangle(
            frame,
            (region_x1, region_y1),
            (region_x2, region_y2),
            (255, 0, 0),
            2
        )

        cv2.putText(
            frame,
            "KILIT BOLGESI",
            (region_x1, region_y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 0),
            2
        )

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                center_x, center_y = hand_center_px(hand_landmarks, w, h)
                current_center = (center_x, center_y)

                stable = hand_is_stable(current_center, previous_center, threshold=16)
                previous_center = current_center

                in_region = is_hand_in_region(
                    center_x, center_y,
                    region_x1, region_y1, region_x2, region_y2
                )

                strong_fist = is_strong_fist(hand_landmarks)

                # El merkezini göster
                cv2.circle(frame, (center_x, center_y), 6, (0, 0, 255), -1)

                if not in_region:
                    fist_frames = 0
                    status_text = "BOLGE DISI"

                elif in_region and not strong_fist:
                    fist_frames = 0
                    status_text = "BOLGEDE AMA YUMRUK DEGIL"

                elif in_region and strong_fist and not stable:
                    fist_frames = 0
                    status_text = "YUMRUK AMA HAREKETLI"

                elif in_region and strong_fist and stable:
                    fist_frames += 1
                    status_text = f"KILIT ICIN BEKLE: {fist_frames}/{REQUIRED_FRAMES}"

                current_time = time.time()
                if fist_frames >= REQUIRED_FRAMES and (current_time - last_lock_time) > COOLDOWN_SECONDS:
                    status_text = "KILITLENIYOR"
                    cv2.putText(
                        frame,
                        status_text,
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3
                    )
                    cv2.imshow("Fist Lock", frame)
                    cv2.waitKey(300)
                    lock_screen()
                    last_lock_time = current_time
                    fist_frames = 0

        else:
            fist_frames = 0
            previous_center = None

        cv2.putText(
            frame,
            status_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

        cv2.imshow("Fist Lock", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break

cap.release()
cv2.destroyAllWindows()
