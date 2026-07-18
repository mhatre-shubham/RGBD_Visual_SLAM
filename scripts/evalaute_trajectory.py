import os
import numpy as np
import matplotlib.pyplot as plt

GT_FILE = "/home/mhatre/ros2_humble/data/data_odometry_poses/dataset/poses/03.txt"
SLAM_FILE = "/home/mhatre/ros2_humble/src/rgbd_slam/external/ORB_SLAM3/CameraTrajectory_03_01.txt"

RESULTS_DIR = "./results"
OUTPUT_FILE = os.path.join(RESULTS_DIR, "trajectory_comparison_03_01.png")


def load_kitti_poses(path):
    raw = np.loadtxt(path)
    if raw.ndim == 1:
        raw = raw.reshape(1, -1)
    n = raw.shape[0]
    poses = np.tile(np.eye(4), (n, 1, 1))
    poses[:, :3, :4] = raw.reshape(n, 3, 4)
    return poses


def load_tum_poses(path):
    raw = np.loadtxt(path)
    if raw.ndim == 1:
        raw = raw.reshape(1, -1)
    n = raw.shape[0]
    poses = np.tile(np.eye(4), (n, 1, 1))
    for i in range(n):
        tx, ty, tz = raw[i, 1:4]
        poses[i, :3, 3] = [tx, ty, tz]
    return poses


def main():
    gt_poses = load_kitti_poses(GT_FILE)
    est_poses = load_tum_poses(SLAM_FILE)

    n = min(len(gt_poses), len(est_poses))
    gt_xyz = gt_poses[:n, :3, 3]
    est_xyz = est_poses[:n, :3, 3]

    plt.figure(figsize=(8, 6))
    plt.plot(gt_xyz[:, 0], gt_xyz[:, 2], label="Ground Truth", color="black")
    plt.plot(est_xyz[:, 0], est_xyz[:, 2], label="ORB-SLAM3", color="blue")
    plt.title("Trajectory Comparison")
    plt.xlabel("x [m]")
    plt.ylabel("z [m]")
    plt.axis("equal")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    plt.savefig(OUTPUT_FILE, dpi=1200, bbox_inches="tight")
    print(f"Saved plot to: {OUTPUT_FILE}")

    plt.show()


if __name__ == "__main__":
    main()