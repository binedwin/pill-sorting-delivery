#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
# 두봇 패키지에서 제공하는 메시지 타입을 임포트해야 합니다.
# 보통 geometry_msgs/PoseStamped 또는 자체 정의한 메시지를 사용합니다.
from geometry_msgs.msg import PoseStamped 

class DobotPoseSubscriber(Node):
    def __init__(self):
        super().__init__('dobot_pose_subscriber')
        
        # 🌟 두봇이 현재 위치를 발행하는 ROS 2 토픽을 구독합니다.
        # 패키지 스펙에 따라 토픽 이름('/dobot_pose')과 메시지 타입(PoseStamped)을 확인해 주세요.
        self.subscription = self.create_subscription(
            PoseStamped,
            '/dobot_TCP',
            self.pose_callback,
            10
        )
        self.get_logger().info('두봇 좌표 구독 노드가 시작되었습니다.')
        print("두봇 팔의 버튼을 누르고 손으로 움직이면서 터미널의 X, Y 좌표를 기록하세요.\n")

    def pose_callback(self, msg):
        # geometry_msgs/PoseStamped 기준 좌표 추출
        x = msg.pose.position.x *1000
        y = msg.pose.position.y *1000
        z = msg.pose.position.z *1000
        
        # 두봇 단위가 mm인지 m인지 확인 후 출력 (보통 ROS 표준은 m이므로 mm 변환이 필요할 수 있습니다)
        print(f" 현재 두봇 위치 -> X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}")

def main(args=None):
    rclpy.init(args=args)
    node = DobotPoseSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('사용자에 의해 노드가 종료되었습니다.')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()