import lgpio
import time
import cv2
import numpy as np
import threading
import sys

# ==========================================
# 1. 하드웨어 핀 설정 (서보모터 + 스텝모터)
# ==========================================
SERVO_PIN = 18

DIR_PIN = 17
STEP_PIN = 27
ENABLE_PIN = 22

CENTER_ANGLE = 135
LEFT_ANGLE = 95     
RIGHT_ANGLE = 175   

# 라즈베리파이 5 칩 열기 (사용자님 환경에 맞게 gpiochip4 사용)
h = lgpio.gpiochip_open(4) 

for pin in [SERVO_PIN, DIR_PIN, STEP_PIN, ENABLE_PIN]:
    lgpio.gpio_claim_output(h, pin)

# ==========================================
# 2. 모터 제어 함수 (스레드 처리)
# ==========================================
motor_running = False
motor_direction = 0  # 0: 정방향, 1: 역방향

def set_servo(angle):
    """0.4초 동안 비전 연산을 양보하고 서보모터 신호에 집중"""
    pulse_width = (angle / 270) * (0.0025 - 0.0005) + 0.0005
    for _ in range(20):
        lgpio.gpio_write(h, SERVO_PIN, 1)
        time.sleep(pulse_width)
        lgpio.gpio_write(h, SERVO_PIN, 0)
        time.sleep(0.02 - pulse_width)

def step_motor_thread():
    """백그라운드 스텝 모터 구동 스레드"""
    global motor_running
    while motor_running:
        lgpio.gpio_write(h, STEP_PIN, 1)
        time.sleep(0.0001)
        lgpio.gpio_write(h, STEP_PIN, 0)
        time.sleep(0.0001)

def start_conveyor():
    """컨베이어 벨트 가동"""
    global motor_running
    if not motor_running:
        lgpio.gpio_write(h, DIR_PIN, motor_direction)
        lgpio.gpio_write(h, ENABLE_PIN, 0)  # Active Low
        motor_running = True
        threading.Thread(target=step_motor_thread, daemon=True).start()

def stop_conveyor():
    """컨베이어 벨트 정지"""
    global motor_running
    motor_running = False
    time.sleep(0.05)
    lgpio.gpio_write(h, ENABLE_PIN, 1)

# ==========================================
# 3. 비전 처리 전용 함수 (깔끔한 코드 관리)
# ==========================================
def detect_color(color_image):
    """현재 카메라 프레임에서 빨강/파랑 객체를 찾아 색상을 반환합니다."""
    hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)

    lower_red1, upper_red1 = np.array([0, 150, 80]), np.array([10, 255, 255])
    lower_red2, upper_red2 = np.array([170, 150, 80]), np.array([179, 255, 255])
    lower_blue, upper_blue = np.array([100, 150, 80]), np.array([130, 255, 255])

    mask_red = cv2.bitwise_or(cv2.inRange(hsv_image, lower_red1, upper_red1), 
                              cv2.inRange(hsv_image, lower_red2, upper_red2))
    mask_blue = cv2.inRange(hsv_image, lower_blue, upper_blue)

    kernel = np.ones((5, 5), np.uint8)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel)

    detected_color = None
    max_area = 0

    contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours_red:
        area = cv2.contourArea(contour)
        if area > 1000 and area > max_area:
            max_area = area
            detected_color = 'red'

    contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours_blue:
        area = cv2.contourArea(contour)
        if area > 1000 and area > max_area:
            max_area = area
            detected_color = 'blue'

    return detected_color

# ==========================================
# 4. 사용자 세팅 및 메인 로직
# ==========================================
print("===================================")
print("   스마트 컨베이어 분류 시스템 시작   ")
print("===================================")
target_color = input("분류할 타겟 색상을 입력하세요 (blue 또는 red): ").strip().lower()

if target_color not in ['blue', 'red']:
    target_color = 'blue'

print(f"\n=> [{target_color.upper()}] 색상은 왼쪽({LEFT_ANGLE}도)으로 분류합니다.")
print(f"=> 나머지 색상은 오른쪽({RIGHT_ANGLE}도)으로 분류합니다.\n")

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("🚨 에러: 카메라를 열 수 없습니다.")
    exit()

# 초기화
set_servo(CENTER_ANGLE)
stop_conveyor()

print("✅ 시스템 준비 완료. 터미널 창을 활성화 해주세요.")
print("종료하려면 터미널에서 Ctrl+C 를 누르세요.\n")

try:
    while True:
        # [단계 1~2] 두봇 신호 대기 (현재는 터미널 입력으로 대체)
        # sys.stdin.readline()은 사용자가 엔터를 칠 때까지 무한 대기합니다.
        input("🤖 [대기] 두봇이 물건을 올리면 'Enter' 키를 누르세요 (신호 발생): ")
        print("="*50)
        print("📥 두봇 신호 수신 완료! 공정을 시작합니다.")

        # [단계 3] 컨베이어 2초 가동 (상자를 카메라 밑으로 이송)
        print("▶️ 3. 컨베이어 이송 시작 (2초)")
        start_conveyor()
        time.sleep(2.0)
        stop_conveyor()  # 정확히 카메라 밑에서 멈춤
        time.sleep(0.5)  # 잔진동 멈출 시간 부여

        # [단계 4] 카메라 인식 시작 (최대 2초간 시도)
        print("🔍 4. 객체 인식 중...")
        detected_color = None
        start_time = time.time()
        
        # 최신 프레임을 얻기 위해 버퍼를 비워줌
        for _ in range(5): cap.read()

        while (time.time() - start_time) < 2.0:
            ret, color_image = cap.read()
            if not ret: continue
            
            detected_color = detect_color(color_image)
            if detected_color:
                break # 색상을 찾으면 즉시 반복문 탈출

        if not detected_color:
            print("🚨 ⚠️ 경고: 지정된 객체(색상)를 인식하지 못했습니다. 공정을 초기화합니다.")
            print("="*50 + "\n")
            continue # 다음 박스 대기로 넘어감

        print(f"🎯 인식 성공: [{detected_color.upper()}] 객체 확인!")

        # [단계 5] 분류기 작동
        if detected_color == target_color:
            print(f"✅ 5. 타겟 일치! 분류기 왼쪽({LEFT_ANGLE}도) 세팅")
            set_servo(LEFT_ANGLE)
        else:
            print(f"❌ 5. 타겟 불일치! 분류기 오른쪽({RIGHT_ANGLE}도) 세팅")
            set_servo(RIGHT_ANGLE)

        # [단계 6] 컨베이어 재가동 (분류 완료 후 상자 배출)
        print("▶️ 6. 컨베이어 재가동 (2초간 상자 배출)")
        start_conveyor()
        time.sleep(2.0) # 상자가 밀려 내려갈 때까지 가동
        stop_conveyor()

        # 공정 마무리: 분류기 중앙 복귀
        print("⏳ 공정 완료. 다음 상자를 위해 분류기를 중앙으로 복귀합니다.")
        set_servo(CENTER_ANGLE)
        print("="*50 + "\n")

except KeyboardInterrupt:
    print("\n사용자에 의해 프로그램을 종료합니다.")

finally:
    cap.release()
    cv2.destroyAllWindows()
    stop_conveyor() 
    lgpio.gpiochip_close(h)
    print("시스템이 안전하게 종료되었습니다.")