from pathlib import Path

import matplotlib as mpl
mpl.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patches as patches

FG_COLOR = '#79d5f6'
BG_COLOR = '#4167e1'
# FG_COLOR = '#ffffff'
# BG_COLOR = '#79d5f6'

f = plt.figure(figsize=[1, 1], dpi=8, frameon=False)
f.set_size_inches([4, 4])

ax = plt.Axes(f, [0., 0., 1., 1.])
ax.set_axis_off()
f.add_axes(ax)

ax.set_xlim([0, 10])
ax.set_ylim([0, 10])

# Background
ax.add_patch(patches.Circle((5, 5), radius=5, facecolor=BG_COLOR))
ax.add_patch(patches.Rectangle((0, 5), 5, 5, facecolor=BG_COLOR))
ax.add_patch(patches.Rectangle((5, 0), 5, 5, facecolor=BG_COLOR))

# Foreground
dims = [3.5, 2.5, 1.75, 2.25]
dims = [x * 0.9 for x in dims]
x = 0.5
y = 9.5
for dim in dims:
    y -= dim
    ax.add_patch(patches.Rectangle((x, y), dim, dim, facecolor=FG_COLOR))
    x += dim

plt.savefig(
    Path(__file__).absolute().parents[1] / 'static' / 'favicon.png',
    facecolor='none'
)
