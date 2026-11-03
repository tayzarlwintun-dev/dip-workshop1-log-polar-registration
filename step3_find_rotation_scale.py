"""
Step 3 - Let the computer FIND the slide by itself, then turn it into
rotation angle and zoom.

How (from the lecture / paper):
  1. Make the log-polar picture of the original and of the test picture (Step 2).
  2. Cross-correlation: try every possible slide (up/down and left/right),
     give each slide a "match score", keep the slide with the best score.
       - we use the fast version called PHASE CORRELATION. It uses the
         Fourier transform to score ALL slides at once instead of one by one,
         and gives a sharp peak at the best slide.
  3. Turn the slide into real answers:
       rows slid    (dy) -> rotation angle = -dy / 360_rows * 360 degrees
       columns slid (dx) -> zoom           = e^(dx * log(max_radius) / 256_columns)
  4. Compare with the true answers in results/test_cases.json.

Note: this only works when the picture is NOT shifted (same center).
test1 and test2 should be correct; test3/4/5 are shifted, so their answers
will be wrong here. Step 4 fixes that.

Output:
  results/step3_results.json      found vs. true values
  results/step3_peaks.png         the "score map" for each test (bright dot = best slide)
"""

import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------
# Settings (same as Step 2)
# ---------------------------------------------------------------
TRUTH_PATH = "results/test_cases.json"
OUT_DIR = "results"
LP_ROWS = 360   # angle steps    (1 row = 1 degree)
LP_COLS = 256   # log-distance steps


def load_gray(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not open {path}")
    return img.astype(np.float32)


def log_polar(img, max_radius):
    """Same as Step 2: rows = angle, columns = log(distance)."""
    h, w = img.shape
    center = (w / 2, h / 2)
    return cv2.warpPolar(img, (LP_COLS, LP_ROWS), center, max_radius,
                         cv2.INTER_LINEAR + cv2.WARP_FILL_OUTLIERS + cv2.WARP_POLAR_LOG)


def phase_correlation(a, b):
    """Find how far picture b is slid compared to picture a.
    Returns (dx, dy, peak, score_map).
      dx = columns slid right, dy = rows slid down
      peak = how strong the best match is (bigger = more sure)
    """
    # soften the left and right edges so the cut edges do not confuse the score
    window = np.hanning(a.shape[1])[None, :].astype(np.float32)
    A = np.fft.fft2((a - a.mean()) * window)
    B = np.fft.fft2((b - b.mean()) * window)
    cross = np.conj(A) * B
    cross /= np.abs(cross) + 1e-9          # keep only the "where", not the "how bright"
    score = np.real(np.fft.ifft2(cross))   # score for every possible slide
    score = np.fft.fftshift(score)         # put "no slide" in the middle of the map

    peak_y, peak_x = np.unravel_index(np.argmax(score), score.shape)
    peak = float(score[peak_y, peak_x])

    # sub-pixel: fit a small parabola through the peak and its neighbours
    def refine(m, p, n):
        d = m - 2 * p + n
        return 0.0 if d == 0 else 0.5 * (m - n) / d
    h, w = score.shape
    fy = refine(score[(peak_y - 1) % h, peak_x], score[peak_y, peak_x], score[(peak_y + 1) % h, peak_x])
    fx = refine(score[peak_y, (peak_x - 1) % w], score[peak_y, peak_x], score[peak_y, (peak_x + 1) % w])

    dy = peak_y + fy - h // 2
    dx = peak_x + fx - w // 2
    return dx, dy, peak, score


def slide_to_rotation_scale(dx, dy, max_radius):
    """Turn the slide into real answers (opposite of expected_slide in Step 2)."""
    angle = -dy / LP_ROWS * 360.0
    angle = (angle + 180) % 360 - 180            # keep it between -180 and 180
    scale = float(np.exp(dx * np.log(max_radius) / LP_COLS))
    return angle, scale


def angle_error(found, true):
    """Smallest difference between two angles (359 deg and 1 deg are only 2 apart)."""
    return abs((found - true + 180) % 360 - 180)


def main():
    with open(TRUTH_PATH) as f:
        truth = json.load(f)

    original = load_gray(truth["original"])
    h, w = original.shape
    max_radius = np.hypot(w / 2, h / 2)
    lp_original = log_polar(original, max_radius)

    print(f"{'test':6} {'slide rows':>10} {'slide cols':>10} {'peak':>6} | "
          f"{'angle found':>11} {'true':>6} {'error':>6} | "
          f"{'zoom found':>10} {'true':>5} {'error':>7} | verdict")
    print("-" * 120)

    results = []
    maps = []
    for t in truth["tests"]:
        lp_test = log_polar(load_gray(t["file"]), max_radius)
        dx, dy, peak, score = phase_correlation(lp_original, lp_test)
        angle, scale = slide_to_rotation_scale(dx, dy, max_radius)

        true_angle = (t["angle"] + 180) % 360 - 180
        a_err = angle_error(angle, true_angle)
        s_err = abs(scale - t["scale"]) / t["scale"] * 100      # in percent
        ok = a_err < 1.0 and s_err < 2.0
        shifted = t["shift_x"] != 0 or t["shift_y"] != 0
        if ok:
            verdict = "CORRECT"
        elif shifted:
            verdict = "not exact, weak peak - picture is shifted (Step 4)"
        else:
            verdict = "WRONG"

        print(f"{t['name']:6} {dy:10.2f} {dx:10.2f} {peak:6.3f} | "
              f"{angle:10.2f}° {true_angle:5.0f}° {a_err:5.2f}° | "
              f"{scale:9.3f}x {t['scale']:4.2f}x {s_err:6.2f}% | {verdict}")

        results.append({"name": t["name"], "slide_rows": round(dy, 3), "slide_cols": round(dx, 3),
                        "peak": round(peak, 4),
                        "angle_found": round(angle, 3), "angle_true": true_angle,
                        "angle_error_deg": round(a_err, 3),
                        "scale_found": round(scale, 4), "scale_true": t["scale"],
                        "scale_error_percent": round(s_err, 3),
                        "shifted": shifted, "correct": bool(ok)})
        maps.append((t, score, dx, dy, peak))

    out_json = os.path.join(OUT_DIR, "step3_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {out_json}")

    # ---- Figure: the score map for each test ----
    n = len(maps)
    fig, axes = plt.subplots(1, n, figsize=(3.3 * n, 4.2))
    for ax, (t, score, dx, dy, peak) in zip(axes, maps):
        ax.imshow(score, cmap="inferno", aspect="auto",
                  extent=[-LP_COLS // 2, LP_COLS // 2, LP_ROWS // 2, -LP_ROWS // 2])
        ax.plot(dx, dy, "o", mfc="none", mec="cyan", ms=14, mew=1.5)
        ax.set_title(f"{t['name']}  peak {peak:.3f}\nslide rows {dy:.1f}, cols {dx:.1f}", fontsize=9)
        ax.set_xlabel("columns slid (zoom)")
        ax.set_ylabel("rows slid (rotation)")
    fig.suptitle("Score for every possible slide - one bright dot = one clear answer", fontsize=11)
    plt.tight_layout()
    out_png = os.path.join(OUT_DIR, "step3_peaks.png")
    plt.savefig(out_png, dpi=110, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_png}")


if __name__ == "__main__":
    main()
