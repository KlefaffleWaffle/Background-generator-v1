# -*- coding: utf-8 -*-
import cv2
import numpy as np
import math
import random
 
# -----------------------
# Outrun neon palette (BGR)
# -----------------------

#An array of predetermined colors of an Outrun aesthetic. Will be utilized later.

OUTRUN_COLORS = [
    (255, 0, 200),    # Hot pink
    (255, 0, 120),    # Deep magenta
    (200, 0, 255),    # Purple
    #(255, 100, 255),  # Lavender neon
    (255, 255, 0),    # Cyan
    (200, 255, 50),   # Teal-cyan
    (50, 0, 50), #Dark Purple
]
 
# -----------------------
# Video settings
# -----------------------

# These are the video settings including video dimensions and frame rate.
width, height = 1080, 720
fps = 30
duration_seconds = 180

#total length of the video.
num_frames = fps * duration_seconds
output_file = "line_segment.mp4"
 
# -----------------------
# Segment settings
# -----------------------

#np is the library that helps with math and arrays (may be unnecessary, consider changing);
#Claude suggested doing it like this, will verify.
background_color = np.array([94, 94, 94], dtype=np.float32)

#The animation mimics a squeegee painting. Segment length, is akin to the length of the squeegee.
segment_length = 120
segment_speed = 3.0

#Stains are the little dots left behind after the squeegee moves.
#Stains_per_frame tells the computer how many dots to create. This went through a variety of iterations to find the right stain density.
stains_per_frame = segment_length // 2

#How big the stains are. Also went through a variety of iterations.
stain_radius = 1

#Delay before creating a new segment.
pause_frames = fps * 5

#The segment is a shape called a "Stadium" which is a pre-existing term.
#This is the Stadiums width.
segment_thickness = 4
 
# -----------------------
# Canvas — float32 for blending
# -----------------------

#This creates a grid of pixel arrays. This defines the background.
canvas = np.full((height, width, 3), background_color, dtype=np.float32)

#Creates an overlay grid that will be used to analyze whether a color should be blended or overridden.
grey_mask = np.ones((height, width), dtype=bool)
 
# Precompute stain circle offsets
#Alias
_r = stain_radius

#Creates a 2D grid of values for the bounding box.
_dy, _dx = np.mgrid[-_r:_r+1, -_r:_r+1]
CIRCLE_OFFSETS = np.argwhere((_dx**2 + _dy**2) <= _r**2) - _r  # (N, 2) as (dy, dx)
 

def paint_stains(xs, ys, color):
    color_arr = np.array(color, dtype=np.float32)
    for sx, sy in zip(xs.astype(int), ys.astype(int)):
        pys = sy + CIRCLE_OFFSETS[:, 0]
        pxs = sx + CIRCLE_OFFSETS[:, 1]
        valid = (pxs >= 0) & (pxs < width) & (pys >= 0) & (pys < height)
        pxs, pys = pxs[valid], pys[valid]
        if len(pxs) == 0:
            continue
        is_grey = grey_mask[pys, pxs]
        canvas[pys[is_grey], pxs[is_grey]] = color_arr
        grey_mask[pys[is_grey], pxs[is_grey]] = False
        not_grey = ~is_grey
        if np.any(not_grey):
            canvas[pys[not_grey], pxs[not_grey]] = (
                canvas[pys[not_grey], pxs[not_grey]] + color_arr
            ) / 2.0
 
# -----------------------
# Segment class
# -----------------------
class Segment:
    def __init__(self, x, y, move_angle, line_angle, drift, color):
        self.x = float(x)
        self.y = float(y)
        self.move_angle = move_angle  # direction of travel
        self.line_angle = line_angle  # visual orientation of the segment
        self.drift = drift
        self.color = color
        self.has_been_onscreen = False
 
    def tip(self):
        return self.x, self.y
 
    def tail(self):
        # Tail is offset from tip along line_angle, not move_angle
        return (
            self.x - math.cos(self.line_angle) * segment_length,
            self.y - math.sin(self.line_angle) * segment_length,
        )
 
    def advance(self):
        self.x += math.cos(self.move_angle) * segment_speed
        self.y += math.sin(self.move_angle) * segment_speed
        self.move_angle += self.drift
 
    #######################################################################
    #Checks wheather the segment is on screen or not.
    def tip_onscreen(self):
        hx, hy = self.tip()
        return 0 <= hx < width and 0 <= hy < height
 
    def is_done(self):
        if not self.has_been_onscreen:
            return False
        hx, hy = self.tip()
        return hx < 0 or hx >= width or hy < 0 or hy >= height
 
    def drop_stains(self):
        tx, ty = self.tail()
        hx, hy = self.tip()
        t = np.random.uniform(0.0, 1.0, stains_per_frame)
        xs = tx + t * (hx - tx) + np.random.normal(0, 3, stains_per_frame)
        ys = ty + t * (hy - ty) + np.random.normal(0, 3, stains_per_frame)
        paint_stains(xs, ys, self.color)
 
    def draw(self, frame):
        tx, ty = self.tail()
        hx, hy = self.tip()
        # Debug outline
        cv2.line(
            frame,
            (int(tx), int(ty)),
            (int(hx), int(hy)),
            (255, 255, 255),
            thickness=segment_thickness + 6,
            lineType=cv2.LINE_AA,
        )
        # Main segment
        cv2.line(
            frame,
            (int(tx), int(ty)),
            (int(hx), int(hy)),
            self.color,
            thickness=segment_thickness,
            lineType=cv2.LINE_AA,
        )
 
def spawn_segment():
    edge = random.choice(['left', 'right', 'top', 'bottom'])
    if edge == 'left':
        x = -segment_length
        y = random.uniform(height * 0.1, height * 0.9)
        move_angle = random.uniform(-math.pi / 6, math.pi / 6)
    elif edge == 'right':
        x = width + segment_length
        y = random.uniform(height * 0.1, height * 0.9)
        move_angle = random.uniform(math.pi - math.pi / 6, math.pi + math.pi / 6)
    elif edge == 'top':
        x = random.uniform(width * 0.1, width * 0.9)
        y = -segment_length
        move_angle = random.uniform(math.pi / 3, math.pi * 2 / 3)
    else:
        x = random.uniform(width * 0.1, width * 0.9)
        y = height + segment_length
        move_angle = random.uniform(-math.pi * 2 / 3, -math.pi / 3)
 
    line_angle = random.uniform(0, 2 * math.pi)  # completely independent
    drift = random.uniform(-0.003, 0.003)
    color = random.choice(OUTRUN_COLORS)
    return Segment(x=x, y=y, move_angle=move_angle, line_angle=line_angle, drift=drift, color=color)
 
# -----------------------
# State
# -----------------------
segment = spawn_segment()
pause_countdown = 0
 
# -----------------------
# Video writer
# -----------------------
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
 
# -----------------------
# Main loop
# -----------------------

#For every frame in the 
for frame_idx in range(num_frames):
 
    ###########(Time between spawning segments.)
    if pause_countdown > 0:
        pause_countdown -= 1
        if pause_countdown == 0:
            segment = spawn_segment()
    else:
        if segment.tip_onscreen():
            segment.has_been_onscreen = True
 
        segment.drop_stains()
        segment.advance()
 
        if segment.is_done():
            pause_countdown = pause_frames
 
    frame = np.clip(canvas, 0, 255).astype(np.uint8)
 
    if pause_countdown == 0:
        segment.draw(frame)
 
    video.write(frame)
 
video.release()
print(f"Video saved as {output_file}")