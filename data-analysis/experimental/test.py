import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import csv

file = open('magsample.csv', 'r')
vec = np.array([row.split(',') for row in file], dtype=float).T
x = vec[0]
y = vec[1]
z = vec[2]
n_frames = len(x)

r_xy = np.sqrt(x**2 + y**2)
theta_xy = np.arctan2(y, x)

r_xz = np.sqrt(x**2 + z**2)
theta_xz = np.arctan2(z, x)

mag_3d = np.sqrt(x**2 + y**2 + z**2)
frames_arr = np.arange(n_frames)

fig = plt.figure(figsize=(10, 10))
gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 1])

ax_polar_xy = fig.add_subplot(gs[0, 0], projection='polar')
ax_polar_xz = fig.add_subplot(gs[0, 1], projection='polar')

ax_arg_xy = fig.add_subplot(gs[1, 0])
ax_arg_xz = fig.add_subplot(gs[1, 1])

ax_mag = fig.add_subplot(gs[2, :])

line_polar_xy, = ax_polar_xy.plot([], [], 'ro-', lw=2)
line_polar_xz, = ax_polar_xz.plot([], [], 'bo-', lw=2)

line_arg_xy, = ax_arg_xy.plot([], [], 'r-', lw=2)
line_arg_xz, = ax_arg_xz.plot([], [], 'b-', lw=2)

line_mag, = ax_mag.plot([], [], 'g-', lw=2)

ax_polar_xy.set_title('Vector Projection (x, y)')
ax_polar_xz.set_title('Vector Projection (x, z)')
max_r = max(np.max(r_xy), np.max(r_xz))
ax_polar_xy.set_ylim(0, max_r * 1.1)
ax_polar_xz.set_ylim(0, max_r * 1.1)

ax_arg_xy.set_title('Argument (x, y) over frames')
ax_arg_xy.set_xlim(0, n_frames - 1)
ax_arg_xy.set_ylim(-np.pi - 0.5, np.pi + 0.5)
ax_arg_xy.set_ylabel('Angle (rad)')

ax_arg_xz.set_title('Argument (x, z) over frames')
ax_arg_xz.set_xlim(0, n_frames - 1)
ax_arg_xz.set_ylim(-np.pi - 0.5, np.pi + 0.5)

ax_mag.set_title('3D Vector Magnitude over frames')
ax_mag.set_xlim(0, n_frames - 1)
ax_mag.set_ylim(np.min(mag_3d)*0.9, np.max(mag_3d) * 1.1)
ax_mag.set_xlabel('Frames passed')
ax_mag.set_ylabel('Magnitude')

plt.tight_layout()

def init():
    line_polar_xy.set_data([], [])
    line_polar_xz.set_data([], [])
    line_arg_xy.set_data([], [])
    line_arg_xz.set_data([], [])
    line_mag.set_data([], [])
    return line_polar_xy, line_polar_xz, line_arg_xy, line_arg_xz, line_mag

def update(frame):
    line_polar_xy.set_data([0, theta_xy[frame]], [0, r_xy[frame]])
    line_polar_xz.set_data([0, theta_xz[frame]], [0, r_xz[frame]])
    
    line_arg_xy.set_data(frames_arr[:frame+1], theta_xy[:frame+1])
    line_arg_xz.set_data(frames_arr[:frame+1], theta_xz[:frame+1])
    
    line_mag.set_data(frames_arr[:frame+1], mag_3d[:frame+1])
    
    return line_polar_xy, line_polar_xz, line_arg_xy, line_arg_xz, line_mag

anim = FuncAnimation(fig, update, frames=n_frames, init_func=init, blit=True)

anim.save('vectorplot.mp4', writer='ffmpeg', fps=20)

plt.show()