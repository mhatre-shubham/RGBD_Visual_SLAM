from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    return LaunchDescription([

        # Publish KITTI RGB images
        Node(
            package='rgbd_slam',
            executable='kitti_publisher.py',
            name='kitti_publisher',
            output='screen'
        ),

        # Depth Anything V2 inference
        Node(
            package='rgbd_slam',
            executable='depth_estimation.py',
            name='depth_estimation',
            output='screen'
        ),

        # Synchronize RGB and depth images for ORB-SLAM3
        Node(
            package='rgbd_slam',
            executable='slam_rgbd_sync_node',
            name='slam_rgbd_sync_node',
            output='screen'
        ),

    ])