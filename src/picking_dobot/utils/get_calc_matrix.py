import cv2
import numpy as np

# 1. 측정하신 카메라 픽셀 좌표 4개 (u, v)
# 순서: [좌상, 우상, 우하, 좌하] (순서가 일치해야 합니다!)
pts_camera = np.float32([
    [535, 552],  # 점 1
    [199, 48],  # 점 2
    [1117, 407],  # 점 3
    [169, 456]   # 점 4
])

# 2. 매칭되는 로봇 물리 좌표 4개 (X, Y)
pts_robot = np.float32([
    [191.18, -42.18],   # 점 1
    [-26.52, -180.33],  # 점 2
    [156.37, 168.85],  # 점 3
    [161.25, -177.37]    # 점 4
])

# 3. 변환 행렬 계산
matrix = cv2.getPerspectiveTransform(pts_camera, pts_robot)

# 4. 결과 출력
print("\n=== 계산된 변환 행렬 (transform_matrix) ===")
print("np.array([")
for row in matrix:
    print(f"    [{row[0]:.6f}, {row[1]:.6f}, {row[2]:.6f}],")
print("])")

# 5. 검증 (테스트)
print("\n[검증 테스트]")
test_pixel = np.array([300, 250, 1.0]) # 카메라 화면 중앙 근처의 픽셀이라고 가정
result = np.dot(matrix, test_pixel)
robot_x = result[0] / result[2]
robot_y = result[1] / result[2]
print(f"카메라 픽셀 (300, 250) -> 로봇 좌표: X={robot_x:.2f}, Y={robot_y:.2f}")