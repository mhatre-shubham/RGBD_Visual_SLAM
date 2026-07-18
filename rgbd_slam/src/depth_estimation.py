#!/usr/bin/env python3

import cv2
import torch
import numpy as np
import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from metric_depth.depth_anything_v2.dpt import DepthAnythingV2

class DepthAnythingNode(Node):

    def __init__(self):
        super().__init__('depth_anything_v2_node')

        self.bridge = CvBridge()
        self.rgb_sub = self.create_subscription(Image,'/camera/image_raw', self.image_callback, 10)
        self.depth_pub = self.create_publisher(Image, '/depth/image_raw', 10)
        self.depth_vis_pub = self.create_publisher(Image,'/depth/image_color', 10)

        # Model config
        self.encoder = 'vits'
        self.dataset = 'vkitti'
        self.max_depth = 80

        model_configs = {
            'vits': {
                'encoder': 'vits',
                'features': 64,
                'out_channels': [48, 96, 192, 384]
            },
            'vitb': {
                'encoder': 'vitb',
                'features': 128,
                'out_channels': [96, 192, 384, 768]
            },
            'vitl': {
                'encoder': 'vitl',
                'features': 256,
                'out_channels': [256, 512, 1024, 1024]
            }
        }

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.get_logger().info(f'Using device: {self.device}')

        # Load Model
        self.model = DepthAnythingV2(
            **{
                **model_configs[self.encoder],
                'max_depth': self.max_depth
            }
        )


        checkpoint_path = os.path.join(
            "/home/mhatre/ros2_humble/external/Depth-Anything-V2/checkpoints",
            f"depth_anything_v2_metric_{self.dataset}_{self.encoder}.pth"
        )

        self.model.load_state_dict(
            torch.load(checkpoint_path, map_location=self.device)
        )

        self.model.to(self.device)
        self.model.eval()
        self.get_logger().info("Depth Anything V2 Metric model loaded successfully")

    def image_callback(self, msg):
        rgb = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        with torch.no_grad():
            depth = self.model.infer_image(rgb)

        depth = depth.astype(np.float32)
        depth_msg = self.bridge.cv2_to_imgmsg(depth, encoding='32FC1')
        depth_msg.header = msg.header
        self.depth_pub.publish(depth_msg)

        # Color depth
        depth_vis = self.visualize_depth(depth)
        vis_msg = self.bridge.cv2_to_imgmsg(depth_vis, encoding='bgr8')
        vis_msg.header = msg.header
        self.depth_vis_pub.publish(vis_msg)
        self.get_logger().info(f'Depth range: {depth.min():.2f}m - {depth.max():.2f}m')

    def visualize_depth(self, depth):
        depth = np.nan_to_num(depth)

        d_min = np.percentile(depth, 5)
        d_max = np.percentile(depth, 95)

        depth_norm = np.clip((depth - d_min) / (d_max - d_min + 1e-6), 0, 1)
        depth_8u = (depth_norm * 255).astype(np.uint8)

        depth_color = cv2.applyColorMap(depth_8u, cv2.COLORMAP_INFERNO)

        return depth_color

def main():
    rclpy.init()
    node = DepthAnythingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()