"""
Makes ONE picture that explains the log-polar ("clock picture") idea simply.
Rows 1-2: toy drawings (a coloured pie and coloured rings), so you can SEE the slide.
Rows 3-4: my Bangkok photo, test1 (turned 30 deg) and test2 (zoomed x1.5).
Run from the main folder:  python explanations/make_log_polar_explained.py
Output: explanations/log_polar_explained.png
"""
import os
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
ROWS, COLS = 360, 256


def rgb(hexcode):
    return [int(hexcode[i:i + 2], 16) for i in (1, 3, 5)]


def pie(turn_deg=0, size=400):
    """8 coloured slices around the middle (like a clock with 8 colours)."""
    y, x = np.mgrid[0:size, 0:size] - size / 2
    ang = (np.degrees(np.arctan2(y, x)) - turn_deg) % 360
    img = np.zeros((size, size, 3), np.uint8)
    for k in range(8):
        img[(ang >= 45 * k) & (ang < 45 * (k + 1))] = rgb(COLORS[k])
    return img


def rings(zoom=1.0, size=400):
    """Coloured rings, each ring TWICE as far out as the one before (5, 10, 20, 40, 80, 160 px)."""
    y, x = np.mgrid[0:size, 0:size] - size / 2
    r = np.hypot(x, y) / zoom
    img = np.full((size, size, 3), 255, np.uint8)
    edges = [0, 5, 10, 20, 40, 80, 160, 320, 10_000]
    for k in range(len(edges) - 1):
        img[(r >= edges[k]) & (r < edges[k + 1])] = rgb(COLORS[k % 8])
    return img


def clock(img, radius):
    h, w = img.shape[:2]
    return cv2.warpPolar(img, (COLS, ROWS), (w / 2, h / 2), radius,
                         cv2.INTER_LINEAR + cv2.WARP_POLAR_LOG)


def show(ax, img, title, gray=False, aspect="equal"):
    ax.imshow(img, cmap="gray" if gray else None, aspect=aspect)
    ax.set_title(title, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    fig, ax = plt.subplots(4, 4, figsize=(16, 17))

    # Row 1: turn the pie by 45 degrees -> clock picture slides DOWN by 45 rows
    p0, p1 = pie(0), pie(45)
    show(ax[0, 0], p0, "A. Pie with 8 colours")
    show(ax[0, 1], p1, "B. Same pie, TURNED 45° clockwise")
    show(ax[0, 2], clock(p0, 200), "Clock picture of A (row = direction: top row = pointing\nRIGHT, then going around clockwise to the bottom)", aspect="auto")
    show(ax[0, 3], clock(p1, 200), "Clock picture of B\n= the SAME stripes, slid DOWN 45 rows", aspect="auto")
    ax[0, 3].annotate("", xy=(128, 45 + 22), xytext=(128, 22),
                      arrowprops=dict(arrowstyle="-|>", color="black", lw=2))

    # Row 2: zoom the rings x2 -> clock picture slides RIGHT by one ring
    r0, r1 = rings(1), rings(2)
    show(ax[1, 0], r0, "C. Rings, each twice as far out")
    show(ax[1, 1], r1, "D. Same rings, ZOOMED ×2")
    show(ax[1, 2], clock(r0, 200), "Clock picture of C (column = distance,\nlog ruler: every ring is the same width)", aspect="auto")
    show(ax[1, 3], clock(r1, 200), "Clock picture of D\n= the SAME stripes, slid RIGHT by one ring", aspect="auto")
    step = COLS * np.log(2) / np.log(200)
    ax[1, 3].annotate("", xy=(140 + step, 180), xytext=(140, 180),
                      arrowprops=dict(arrowstyle="-|>", color="black", lw=2))

    # Rows 3-4: the real photo
    o = cv2.imread(os.path.join(ROOT, "images/original.jpg"), cv2.IMREAD_GRAYSCALE)
    t1 = cv2.imread(os.path.join(ROOT, "images/generated/test1.png"), cv2.IMREAD_GRAYSCALE)
    t2 = cv2.imread(os.path.join(ROOT, "images/generated/test2.png"), cv2.IMREAD_GRAYSCALE)
    h, w = o.shape
    R = float(np.hypot(w / 2, h / 2))                   # 376 px, half the diagonal
    tower = (330, 150)                                   # the tall tower, top right
    dx, dy = tower[0] - w / 2, tower[1] - h / 2
    row0 = np.degrees(np.arctan2(dy, dx)) % 360          # its direction  (row)
    col0 = COLS * np.log(np.hypot(dx, dy)) / np.log(R)   # its distance   (column)

    show(ax[2, 0], o, "E. My photo (tower = red dot)", gray=True)
    ax[2, 0].plot(*tower, "o", color="#e34948", ms=9)
    show(ax[2, 1], t1, "F. test1: TURNED 30° counter-clockwise", gray=True)
    show(ax[2, 2], clock(o, R), f"Clock picture of E\ntower at row {row0:.0f}", gray=True, aspect="auto")
    ax[2, 2].plot(col0, row0, "o", color="#e34948", ms=9)
    show(ax[2, 3], clock(t1, R), f"Clock picture of F: same picture, slid 30 rows UP\n(turned the other way) → tower at row {row0 - 30:.0f}", gray=True, aspect="auto")
    ax[2, 3].plot(col0, row0 - 30, "o", color="#e34948", ms=9)

    show(ax[3, 0], o, "E. My photo again", gray=True)
    ax[3, 0].plot(*tower, "o", color="#e34948", ms=9)
    show(ax[3, 1], t2, "G. test2: ZOOMED ×1.5", gray=True)
    show(ax[3, 2], clock(o, R), f"Clock picture of E\ntower at column {col0:.0f}", gray=True, aspect="auto")
    ax[3, 2].plot(col0, row0, "o", color="#e34948", ms=9)
    c2 = col0 + COLS * np.log(1.5) / np.log(R)
    show(ax[3, 3], clock(t2, R), f"Clock picture of G: same picture,\nslid 17.5 columns RIGHT → tower at column {c2:.0f}", gray=True, aspect="auto")
    ax[3, 3].plot(c2, row0, "o", color="#e34948", ms=9)

    fig.suptitle("Turning a photo = sliding its clock picture up/down.   Zooming = sliding it right.\n"
                 "Left two: normal photos (everything moves differently).   Right two: clock pictures (everything moves the SAME way).",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=(0, 0, 1, 0.96), h_pad=2.5)
    out = os.path.join(HERE, "log_polar_explained.png")
    plt.savefig(out, dpi=90, bbox_inches="tight")
    print("Saved", out)


if __name__ == "__main__":
    main()
