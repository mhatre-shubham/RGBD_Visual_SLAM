#!/usr/bin/env python3

from pathlib import Path

rgb_dir = Path("/home/mhatre/ros2_humble/data/03/image_0")
depth_dir = Path("/home/mhatre/ros2_humble/data/03/depth")
output_file = Path("/home/mhatre/ros2_humble/data/03/associations.txt")

extensions = {".png", ".jpg", ".jpeg"}

rgb_files = sorted(
    [f for f in rgb_dir.iterdir() if f.suffix.lower() in extensions]
)

with open(output_file, "w") as f:
    for i, rgb_path in enumerate(rgb_files):
        depth_path = depth_dir / rgb_path.name

        if not depth_path.exists():
            print(f"Skipping {rgb_path.name}: depth image not found.")
            continue

        # Timestamp (30 Hz)
        timestamp = i / 30.0

        f.write(
            f"{timestamp:.6f} image_0/{rgb_path.name} "
            f"{timestamp:.6f} depth/{depth_path.name}\n"
        )

print(f"Association file saved to:\n{output_file}")