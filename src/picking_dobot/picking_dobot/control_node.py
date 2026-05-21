import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from rclpy.action import ActionClient
from dobot_msgs.action import PointToPoint
import numpy as np
import time

class ControlNode(Node):
    def __init__(self):
        super().__init__('control_node')
        
        # 비전 노드가 보낸 픽셀 좌표를 구독
        self.subscription = self.create_subscription(
            Point, '/target_pixel', self.target_callback, 10)
            
        self._action_client = ActionClient(self, PointToPoint, 'PTP_action')
        
        self.is_moving = False
        self.cooldown_until = 0.0
        
        # 🌟 다단계 이동을 위한 상태 변수
        self.current_step = 0 
        self.target_x = 0.0
        self.target_y = 0.0
        
        # 🌟 Z축 높이 설정 (하드코딩)
        self.safe_z = 20.0       # 이동 시 안전 높이
        self.pick_z = -31.77     # 물체를 집기 위한 하강 높이
        
        self.transform_matrix = np.array([
            [0.061468, 0.724471, -76.627215],
            [0.624325, -0.172503, -317.373288],
            [0.000275, 0.001297, 1.000000],
        ])
        
        self.get_logger().info("🦾 제어 노드 시작됨. 목표 좌표 대기 중...")

    def pixel_to_robot_coords(self, u, v):
        camera_pt = np.array([u, v, 1.0])
        robot_pt = np.dot(self.transform_matrix, camera_pt)
        return robot_pt[0] / robot_pt[2], robot_pt[1] / robot_pt[2]

    def target_callback(self, msg):
        if self.is_moving:
            return

        current_time = self.get_clock().now().nanoseconds / 1e9
        if current_time < self.cooldown_until:
            return

        cx, cy = msg.x, msg.y
        self.target_x, self.target_y = self.pixel_to_robot_coords(cx, cy)
        
        self.is_moving = True
        self.current_step = 1  # 1단계 시작
        
        # 1단계: X, Y 좌표로 이동하되, Z는 안전 높이(safe_z) 유지
        target_pose = [float(self.target_x), float(self.target_y), self.safe_z, 0.0]
        
        self.get_logger().info("="*40)
        self.get_logger().info(f"📍 [Step 1] 목표 상공으로 이동: X={self.target_x:.1f}, Y={self.target_y:.1f}, Z={self.safe_z}")
        self.send_goal(target_pose)

    def send_goal(self, target):
        self._action_client.wait_for_server()
        goal_msg = PointToPoint.Goal()
        goal_msg.target_pose = target
        goal_msg.motion_type = 1 # 1: PTP 모드 (직선 또는 관절 이동)

        send_goal_future = self._action_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('🚨 명령 거절됨! 공정을 초기화합니다.')
            
            # 거절 시 모든 상태 리셋 및 쿨다운
            current_time = self.get_clock().now().nanoseconds / 1e9
            self.cooldown_until = current_time + 2.0
            self.is_moving = False
            self.current_step = 0
            return
        
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        # 현재 단계의 이동이 완료되었을 때 실행됨
        if self.current_step == 1:
            self.get_logger().info(f'⬇️ [Step 2] 물체 향해 하강 (Z={self.pick_z})')
            self.current_step = 2
            target_pose = [float(self.target_x), float(self.target_y), self.pick_z, 0.0]
            self.send_goal(target_pose)
            
        elif self.current_step == 2:
            self.get_logger().info('✅ 하강 완료! (여기에 흡착/그리퍼 작동 코드 추가 가능)')
            time.sleep(1.0) # 하강 후 물체를 확실히 집을 시간(1초) 부여
            
            self.get_logger().info(f'⬆️ [Step 3] 안전 높이로 복귀 (Z={self.safe_z})')
            self.current_step = 3
            target_pose = [float(self.target_x), float(self.target_y), self.safe_z, 0.0]
            self.send_goal(target_pose)
            
        elif self.current_step == 3:
            self.get_logger().info('🎯 모든 픽업 시퀀스 완료! 2초 대기 후 다음 목표를 찾습니다.')
            self.get_logger().info("="*40 + "\n")
            
            current_time = self.get_clock().now().nanoseconds / 1e9
            self.cooldown_until = current_time + 2.0
            self.is_moving = False 
            self.current_step = 0

def main(args=None):
    rclpy.init(args=args)
    node = ControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()