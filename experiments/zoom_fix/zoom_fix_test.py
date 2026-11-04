"""
EXPERIMENT (not part of the main method) - Can we fix big zoom in and zoom out?

The main method (step4_find_shift.py) works for zoom x0.5 - x3 (see step8_zoom_limits.py).
This file tries two fixes WITHOUT changing the main files:

FIX 1 - zoom in x4 and more: "zoom guesses" in the rough search
  Problem: the rough search makes BOTH photos 4x smaller. At zoom x4 the piece of the city
  that the test photo shows becomes only ~3 pixels in the small original -> unrecognisable.
  Fix: also try making the TEST photo smaller than the original (zoom guesses x2, x4, x8):
  test photo 8x / 16x / 32x smaller, original still 4x smaller. Then both show the city at
  about the SAME size again, so the rough search can recognise it.
  All guesses put spots on the short list; the exact full-size search decides (as before).

FIX 2 - zoom out (x0.5 and less): swap the two photos
  Zoom out = zoom in the other way round (the paper's 0.469 example is exactly this).
  So we also search for the ORIGINAL inside the TEST photo, then turn the answer around.

At the end, every answer is put back and checked ("really matches?", like Step 4 version 2);
the best one wins. Then the optimizer (Step 6) as usual.

Run from the main folder:   python experiments/zoom_fix/zoom_fix_test.py
Output (in experiments/zoom_fix/):  zoom_fix_results.json, zoom_fix_compare.png, why_zoom_fails.png
"""
import json
import os
import sys
import time

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.fft as sfft

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import step4_find_shift as s4          # main method (NOT changed)
import step6_optimizer as s6
import step7_hard_tests as s7

ZOOM_GUESSES = [1, 2, 4, 8]             # FIX 1
ZOOMS = [0.25, 0.35, 0.5, 0.75, 2, 3, 4, 5, 6, 8, 10]
GOOD = 0.1


# ---------------------------------------------------------------------------
# FIX 1: rough search with a zoom guess (test photo shrunk more than the original)
# ---------------------------------------------------------------------------
def rough_scores_guess(O, T, anchor, size, guess):
    """Like s4.rough_scores, but the test photo is made `guess` times smaller extra."""
    h, w = size
    k_o, k_t = s4.SHRINK, s4.SHRINK * guess
    small_o = cv2.resize(O, None, fx=1 / k_o, fy=1 / k_o, interpolation=cv2.INTER_AREA)
    small_t = cv2.resize(T, None, fx=1 / k_t, fy=1 / k_t, interpolation=cv2.INTER_AREA)
    lp_size, r = (s4.SMALL_COLS, s4.SMALL_ROWS), s4.RADIUS / s4.SHRINK

    def prepare(lp):
        z = lp - lp.mean(axis=(-2, -1), keepdims=True)
        z /= z.std(axis=(-2, -1), keepdims=True) + 1e-6
        return sfft.rfft2(z * s4.SMALL_WINDOW, workers=-1)

    T_spec = prepare(s4.log_polar_at(small_t, ((s4.FRAME + anchor[0]) / k_t,
                                               (s4.FRAME + anchor[1]) / k_t), lp_size, r))
    hs, ws = h // k_o, w // k_o
    f = s4.FRAME / k_o
    spots = [(x, y) for y in range(hs) for x in range(ws)]
    cross_map = np.zeros(len(spots), np.float32)
    phase_map = np.zeros(len(spots), np.float32)
    for start in range(0, len(spots), 2000):
        part = spots[start:start + 2000]
        lps = np.stack([s4.log_polar_at(small_o, (f + x + 0.5, f + y + 0.5), lp_size, r)
                        for (x, y) in part])
        prod = np.conj(prepare(lps)) * T_spec
        shape = (s4.SMALL_ROWS, s4.SMALL_COLS)
        cross_map[start:start + len(part)] = (sfft.irfft2(prod, s=shape, workers=-1)
                                              .max(axis=(1, 2)) / (shape[0] * shape[1]))
        phase_map[start:start + len(part)] = sfft.irfft2(prod / (np.abs(prod) + 1e-9), s=shape,
                                                         workers=-1).max(axis=(1, 2))
    return cross_map.reshape(hs, ws), phase_map.reshape(hs, ws)


