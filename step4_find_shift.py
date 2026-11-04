"""
Step 4 - Find the SHIFT by searching for the right "standing spot" (center).

The problem (from Step 3):
  We always unrolled both pictures around their MIDDLE pixel. If the test picture
  was also moved, its middle is a DIFFERENT spot of the city -> no good match.

The fix (the paper's algorithm, slide 11):
  1. Take the TEST picture and unroll it around its middle. Keep this fixed.
     (We use the test picture as the fixed one because it is zoomed IN, so it
      shows a smaller part of the city that surely exists in the original.)
  2. In the ORIGINAL picture, try many standing spots (x, y):
        - unroll the original around (x, y)
        - run Step 3 (phase correlation) -> best slide + peak (how sure)
  3. The spot with the HIGHEST PEAK is the spot that shows the same building
     as the middle of the test picture.
  4. From that spot + the rotation + zoom, calculate the shift.

Speed trick (coarse-to-fine, like Google Maps zoom):
  - Coarse search: try every 4th pixel in a big area   -> rough best spot
  - Fine search:   try every pixel near the rough spot -> exact best spot

How the shift is calculated:
  The test picture was made like this (Step 1):
      test_point = zoom * rotate(original_point - middle) + middle + shift
  The middle of the test picture came from the best spot in the original, so:
      middle = zoom * rotate(best_spot - middle) + middle + shift
      shift  = - zoom * rotate(best_spot - middle)

Output:
  results/step4_results.json     found vs. true values
  results/step4_search_maps.png  peak for every spot tried (bright = good match)
"""

import json
import os
import time

import cv2
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------
# Settings
# ---------------------------------------------------------------
TRUTH_PATH = "results/test_cases.json"
OUT_DIR = "results"
LP_ROWS = 360       # angle steps (1 row = 1 degree)
LP_COLS = 256       # log-distance steps
RADIUS = 180        # how far we look from the standing spot (pixels)
SEARCH = 60         # search spots up to 60 px away from the middle (left/right/up/down)
COARSE_STEP = 4     # coarse search: every 4th pixel
FINE_RANGE = 4      # fine search: +-4 px around the coarse best, every pixel


