#!/usr/bin/env python3
from pathlib import Path
import cv2
import numpy as np
import torch
from metric_depth.depth_anything_v2.dpt import DepthAnythingV2

INPUT_DIR = Path("/home/mhatre/ros2_humble/data/03/image_2")
OUTPUT_DEPTH_DIR = Path("/home/mhatre/ros2_humble/data/03/depth")
OUTPUT_VIS_DIR = Path("/home/mhatre/ros2_humble/data/03/depth_vis")

ENCODER = "vits"
DATASET = "vkitti"
MAX_DEPTH = 80

CHECKPOINT_PATH = (
    "/home/mhatre/ros2_humble/external/"
    "Depth-Anything-V2/checkpoints/"
    f"depth_anything_v2_metric_{DATASET}_{ENCODER}.pth"
)

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg"}

MODEL_CONFIGS = {
    "vits": {
        "encoder": "vits",
        "features": 64,
        "out_channels": [48, 96, 192, 384],
    },
    "vitb": {
        "encoder": "vitb",
        "features": 128,
        "out_channels": [96, 192, 384, 768],
    },
    "vitl": {
        "encoder": "vitl",
        "features": 256,
        "out_channels": [256, 512, 1024, 1024],
    },
}

def load_model() -> DepthAnythingV2:
    """
    Load Depth Anything V2 model.

    Returns:
        Initialized and loaded model.
    """
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Using device: {device}")

    model = DepthAnythingV2(**MODEL_CONFIGS[ENCODER], max_depth=MAX_DEPTH)

    model.load_state_dict(
        torch.load(
            CHECKPOINT_PATH,
            map_location=device,
        )
    )

    model.to(device)
    model.eval()

    return model

def visualize_depth(depth: np.ndarray) -> np.ndarray:
    """
    Convert depth map into colored visualization.

    Args:
        depth: Float32 depth image.

    Returns:
        Colored depth image.
    """
    depth = np.nan_to_num(depth)

    depth_min = np.percentile(depth, 5)
    depth_max = np.percentile(depth, 95)

    normalized = np.clip((depth - depth_min) / (depth_max - depth_min + 1e-6), 0.0, 1.0,)

    depth_uint8 = (normalized * 255).astype(np.uint8)

    return cv2.applyColorMap(depth_uint8, cv2.COLORMAP_INFERNO)


def save_depth(depth: np.ndarray, output_path: Path) -> None:
    """
    Save depth as 16-bit PNG in millimeters.

    Args:
        depth: Float depth image (meters).
        output_path: Save destination.
    """
    depth_mm = (depth * 1000).astype(np.uint16)

    cv2.imwrite(str(output_path), depth_mm)


def process_images(model: DepthAnythingV2) -> None:
    """
    Run depth estimation for all images.

    Args:
        model: Loaded depth estimation model.
    """
    OUTPUT_DEPTH_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_VIS_DIR.mkdir(parents=True, exist_ok=True)

    image_files = sorted([
        file
        for file in INPUT_DIR.iterdir()
        if file.suffix.lower() in VALID_EXTENSIONS
    ])

    print(f"Found {len(image_files)} images")

    for index, image_path in enumerate(image_files, start=1):

        rgb = cv2.imread(str(image_path))

        if rgb is None:
            print(f"Skipping: {image_path.name}")
            continue

        with torch.no_grad():
            depth = model.infer_image(rgb)

        depth = depth.astype(np.float32)

        depth_path = (OUTPUT_DEPTH_DIR / image_path.with_suffix(".png").name)

        save_depth(depth, depth_path)

        vis = visualize_depth(depth)

        vis_path = (OUTPUT_VIS_DIR / image_path.name)

        cv2.imwrite(str(vis_path), vis)

        print(
            f"[{index}/{len(image_files)}] "
            f"Processed: {image_path.name}"
        )


def main() -> None:
    model = load_model()
    process_images(model)

    print("\nFinished generating depth maps.")


if __name__ == "__main__":
    main()