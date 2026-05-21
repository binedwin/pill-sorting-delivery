import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point # 좌표를 보내기 위한 표준 메시지
from cv_bridge import CvBridge
import cv2
import numpy as np

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        
        # 카메라 이미지를 구독
        self.subscription = self.create_subscription(
            Image, '/camera/camera/color/image_raw', self.image_callback, 10)
            
        # 찾은 픽셀 좌표를 퍼블리시
        self.publisher_ = self.create_publisher(Point, '/target_pixel', 10)
        
        self.bridge = CvBridge()
        self.get_logger().info("👁️ 비전 노드 시작됨. 노란색 객체 탐지 중...")

    def image_callback(self, msg):
        # ROS2 이미지를 다시 OpenCV용으로 변환
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        lower_yellow = np.array([20, 150, 80])
        upper_yellow = np.array([35, 255, 255])
        mask_yellow = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
        
        kernel = np.ones((5, 5), np.uint8)
        mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            if cv2.contourArea(contour) > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                cx, cy = x + w // 2, y + h // 2
                
                # 디버그용 화면 표시
                cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.circle(cv_image, (cx, cy), 5, (0, 0, 255), -1)
                
                # 좌표를 Point 메시지로 감싸서 퍼블리시
                point_msg = Point()
                point_msg.x = float(cx)
                point_msg.y = float(cy)
                point_msg.z = 0.0
                self.publisher_.publish(point_msg)
                break # 가장 큰(먼저 찾아진) 객체 하나만 처리

        cv2.imshow("Vision Node", cv_image)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()