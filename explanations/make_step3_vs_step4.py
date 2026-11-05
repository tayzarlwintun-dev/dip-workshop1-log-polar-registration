"""
Picture: Step 3 = ONE check at the middle; Step 4 = the same check at MANY spots.
Uses test3 (turned 45°, zoomed x1.5, moved). Run from the main folder:
    python explanations/make_step3_vs_step4.py      -> explanations/step3_vs_step4.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import step3_find_rotation_scale as s3
import step4_find_shift as s4


def score_panel(ax, A, B, title):
    """Run the slide search (phase correlation) once and draw its score map."""
    dx, dy, peak, smap = s3.phase_correlation(A, B)
    h, w = smap.shape
    ax.imshow(smap, cmap="inferno", extent=[-w / 2, w / 2, h / 2, -h / 2], aspect="auto")
    ax.plot(dx, dy, "o", mfc="none", mec="cyan", ms=14, mew=2)
    ax.set_title(f"{title}\npeak {peak:.2f}", fontsize=10)
    ax.set_xlabel("columns slid (zoom)", fontsize=8)
    ax.set_ylabel("rows slid (turn)", fontsize=8)
    ax.tick_params(labelsize=7)
    return peak


def main():
    o = s3.load_gray("images/original.jpg")
    t = s3.load_gray("images/generated/test3.png")
    h, w = o.shape
    mid = (w / 2, h / 2)
    R = float(np.hypot(w / 2, h / 2))
    spots = {"A": (100, 150), "B": (310, 520), "C": (193, 310)}   # C = the right place

    fig, ax = plt.subplots(2, 5, figsize=(20, 10.5), gridspec_kw={"width_ratios": [1, 1, 1.15, 1.15, 1.15]})

    # ---- Row 1: Step 3 = ONE check, middle vs middle ----
    ax[0, 0].imshow(o, cmap="gray")
    ax[0, 0].plot(*mid, "o", color="#e34948", ms=12, mec="white", mew=2)
    ax[0, 0].set_title("ORIGINAL\nred = its middle", fontsize=10)
    ax[0, 1].imshow(t, cmap="gray")
    ax[0, 1].plot(*mid, "o", color="#e34948", ms=12, mec="white", mew=2)
    ax[0, 1].set_title("TEST3 (turned, zoomed, MOVED)\nred = its middle = a DIFFERENT building", fontsize=10)
    lpo, lpt = s3.log_polar(o, R), s3.log_polar(t, R)
    ax[0, 2].imshow(lpo, cmap="gray", aspect="auto")
    ax[0, 2].set_title("clock picture of the ORIGINAL\nmade at ITS middle", fontsize=10)
    ax[0, 3].imshow(lpt, cmap="gray", aspect="auto")
    ax[0, 3].set_title("clock picture of TEST3\nmade at ITS middle", fontsize=10)
    score_panel(ax[0, 4], lpo, lpt, "STEP 3: one slide search\nno clear dot = no real match")
    for a in ax[0, :4]:
        a.set_xticks([])
        a.set_yticks([])

    # ---- Row 2: Step 4 = the same check at MANY spots ----
    ax[1, 0].imshow(o, cmap="gray")
    gx, gy = np.meshgrid(np.arange(20, w, 24), np.arange(20, h, 24))
    ax[1, 0].plot(gx, gy, ".", color="#eda100", ms=3)
    for name, (x, y) in spots.items():
        ax[1, 0].plot(x, y, "o", mfc="none", mec="cyan" if name == "C" else "white", ms=16, mew=2.5)
        ax[1, 0].text(x + 14, y - 10, name, color="cyan" if name == "C" else "white", fontsize=15, fontweight="bold")
    ax[1, 0].set_title("ORIGINAL: Step 4 tries EVERY spot\n(orange = a few of them; A, B, C as examples)", fontsize=10)
    ax[1, 1].imshow(t, cmap="gray")
    ax[1, 1].plot(*mid, "o", color="#e34948", ms=12, mec="white", mew=2)
    ax[1, 1].set_title("TEST3: its middle stays FIXED\n(clock picture made here once)", fontsize=10)
    B = s4.log_polar_at(t, mid)
    for k, (name, label) in enumerate([("A", "spot A (sky, wrong place)"),
                                       ("B", "spot B (street, wrong place)"),
                                       ("C", "spot C = RIGHT place (best)")]):
        A = s4.log_polar_at(o, spots[name])
        score_panel(ax[1, 2 + k], A, B, f"STEP 4 at {label}")
    for a in ax[1, :2]:
        a.set_xticks([])
        a.set_yticks([])

    fig.text(0.005, 0.73, "STEP 3\none check", fontsize=15, fontweight="bold", rotation=90, va="center")
    fig.text(0.005, 0.27, "STEP 4\nmany checks", fontsize=15, fontweight="bold", rotation=90, va="center")
    fig.suptitle("Step 3 = the slide search at ONE spot (the middle).   Step 4 = the SAME slide search at EVERY spot, keep the best.",
                 fontsize=14, fontweight="bold")
    plt.tight_layout(rect=(0.02, 0, 1, 0.95), h_pad=3)
    out = os.path.join(HERE, "step3_vs_step4.png")
    plt.savefig(out, dpi=85, bbox_inches="tight")
    print("Saved", out)


if __name__ == "__main__":
    main()