def load_gray(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not open {path}")
    return img.astype(np.float32)


def log_polar_at(img, center):
    """Unroll the picture around ANY standing spot (center), looking RADIUS px far."""
    return cv2.warpPolar(img, (LP_COLS, LP_ROWS), center, RADIUS,
                         cv2.INTER_LINEAR + cv2.WARP_FILL_OUTLIERS + cv2.WARP_POLAR_LOG)


WINDOW = np.hanning(LP_COLS)[None, :].astype(np.float32)


def spectrum(lp):
    """Fourier transform of an unrolled picture (done once per picture, reused)."""
    return np.fft.fft2((lp - lp.mean()) * WINDOW)


def phase_correlation(A, B):
    """Same as Step 3, but takes the Fourier transforms directly (faster).
    Returns (dx, dy, peak)."""
    cross = np.conj(A) * B
    cross /= np.abs(cross) + 1e-9
    score = np.fft.fftshift(np.real(np.fft.ifft2(cross)))
    py, px = np.unravel_index(np.argmax(score), score.shape)
    h, w = score.shape

    def refine(m, p, n):
        d = m - 2 * p + n
        return 0.0 if d == 0 else 0.5 * (m - n) / d
    fy = refine(score[(py - 1) % h, px], score[py, px], score[(py + 1) % h, px])
    fx = refine(score[py, (px - 1) % w], score[py, px], score[py, (px + 1) % w])
    return px + fx - w // 2, py + fy - h // 2, float(score[py, px])


def slide_to_rotation_scale(dx, dy):
    angle = -dy / LP_ROWS * 360.0
    angle = (angle + 180) % 360 - 180
    scale = float(np.exp(dx * np.log(RADIUS) / LP_COLS))
    return angle, scale


def search(original, B_test, centers):
    """Try every standing spot in `centers`. Return the best one and all peaks."""
    best = None
    peaks = []
    for (x, y) in centers:
        A = spectrum(log_polar_at(original, (float(x), float(y))))
        dx, dy, peak = phase_correlation(A, B_test)
        peaks.append(peak)
        if best is None or peak > best["peak"]:
            best = {"x": x, "y": y, "dx": dx, "dy": dy, "peak": peak}
    return best, peaks


def shift_from_spot(spot, middle, angle, scale):
    """shift = - zoom * rotate(spot - middle)   (see explanation at the top)"""
    a = np.deg2rad(angle)
    # OpenCV's rotation (y-axis points down) for a counter-clockwise angle
    rot = np.array([[np.cos(a), np.sin(a)],
                    [-np.sin(a), np.cos(a)]])
    d = np.array([spot[0] - middle[0], spot[1] - middle[1]])
    return -scale * rot @ d


def angle_error(found, true):
    return abs((found - true + 180) % 360 - 180)


def main():
    with open(TRUTH_PATH) as f:
        truth = json.load(f)

    original = load_gray(truth["original"])
    h, w = original.shape
    middle = (w / 2, h / 2)
    print(f"Picture {w} x {h}, middle {middle}, look radius {RADIUS} px")
    print(f"Search area: +-{SEARCH} px around the middle "
          f"(coarse every {COARSE_STEP} px, then fine +-{FINE_RANGE} px)\n")

    coarse = [(middle[0] + ox, middle[1] + oy)
              for oy in range(-SEARCH, SEARCH + 1, COARSE_STEP)
              for ox in range(-SEARCH, SEARCH + 1, COARSE_STEP)]
    n_side = len(range(-SEARCH, SEARCH + 1, COARSE_STEP))

    header = (f"{'test':6} {'spot found':>14} {'peak':>6} | {'angle':>8} {'true':>5} {'err':>6} | "
              f"{'zoom':>7} {'true':>5} {'err':>6} | {'shift found':>15} {'true':>11} {'err':>6} | verdict")
    print(header)
    print("-" * len(header))

    results, maps = [], []
    for t in truth["tests"]:
        start = time.time()
        test = load_gray(t["file"])
        # 1) unroll the TEST picture around its middle (fixed)
        B_test = spectrum(log_polar_at(test, middle))

        # 2) coarse search in the ORIGINAL
        best, peaks = search(original, B_test, coarse)
        # 3) fine search around the coarse best
        fine = [(best["x"] + ox, best["y"] + oy)
                for oy in range(-FINE_RANGE, FINE_RANGE + 1)
                for ox in range(-FINE_RANGE, FINE_RANGE + 1)]
        best, _ = search(original, B_test, fine)

        # 4) rotation, zoom, shift
        angle, scale = slide_to_rotation_scale(best["dx"], best["dy"])
        shift = shift_from_spot((best["x"], best["y"]), middle, angle, scale)

        true_angle = (t["angle"] + 180) % 360 - 180
        a_err = angle_error(angle, true_angle)
        s_err = abs(scale - t["scale"]) / t["scale"] * 100
        sh_err = float(np.hypot(shift[0] - t["shift_x"], shift[1] - t["shift_y"]))
        ok = a_err < 1.0 and s_err < 2.0 and sh_err < 3.0
        secs = time.time() - start

        print(f"{t['name']:6} ({best['x']:5.0f},{best['y']:5.0f}) {best['peak']:6.3f} | "
              f"{angle:7.2f}° {true_angle:4.0f}° {a_err:5.2f}° | "
              f"{scale:6.3f}x {t['scale']:4.2f}x {s_err:5.2f}% | "
              f"({shift[0]:6.1f},{shift[1]:6.1f}) ({t['shift_x']:4},{t['shift_y']:4}) {sh_err:5.1f}px | "
              f"{'CORRECT' if ok else 'WRONG'}  ({secs:.1f}s)")

        results.append({"name": t["name"],
                        "spot_found": [best["x"], best["y"]], "peak": round(best["peak"], 4),
                        "angle_found": round(angle, 3), "angle_true": true_angle,
                        "angle_error_deg": round(a_err, 3),
                        "scale_found": round(scale, 4), "scale_true": t["scale"],
                        "scale_error_percent": round(s_err, 3),
                        "shift_found": [round(float(shift[0]), 2), round(float(shift[1]), 2)],
                        "shift_true": [t["shift_x"], t["shift_y"]],
                        "shift_error_px": round(sh_err, 2),
                        "correct": bool(ok), "seconds": round(secs, 2)})
        maps.append((t, np.array(peaks).reshape(n_side, n_side), best))

    out_json = os.path.join(OUT_DIR, "step4_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {out_json}")

    # ---- Figure: peak for every standing spot tried ----
    n = len(maps)
    fig, axes = plt.subplots(1, n, figsize=(3.3 * n, 4))
    ext = [middle[0] - SEARCH, middle[0] + SEARCH, middle[1] + SEARCH, middle[1] - SEARCH]
    for ax, (t, pm, best) in zip(axes, maps):
        ax.imshow(pm, cmap="inferno", extent=ext)
        ax.plot(best["x"], best["y"], "o", mfc="none", mec="cyan", ms=12, mew=1.5)
        ax.plot(middle[0], middle[1], "+", color="white", ms=10)
        ax.set_title(f"{t['name']}: best spot ({best['x']:.0f},{best['y']:.0f})\n"
                     f"peak {best['peak']:.3f}", fontsize=9)
        ax.set_xlabel("x of standing spot")
        ax.set_ylabel("y of standing spot")
    fig.suptitle("Peak for every standing spot tried in the original "
                 "(+ = middle, circle = best spot)", fontsize=11)
    plt.tight_layout()
    out_png = os.path.join(OUT_DIR, "step4_search_maps.png")
    plt.savefig(out_png, dpi=110, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_png}")


if __name__ == "__main__":
    main()
