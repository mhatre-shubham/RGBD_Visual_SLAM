#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import os

class KITTIPublisher(Node):
    def __init__(self):
        super().__init__('kitti_publisher')

        self.declare_parameter('image_dir', '/home/mhatre/ros2_humble/data/00/image_2')
        self.declare_parameter('frame_rate', 10.0)

        self.image_dir = self.get_parameter('image_dir').value
        self.frame_rate = self.get_parameter('frame_rate').value
        
        self.img_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)

        self.bridge = CvBridge()

        # Load images
        self.images = sorted([
            f for f in os.listdir(self.image_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        self.index = 0

        self.timer = self.create_timer(1.0 / self.frame_rate, self.publish_frame)

        self.get_logger().info("KITTI Publisher Node Started")

    def publish_frame(self):
        if self.index >= len(self.images):
            self.get_logger().info("Dataset finished")
            return

        img_path = os.path.join(self.image_dir, self.images[self.index])
        frame = cv2.imread(img_path)

        if frame is None:
            self.get_logger().error(f"Failed to load {img_path}")
            return

        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera"

        self.img_pub.publish(msg)

        # Publish camera info
        cam_info = CameraInfo()
        cam_info.header = msg.header

        # KITTI left camera intrinsics
        cam_info.k = [
            718.856, 0.0, 607.1928,
            0.0, 718.856, 185.2157,
            0.0, 0.0, 1.0
        ]

        cam_info.width = frame.shape[1]
        cam_info.height = frame.shape[0]

        self.info_pub.publish(cam_info)

        self.index += 1


def main():
    rclpy.init()
    node = KITTIPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()