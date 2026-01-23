# -*- coding: utf-8 -*-

from dataclasses import dataclass
import cv2
import numpy as np
import math
import random


stainList = [];

@dataclass
class Stain:
    x: int
    y: int
    B: int
    G: int
    R: int

# -----------------------
# Video settings
# -----------------------
width, height = 1080, 720
fps = 30
duration_seconds = 5
num_frames = fps * duration_seconds

output_file = "expanding_ring.mp4"

# -----------------------
# Ring settings
# -----------------------
center = (width // 2, height // 2)
max_radius = min(width, height) // 2
ring_thickness = 48

background_color = (94,94,94)  # 0–255
#################   NOTE: BGR! BGR!
ring_color = (180, 0, 120)  # purple (BGR)

# -----------------------
# Video writer
# -----------------------
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

# -----------------------
# Generate frames
# -----------------------
for frame_idx in range(num_frames):
    # Create grey background
    frame = np.full((height, width, 3), background_color, dtype=np.uint8)

    for stain in stainList:
        cv2.circle(
            frame,
            (stain.x,stain.y),
            2,
            (stain.B,stain.G,stain.R),
            -1
            )

    # Compute radius for this frame
    radius = int((frame_idx / (num_frames - 1)) * max_radius)

    # Draw ring
    cv2.circle(
        frame,
        center,
        radius,
        ring_color,
        thickness=ring_thickness,
        lineType=cv2.LINE_AA
    )
    angle_rad = random.uniform(0,2 * math.pi) 
    stainList.append(
        Stain(
            x = int (center[0] + radius * math.cos(angle_rad)),
            y = int (center[1] + radius * math.sin(angle_rad)),
            B = ring_color[0],
            G = ring_color[1],
            R = ring_color[2],
            )
        )

    video.write(frame)

video.release()
print(f"Video saved as {output_file}")