def exact_search(O, T, anchor, size, candidates):
    """Same middle + final search as s4.search_from_anchor, for a given short list."""
    h, w = size
    middle = (w / 2, h / 2)
    mid_size = (s4.MID_COLS, s4.MID_ROWS)
    a = (s4.FRAME + anchor[0], s4.FRAME + anchor[1])
    prep = lambda l: np.fft.fft2((l - l.mean()) * s4.MID_WINDOW)
    B_mid = prep(s4.log_polar_at(T, a, mid_size))
    best_mid = (-1.0, None)
    for (cx, cy) in candidates:
        for oy in range(-s4.FINE_RANGE, s4.FINE_RANGE + 1):
            for ox in range(-s4.FINE_RANGE, s4.FINE_RANGE + 1):
                x, y = s4.FRAME + cx + ox, s4.FRAME + cy + oy
                _, _, peak = s4.phase_correlation(prep(s4.log_polar_at(O, (x, y), mid_size)), B_mid)
                if peak > best_mid[0]:
                    best_mid = (peak, (x, y))
    bx, by = best_mid[1]
    B_full = s4.spectrum(s4.log_polar_at(T, a))
    best, _ = s4.search(O, B_full, [(bx + ox, by + oy) for oy in (-1, 0, 1) for ox in (-1, 0, 1)])
    spot = (best["x"] - s4.FRAME, best["y"] - s4.FRAME)
    angle, scale = s4.slide_to_rotation_scale(best["dx"], best["dy"])
    shift = s4.shift_from_spot(spot, middle, angle, scale, anchor)
    return s6.make_matrix(w, h, angle, scale, shift[0], shift[1])


def one_direction(A, B):
    """Find the matrix A -> B (B should show a ZOOMED-IN part of A). Tries 2 anchors in B
    and all zoom guesses. Returns a list of candidate matrices."""
    h, w = A.shape
    O = s4.add_gray_frame(A, A > 0)
    T = s4.add_gray_frame(B, B > 0)
    anchors = [(w / 2, h / 2), s4.pick_anchor(B)]
    answers = []
    for anchor in anchors:
        cands = []
        for g in ZOOM_GUESSES:
            cm, pm = rough_scores_guess(O, T, anchor, (h, w), g)
            for c in s4.shortlist(cm) + s4.shortlist(pm):
                if all(np.hypot(c[0] - d[0], c[1] - d[1]) > 6 for d in cands):
                    cands.append(c)
        answers.append(exact_search(O, T, anchor, (h, w), cands))
    return answers


