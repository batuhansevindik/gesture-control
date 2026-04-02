import cv2
import mediapipe as mp
import subprocess
import time
import math
from collections import deque

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


# =========================
# SISTEM
# =========================
def lock_screen():
    subprocess.run(["loginctl", "lock-session"])


def volume_up():
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+12%"])


def volume_down():
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-12%"])


# =========================
# YARDIMCI
# =========================
def get_center(hand_landmarks, width, height):
    xs = [lm.x for lm in hand_landmarks.landmark]
    ys = [lm.y for lm in hand_landmarks.landmark]
    return int(sum(xs) / len(xs) * width), int(sum(ys) / len(ys) * height)


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def is_four_fingers_up(lm):
    index_up = lm.landmark[8].y < lm.landmark[6].y
    middle_up = lm.landmark[12].y < lm.landmark[10].y
    ring_up = lm.landmark[16].y < lm.landmark[14].y
    pinky_up = lm.landmark[20].y < lm.landmark[18].y
    return index_up and middle_up and ring_up and pinky_up


def is_hand_horizontal(lm):
    x1, y1 = lm.landmark[5].x, lm.landmark[5].y
    x2, y2 = lm.landmark[17].x, lm.landmark[17].y
    slope = abs((y2 - y1) / (x2 - x1 + 1e-6))
    return slope < 0.9


def is_open_palm(lm):
    # Kullanıcının istediği pratik tanım:
    # başparmak ignore, 4 parmak açık yeterli
    return is_four_fingers_up(lm)


def is_cross_position(hand1, hand2, frame_width):
    """
    Cross için:
    - Eller yeterince yakın olmalı
    - Yükseklik farkı çok fazla olmamalı
    - Handedness'e göre çapraz geçmiş olmalı
    """
    label1, cx1, cy1, _ = hand1
    label2, cx2, cy2, _ = hand2

    hand_dist = distance((cx1, cy1), (cx2, cy2))
    close_enough = hand_dist < frame_width * 0.48
    similar_height = abs(cy1 - cy2) < frame_width * 0.18

    crossed = False
    if label1 == "Right" and label2 == "Left":
        crossed = cx1 < cx2
    elif label1 == "Left" and label2 == "Right":
        crossed = cx2 < cx1

    return close_enough and similar_height and crossed, hand_dist


def draw_center_text(frame, text, scale=2.0, color=(0, 255, 255), thickness=5):
    h, w, _ = frame.shape
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    x = (w - tw) // 2
    y = (h + th) // 2
    cv2.putText(frame, text, (x, y), font, scale, (0, 0, 0), thickness + 3)
    cv2.putText(frame, text, (x, y), font, scale, color, thickness)


# =========================
# CROSS STATE
# =========================
STATE_WAIT_CROSS = 0
STATE_WAIT_PALM_WINDOW = 1

state = STATE_WAIT_CROSS
cross_start_time = None
palm_window_start = None
last_lock_time = 0

CROSS_HOLD_TIME = 0.35
PALM_WINDOW_TIME = 4.0
LOCK_COOLDOWN = 3.0

# Avuç gösterme için eller belirgin ayrılmalı
PALM_OPEN_DISTANCE_RATIO = 0.62

# =========================
# SES
# =========================
last_volume_time = 0
VOLUME_COOLDOWN = 0.08
MIN_TOTAL_VERTICAL_MOVE = 3
y_history = deque(maxlen=6)

cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.60,
    min_tracking_confidence=0.60
) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        now = time.time()
        status = "BEKLIYOR"

        hands_data = []
        if result.multi_hand_landmarks and result.multi_handedness:
            for lm, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                label = handedness.classification[0].label
                cx, cy = get_center(lm, w, h)
                hands_data.append((label, cx, cy, lm))

                mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)
                cv2.circle(frame, (cx, cy), 6, (0, 0, 255), -1)
                cv2.putText(
                    frame,
                    label,
                    (cx + 10, cy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )

        # ==================================================
        # AVUC PENCERESI AKTIFSE:
        # artik cross'a bakma, reset de etme
        # sadece 2 saniye icinde avuclari gostermesini bekle
        # ==================================================
        if state == STATE_WAIT_PALM_WINDOW:
            elapsed = now - palm_window_start
            remaining = max(0.0, PALM_WINDOW_TIME - elapsed)

            draw_center_text(frame, f"{remaining:.1f}", scale=1.8)
            status = f"2 SN ICINDE AVUCLARI GOSTER: {remaining:.1f}"

            if len(hands_data) == 2:
                hand1, hand2 = hands_data[0], hands_data[1]

                cx1, cy1 = hand1[1], hand1[2]
                cx2, cy2 = hand2[1], hand2[2]
                lm1 = hand1[3]
                lm2 = hand2[3]

                palm1 = is_open_palm(lm1)
                palm2 = is_open_palm(lm2)
                hand_dist = distance((cx1, cy1), (cx2, cy2))
                hands_far_apart = hand_dist > w * PALM_OPEN_DISTANCE_RATIO

                both_palms_open = palm1 and palm2 and hands_far_apart

                cv2.line(frame, (cx1, cy1), (cx2, cy2), (255, 255, 255), 2)

                cv2.putText(
                    frame,
                    f"PALM1:{palm1} PALM2:{palm2} FAR:{hands_far_apart}",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    f"DIST:{int(hand_dist)}",
                    (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (255, 255, 255),
                    2
                )

                if both_palms_open:
                    if now - last_lock_time > LOCK_COOLDOWN:
                        lock_screen()
                        last_lock_time = now

                    state = STATE_WAIT_CROSS
                    palm_window_start = None
                    cross_start_time = None
                    status = "EKRAN KILITLENDI"

            if elapsed >= PALM_WINDOW_TIME:
                state = STATE_WAIT_CROSS
                palm_window_start = None
                cross_start_time = None
                status = "SURE DOLDU - IPTAL"

            cv2.putText(
                frame,
                status,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            continue

        # =========================
        # NORMAL MOD
        # =========================

        # 2 EL -> CROSS TESPITI
        if len(hands_data) == 2:
            y_history.clear()

            hand1, hand2 = hands_data[0], hands_data[1]
            is_cross, cross_dist = is_cross_position(hand1, hand2, w)

            cx1, cy1 = hand1[1], hand1[2]
            cx2, cy2 = hand2[1], hand2[2]

            cv2.line(frame, (cx1, cy1), (cx2, cy2), (255, 255, 255), 2)

            cv2.putText(
                frame,
                f"CROSS:{is_cross} DIST:{int(cross_dist)}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            if state == STATE_WAIT_CROSS:
                if not is_cross:
                    status = "CROSS YAP"
                    cross_start_time = None
                else:
                    if cross_start_time is None:
                        cross_start_time = now

                    held = now - cross_start_time
                    status = f"CROSS TUT: {held:.1f}/{CROSS_HOLD_TIME}"

                    if held >= CROSS_HOLD_TIME:
                        state = STATE_WAIT_PALM_WINDOW
                        palm_window_start = now
                        cross_start_time = None
                        status = "2 SN ICINDE AVUCLARI GOSTER"

        # 1 EL -> SES
        elif len(hands_data) == 1:
            cross_start_time = None

            _, cx, cy, lm = hands_data[0]

            if is_four_fingers_up(lm) and is_hand_horizontal(lm):
                y_history.append(cy)

                if len(y_history) >= 3:
                    total_dy = y_history[-1] - y_history[0]

                    if abs(total_dy) > MIN_TOTAL_VERTICAL_MOVE and (now - last_volume_time > VOLUME_COOLDOWN):
                        if total_dy < 0:
                            volume_up()
                            status = "SES +"
                        else:
                            volume_down()
                            status = "SES -"

                        last_volume_time = now
                        y_history.clear()
                    else:
                        status = "ELI YUKARI/ASAGI KAYDIR"
                else:
                    status = "HAREKET BASLAT"
            else:
                y_history.clear()
                status = "4 PARMAK + YATAY"

        else:
            y_history.clear()
            cross_start_time = None
            status = "EL ALGILANMADI"

        cv2.putText(
            frame,
            status,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.imshow("Gesture Control", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
