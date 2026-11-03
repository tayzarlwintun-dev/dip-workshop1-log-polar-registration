"""
Step 2 - The log-polar transform ("unrolling" a picture).

What it does:
  For each picture, stand at the CENTER and look out in every direction.
    - each ROW of the new picture   = one direction (angle), 0 to 360 degrees
    - each COLUMN of the new picture = distance from the center, measured on a
      "doubling ruler" (log), so near the center is on the left,
      far away is on the right

What we expect to see (from the lecture):
  - test1 (rotation only)  -> its log-polar picture SLIDES UP/DOWN
  - test2 (zoom only)      -> its log-polar picture SLIDES RIGHT

To prove it, we take the log-polar picture of the ORIGINAL, slide it by the
amount we expect, and check that it now matches the test picture's
log-polar picture (small difference = good match).

Output:
  results/step2_log_polar.png   pictures + their log-polar versions
  results/step2_slide_check.png proof that rotation = slide down, zoom = slide right
"""

import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------
# Settings
# ---------------------------------------------------------------
TRUTH_PATH = "results/test_cases.json"
OUT_DIR = "results"
LP_ROWS = 360   # number of rows   = angle steps  (360 rows -> 1 row = 1 degree)
LP_COLS = 256   # number of columns = distance steps (on the log ruler)


def load_gray(path):
    """Open a picture in black-and-white (grayscale). Matching only needs brightness."""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not open {path}")
    return img.astype(np.float32)


def log_polar(img, max_radius):
    """Unroll the picture around its center.
    Rows = angle, columns = log(distance)."""
    h, w = img.shape
    center = (w / 2, h / 2)
    return cv2.warpPolar(img, (LP_COLS, LP_ROWS), center, max_radius,
                         cv2.INTER_LINEAR + cv2.WARP_FILL_OUTLIERS + cv2.WARP_POLAR_LOG)


def expected_slide(angle_deg, scale, max_radius):
    """How far the log-polar picture should slide for a given rotation and zoom.
    rows:    rotation / 360 * LP_ROWS  (minus sign: OpenCV's y-axis points down,
             so a counter-clockwise turn makes the angle go DOWN = slide UP)
    columns: log(zoom) on the same log ruler OpenCV uses."""
    rows = -angle_deg / 360.0 * LP_ROWS
    cols = LP_COLS * np.log(scale) / np.log(max_radius)
    return rows, cols


def slide(lp, rows, cols):
    """Slide a log-polar picture: rows wrap around (360 deg = 0 deg),
    columns do NOT wrap (stuff pushed off the right edge is gone)."""
    out = np.roll(lp, int(round(rows)), axis=0)        # up/down, with wrap-around
    c = int(round(cols))
    shifted = np.zeros_like(out)
    if c >= 0:
        shifted[:, c:] = out[:, :LP_COLS - c]
    else:
        shifted[:, :LP_COLS + c] = out[:, -c:]
    return shifted


def difference(a, b):
    """Average brightness difference (0 = identical). Ignore black (empty) areas."""
    mask = (a > 0) & (b > 0)
    return float(np.abs(a[mask] - b[mask]).mean())


def main():
    with open(TRUTH_PATH) as f:
        truth = json.load(f)

    original = load_gray(truth["original"])
    h, w = original.shape
    # farthest distance from center = half of the diagonal (reaches the corners)
    max_radius = np.hypot(w / 2, h / 2)
    print(f"Picture {w} x {h}, center ({w/2:.0f}, {h/2:.0f}), max radius {max_radius:.1f} px")
    print(f"Log-polar size: {LP_ROWS} rows (angle) x {LP_COLS} columns (log distance)\n")

    lp_original = log_polar(original, max_radius)

    # ---- Figure 1: every picture and its log-polar version ----
    tests = truth["tests"]
    n = len(tests) + 1
    fig, axes = plt.subplots(2, n, figsize=(3 * n, 7))
    axes[0, 0].imshow(original, cmap="gray"); axes[0, 0].set_title("original")
    axes[1, 0].imshow(lp_original, cmap="gray", aspect="auto")
    axes[1, 0].set_title("log-polar of original", fontsize=9)

    lps = {}
    for i, t in enumerate(tests, start=1):
        img = load_gray(t["file"])
        lps[t["name"]] = log_polar(img, max_radius)
        axes[0, i].imshow(img, cmap="gray")
        axes[0, i].set_title(f"{t['name']}: {t['angle']} deg, x{t['scale']}\n"
                             f"shift ({t['shift_x']},{t['shift_y']})", fontsize=9)
        axes[1, i].imshow(lps[t["name"]], cmap="gray", aspect="auto")
        axes[1, i].set_title(f"log-polar of {t['name']}", fontsize=9)
    for ax in axes[0]:
        ax.axis("off")
    for ax in axes[1]:
        ax.set_xlabel("log distance  ->")
        ax.set_ylabel("angle (deg)")
        ax.set_yticks([0, 90, 180, 270, 359])
    plt.tight_layout()
    path1 = os.path.join(OUT_DIR, "step2_log_polar.png")
    plt.savefig(path1, dpi=110, bbox_inches="tight")
    plt.close()
    print(f"Saved {path1}\n")

    # ---- Check: does sliding the ORIGINAL log-polar give the test's log-polar? ----
    print("Slide check (smaller difference = better match):")
    print(f"{'test':6} {'expect rows':>12} {'expect cols':>12} {'no slide':>9} {'with slide':>11}  verdict")
    check_rows = []
    for t in tests:
        rows, cols = expected_slide(t["angle"], t["scale"], max_radius)
        slid = slide(lp_original, rows, cols)
        d_before = difference(lp_original, lps[t["name"]])
        d_after = difference(slid, lps[t["name"]])
        has_shift = t["shift_x"] != 0 or t["shift_y"] != 0
        if d_after < d_before * 0.5:
            verdict = "MATCH - slide explains it"
        elif has_shift:
            verdict = "no match - picture is also shifted (center moved), see Step 4"
        else:
            verdict = "no match - check this"
        print(f"{t['name']:6} {rows:12.1f} {cols:12.1f} {d_before:9.1f} {d_after:11.1f}  {verdict}")
        check_rows.append((t, rows, cols, slid))

    # ---- Figure 2: proof for test1 (rotation) and test2 (zoom) ----
    fig, axes = plt.subplots(2, 3, figsize=(11, 7))
    for r, (t, rows, cols, slid) in enumerate(check_rows[:2]):
        axes[r, 0].imshow(lp_original, cmap="gray", aspect="auto")
        axes[r, 0].set_title("log-polar of original", fontsize=9)
        axes[r, 1].imshow(slid, cmap="gray", aspect="auto")
        axes[r, 1].set_title(f"original slid by {rows:.0f} rows, {cols:.0f} cols", fontsize=9)
        axes[r, 2].imshow(lps[t["name"]], cmap="gray", aspect="auto")
        axes[r, 2].set_title(f"log-polar of {t['name']} ({t['note']})", fontsize=9)
        for ax in axes[r]:
            ax.set_yticks([0, 90, 180, 270, 359])
    fig.suptitle("Middle and right should look the same", fontsize=11)
    plt.tight_layout()
    path2 = os.path.join(OUT_DIR, "step2_slide_check.png")
    plt.savefig(path2, dpi=110, bbox_inches="tight")
    plt.close()
    print(f"\nSaved {path2}")


if __name__ == "__main__":
    main()