def match(original, test, m):
    """How well does the put-back test photo REALLY match? (1 = perfect)"""
    h, w = original.shape
    back = cv2.warpAffine(test, m, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    seen = cv2.warpAffine((test > 0).astype(np.uint8), m, (w, h),
                          flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP) > 0
    seen &= original > 0
    if seen.sum() < 1000:
        return -1.0
    a, b = original[seen] - original[seen].mean(), back[seen] - back[seen].mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


def fixed_method(original, test):
    """FIX 1 + FIX 2. Returns the matrix after the optimizer and the time."""
    start = time.time()
    answers = one_direction(original, test)                                 # zoom in
    answers += [cv2.invertAffineTransform(m) for m in one_direction(test, original)]  # FIX 2
    best = max(answers, key=lambda m: match(original, test, m))
    m6, _ = s6.optimize(original, test, best)
    return best, m6, time.time() - start


def main_method(original, test):
    h, w = original.shape
    start = time.time()
    r = s4.find_turn_zoom_shift(original, test)
    m4 = s6.make_matrix(w, h, r["angle"], r["scale"], r["shift"][0], r["shift"][1])
    m6, _ = s6.optimize(original, test, m4)
    return m4, m6, time.time() - start


def why_picture(original):
    """Simple picture: why zoom x4 / x8 / x0.25 is hard."""
    h, w = original.shape
    cx, cy = w / 2 + 20, h / 2 - 15
    t4, _ = s7.make_hard_test(original, 0, 4, (20, -15), s7.NO_STRETCH)
    t8, _ = s7.make_hard_test(original, 0, 8, (20, -15), s7.NO_STRETCH)
    t025, _ = s7.make_hard_test(original, 0, 0.25, (20, -15), s7.NO_STRETCH)
    r = s4.RADIUS / 4                                  # test look-circle (180 px) at zoom x4
    full = original[int(cy - r):int(cy + r), int(cx - r):int(cx + r)]
    small = cv2.resize(full, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    fig, ax = plt.subplots(1, 5, figsize=(17, 4.6))
    ax[0].imshow(original, cmap="gray")
    ax[0].add_patch(plt.Circle((cx, cy), r, fill=False, ec="#eb6834", lw=2.5))
    ax[0].set_title("1. Original: the orange circle is all\nthe test photo shows at zoom x4", fontsize=9)
    ax[1].imshow(full, cmap="gray")
    ax[1].set_title("2. That piece at FULL size\n(90 x 90 px: recognisable)", fontsize=9)
    ax[2].imshow(small, cmap="gray", interpolation="nearest")
    ax[2].set_title(f"3. Same piece in the 4x smaller copy\nused by the rough search ({small.shape[1]} x {small.shape[0]} px!)",
                    fontsize=9)
    ax[3].imshow(t8, cmap="gray", vmin=0, vmax=255)
    ax[3].set_title("4. Test photo at zoom x8:\na tiny piece blown up = very blurry", fontsize=9)
    ax[4].imshow(t025, cmap="gray", vmin=0, vmax=255)
    ax[4].set_title("5. Test photo at zoom x0.25:\n94% black, the city is tiny", fontsize=9)
    for a in ax:
        a.axis("off")
    fig.suptitle("Why big zoom in and big zoom out fail in the main method", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "why_zoom_fails.png"), dpi=120, bbox_inches="tight")
    plt.close()


def main():
    original = s4.load_gray("images/original.jpg")
    why_picture(original)
    print("Saved experiments/zoom_fix/why_zoom_fails.png\n")
    print(f"{'zoom':>5} | {'MAIN method (px off)':>21} | {'FIXED method (px off)':>22} | {'time main/fixed':>15}")
    print("-" * 75)
    rows = []
    for z in ZOOMS:
        test, m_true = s7.make_hard_test(original, 40, z, (20, -15), s7.NO_STRETCH)
        _, m6a, ta = main_method(original, test)
        _, m6b, tb = fixed_method(original, test)
        a, b = s6.pixels_off(m6a, m_true, test), s6.pixels_off(m6b, m_true, test)
        mark = lambda v: "OK " if v < GOOD else "BAD"
        print(f"{z:5} | {a:15.3f} {mark(a)}   | {b:16.3f} {mark(b)}   | {ta:5.0f}s / {tb:4.0f}s", flush=True)
        rows.append({"zoom": z, "main_pixels_off": round(a, 4), "fixed_pixels_off": round(b, 4),
                     "main_seconds": round(ta, 1), "fixed_seconds": round(tb, 1)})
    with open(os.path.join(HERE, "zoom_fix_results.json"), "w") as f:
        json.dump(rows, f, indent=2)
    compare_figure(rows)
    print("\nSaved experiments/zoom_fix/zoom_fix_results.json and zoom_fix_compare.png")


def compare_figure(rows):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(rows))
    ax.bar(x - 0.2, [max(r["main_pixels_off"], 1e-3) for r in rows], 0.38, color="#8a8a8a",
           label="main method (now)")
    ax.bar(x + 0.2, [max(r["fixed_pixels_off"], 1e-3) for r in rows], 0.38, color="#2a78d6",
           label="experiment (zoom guesses + swap)")
    ax.set_yscale("log")
    ax.axhline(GOOD, color="#2e7d32", ls="--", lw=1.2)
    ax.text(2.6, GOOD * 1.3, "0.1 px = practically perfect", color="#2e7d32", fontsize=9)
    ax.set_xticks(x, [f"x{r['zoom']}" for r in rows])
    ax.set_xlabel("zoom (less than 1 = zoom out)")
    ax.set_ylabel("pixels off after optimizer\n(log scale, lower = better)")
    ax.legend(frameon=False, loc="upper center")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Zoom experiment: main method vs fixed experiment", fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "zoom_fix_compare.png"), dpi=130, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
