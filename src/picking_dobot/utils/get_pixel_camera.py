#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class RealSenseClickerROS2(Node):
    def __init__(self):
        super().__init__('realsense_clicker_ros2')
        self.bridge = CvBridge()
        self.current_frame = None

        # 🌟 RealSense ROS 2 노드가 발행하는 컬러 이미지 토픽 이름
        # 보통 ROS 2에서는 '/camera/camera/color/image_raw' 또는 '/camera/color/image_raw' 입니다.
        self.image_topic = "/camera/camera/color/image_raw"
        
        self.subscription = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10
        )
        
        # OpenCV 창 생성 및 마우스 콜백 설정
        cv2.namedWindow('RealSense_ROS2_Calibration')
        cv2.setMouseCallback('RealSense_ROS2_Calibration', self.mouse_click)
        
        self.get_logger().info(f'RealSense 구독 시작 (토픽: {self.image_topic})')
        print("화면의 목표 지점 4곳을 마우스로 클릭하여 픽셀 좌표를 얻으세요.")
        print("종료하려면 'q' 키를 누르세요.\n")

    def mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"🎯 클릭한 픽셀 좌표: [{x}, {y}]")

    def image_callback(self, data):
        try:
            # ROS 2 Image 메시지를 OpenCV 이미지로 변환
            self.current_frame = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except Exception as e:
            self.get_logger().error(f'이미지 변환 실패: {e}')

    def run(self):
        # rclpy.spin_once를 루프 돌리며 OpenCV 창을 갱신합니다.
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.01)
            
            if self.current_frame is not None:
                cv2.imshow('RealSense_ROS2_Calibration', self.current_frame)
                
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = RealSenseClickerROS2()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()