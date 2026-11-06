"""
Picture that explains the optimizer (Step 6) simply:
  1-2: what "blurry photo" means (BOTH photos are blurred the same way)
  3:   the "hill" for test1: brightness difference when only the TURN knob changes.
       Sharp photos: a bumpy hill with a small dip right next to "no change" -> the optimizer
       gets stuck there. Blurry photos: one smooth valley -> easy to walk down.
Run from the main folder:  python explanations/make_optimizer_explained.py
Output: explanations/optimizer_explained.png
"""
import os
import sys

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import step6_optimizer as s6


def hill(o, t, sigma, angles):
    """Average (brightness difference)^2 for each turn, zoom and move kept right (test1)."""
    h, w = o.shape
    ob, tb = cv2.GaussianBlur(o, (0, 0), sigma), cv2.GaussianBlur(t, (0, 0), sigma)
    vals = []
    for a in angles:
        m = s6.make_matrix(w, h, a, 1.0, 0, 0)
        back = s6.undo(tb, m, w, h)
        seen = s6.undo((t > 0).astype(np.float32), m, w, h) > 0.99
        vals.append(float(np.mean((back[seen] - ob[seen]) ** 2)))
    return np.array(vals)


def main():
    o = cv2.imread("images/original.jpg", cv2.IMREAD_GRAYSCALE).astype(np.float32)
    t = cv2.imread("images/generated/test1.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
    angles = np.arange(-90, 121, 1.0)
    sharp, blurry = hill(o, t, 0.5, angles), hill(o, t, 4.0, angles)

    fig = plt.figure(figsize=(16, 8))
    g = fig.add_gridspec(2, 2, width_ratios=[1, 2.3], hspace=0.25, wspace=0.28)
    crop = (slice(330, 520), slice(60, 330))
    a0, a1, a2 = fig.add_subplot(g[0, 0]), fig.add_subplot(g[1, 0]), fig.add_subplot(g[:, 1])
    a0.imshow(cv2.GaussianBlur(o, (0, 0), 0.5)[crop], cmap="gray")
    a0.set_title("1. SHARP photo\n(thin edges, small windows)", fontsize=11)
    a1.imshow(cv2.GaussianBlur(o, (0, 0), 4.0)[crop], cmap="gray")
    a1.set_title("2. Same photo, BLURRED (blur 4)\nBOTH photos get blurred the same way", fontsize=11)
    for a in (a0, a1):
        a.axis("off")

    a2.plot(angles, sharp, color="#8a8a8a", lw=2, label="sharp photos (blur 0.5)")
    a2.plot(angles, blurry, color="#2a78d6", lw=2.5, label="blurry photos (blur 4)")
    i0 = int(np.where(angles == -1)[0][0])
    a2.annotate("small dip next to the start:\nwith SHARP photos the\noptimizer gets STUCK here",
                xy=(-1, sharp[i0]), xytext=(-95, 1500), fontsize=10.5,
                arrowprops=dict(arrowstyle="-|>", color="#555"))
    a2.axvline(0, color="#e34948", ls="--", lw=1.5)
    a2.text(-3, 1150, "start of optimizer ALONE\n(\"no change\" = 0°)", color="#e34948", fontsize=10.5, va="top", ha="right")
    a2.axvline(30, color="#1baf7a", ls="--", lw=1.5)
    a2.text(50, 700, "right answer: 30°\n(Step 4 starts HERE,\nalready at the bottom)", color="#1baf7a", fontsize=10.5)
    a2.set_xlabel("turn knob (degrees)   — zoom and move kept right", fontsize=11)
    a2.set_ylabel("brightness difference\n(lower = better match)", fontsize=11)
    a2.set_title("3. The \"hill\" for test1 (true turn 30°): the optimizer walks DOWNHILL", fontsize=11)
    a2.legend(frameon=False, loc="lower left", fontsize=10.5)
    a2.spines[["top", "right"]].set_visible(False)
    a2.set_ylim(0, 4800)

    fig.suptitle("The optimizer only compares brightness numbers.  Blurry photos make the hill smooth, "
                 "so it doesn't get stuck in small dips.", fontsize=13, fontweight="bold")
    out = os.path.join(HERE, "optimizer_explained.png")
    plt.savefig(out, dpi=95, bbox_inches="tight")
    print("Saved", out)


if __name__ == "__main__":
    main()
