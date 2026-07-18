from pathlib import Path
import cv2
import numpy as np

rgb_dir = Path("/home/mhatre/ros2_humble/data/03/image_0")
depth_vis_dir = Path("/home/mhatre/ros2_humble/data/03/depth_vis")

output_video = Path("./results/depth_video.mp4")

fps = 10

rgb_files = sorted(rgb_dir.glob("*.png"))
depth_files = sorted(depth_vis_dir.glob("*.png"))

assert len(rgb_files) == len(depth_files), "RGB and depth image counts do not match."

# Read first frame
rgb = cv2.imread(str(rgb_files[0]))
depth = cv2.imread(str(depth_files[0]))

# Use RGB size as reference
h, w = rgb.shape[:2]

video = cv2.VideoWriter(
    str(output_video),
    cv2.VideoWriter_fourcc(*"mp4v"),
    fps,
    (w * 2, h)
)

for rgb_path, depth_path in zip(rgb_files, depth_files):

    rgb = cv2.imread(str(rgb_path))
    depth = cv2.imread(str(depth_path))

    rgb = cv2.resize(rgb, (w, h))
    depth = cv2.resize(depth, (w, h))
    frame = np.hstack((rgb, depth))

    video.write(frame)

video.release()

print(f"Video saved as {output_video}")