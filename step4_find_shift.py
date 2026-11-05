"""
Step 4 - Find the SHIFT by searching for the right "standing spot" (center).
VERSION 2 = final version (improved after comparing with my friend, see
COMPARISON_WITH_FRIEND.md and IMPROVEMENTS.md). Version 1 is in the git history.

The problem (from Step 3):
  We always unrolled both pictures around their MIDDLE pixel. If the test picture
  was also moved, its middle is a DIFFERENT spot of the city -> no good match.

The fix (the paper's algorithm, slide 11):
  1. Pick a standing spot ("anchor") in the TEST picture and unroll it there. Keep it fixed.
  2. In the ORIGINAL picture, try many standing spots (x, y):
        - unroll the original around (x, y)
        - compare (Step 3) -> best slide + peak (how sure)
  3. The spot with the HIGHEST PEAK shows the same building as the anchor.
  4. From that spot + the rotation + zoom, calculate the shift.

What is NEW in version 2 (old version: search only +-60 px around the middle):
  A. Search the WHOLE original, not only a +-60 px box  (idea from my friend)
     -> big shifts now work.
  B. Rough search on a 4x smaller copy (fast), then exact search at full size.
     (All 16,000 rough spots are computed in batches with scipy's fast Fourier transform.)
  C. Two "judges" make a shortlist in the rough search:
        - cross-correlation (my friend's, like the paper): gentle, not fooled by sky
        - phase correlation (mine): sharp, very exact
     Each judge proposes its 6 best spots. Then the exact full-size phase
     correlation picks the winner from the 12.
  D. Black corners / outside the picture are filled with average gray, so the
     picture's frame does not create fake matches.
  E. Try TWO anchors in the test picture: the middle (old way) and the spot with
     the MOST DETAIL (a middle in empty sky is hard to find). For each answer, put
     the test picture back and check how well it REALLY matches; keep the better one.

How the shift is calculated:
  The test picture was made like this (Step 1):
      test_point = L (original_point - middle) + middle + shift      (L = zoom * rotate)
  The anchor of the test picture came from the best spot in the original, so:
      shift = anchor - middle - L (best_spot - middle)
  (Old version: anchor = middle, so shift = - L (best_spot - middle).)

Output:
  results/step4_results.json     found vs. true values
  results/step4_search_maps.png  rough-search scores over the whole original
"""

import json
import os
import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
import scipy.fft as sfft   # faster Fourier transform for many pictures at once

# ---------------------------------------------------------------
# Settings
# ---------------------------------------------------------------
TRUTH_PATH = "results/test_cases.json"
OUT_DIR = "results"
LP_ROWS = 360       # angle steps (1 row = 1 degree)
LP_COLS = 256       # log-distance steps
RADIUS = 180        # how far we look from the standing spot (pixels)

SHRINK = 4          # rough search: pictures 4x smaller
SMALL_ROWS = 90     # rough search: smaller "clock picture" (1 row = 4 degrees)
SMALL_COLS = 64
SHORTLIST = 6       # each judge proposes this many spots
MID_ROWS = 180      # middle search: half-size clock picture (cheaper),
MID_COLS = 128      #   every pixel +-5 px around each proposed spot
FINE_RANGE = 5
                    # final: full-size clock picture, +-1 px around the best
FRAME = 200         # gray frame around the pictures (px)


def load_gray(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not open {path}")
    return img.astype(np.float32)


# ---------------------------------------------------------------
# Unrolling ("clock picture") and comparing - same as before
# ---------------------------------------------------------------
def log_polar_at(img, center, size=(LP_COLS, LP_ROWS), radius=RADIUS):
    """Unroll the picture around ANY standing spot (center)."""
    return cv2.warpPolar(img, size, center, radius,
                         cv2.INTER_LINEAR + cv2.WARP_FILL_OUTLIERS + cv2.WARP_POLAR_LOG)


WINDOW = np.hanning(LP_COLS)[None, :].astype(np.float32)
SMALL_WINDOW = np.hanning(SMALL_COLS)[None, :].astype(np.float32)
MID_WINDOW = np.hanning(MID_COLS)[None, :].astype(np.float32)


def spectrum(lp):
    """Fourier transform of an unrolled picture (done once per picture, reused)."""
    return np.fft.fft2((lp - lp.mean()) * WINDOW)


def phase_correlation(A, B):
    """Phase correlation from Fourier transforms. Returns (dx, dy, peak)."""
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


def turn_zoom_matrix(angle, scale):
    """OpenCV's rotation (y-axis points down) for a counter-clockwise angle, times zoom."""
    a = np.deg2rad(angle)
    return scale * np.array([[np.cos(a), np.sin(a)],
                             [-np.sin(a), np.cos(a)]])


def shift_from_spot(spot, middle, angle, scale, anchor=None):
    """shift = anchor - middle - L (spot - middle)   (anchor = middle in the old version)"""
    if anchor is None:
        anchor = middle
    L = turn_zoom_matrix(angle, scale)
    d = np.array([spot[0] - middle[0], spot[1] - middle[1]])
    return np.array(anchor) - np.array(middle) - L @ d


def angle_error(found, true):
    return abs((found - true + 180) % 360 - 180)


# ---------------------------------------------------------------
# NEW helpers
# ---------------------------------------------------------------
def add_gray_frame(img, valid):
    """D. Fill black/outside parts with average gray and add a gray frame."""
    gray = float(img[valid].mean())
    out = img.copy()
    out[~valid] = gray
    return cv2.copyMakeBorder(out, FRAME, FRAME, FRAME, FRAME,
                              cv2.BORDER_CONSTANT, value=gray)


def pick_anchor(test):
    """E. The standing spot in the test picture with the most detail.
    Detail = how strong the edges are within 90 px, and we prefer spots whose
    whole look-circle (180 px) is inside the photo (not black)."""
    h, w = test.shape
    valid = (test > 0).astype(np.float32)
    gx = cv2.Sobel(test, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(test, cv2.CV_32F, 0, 1)
    edges = np.sqrt(gx ** 2 + gy ** 2) * cv2.erode(valid, np.ones((5, 5), np.uint8))
    detail = cv2.blur(edges, (181, 181), borderType=cv2.BORDER_CONSTANT)
    inside = cv2.blur(valid, (361, 361), borderType=cv2.BORDER_CONSTANT)
    score = detail * inside ** 2
    m = 100                                   # keep the anchor a bit away from the edge
    sub = score[m:h - m, m:w - m]
    y, x = np.unravel_index(np.argmax(sub), sub.shape)
    return float(x + m), float(y + m)


def rough_scores(original_framed, test_framed, anchor, size):
    """B + C. Rough search on 4x smaller pictures, for EVERY spot of the original.
    Returns two maps: cross-correlation score and phase-correlation score."""
    h, w = size
    small_o = cv2.resize(original_framed, None, fx=1 / SHRINK, fy=1 / SHRINK,
                         interpolation=cv2.INTER_AREA)
    small_t = cv2.resize(test_framed, None, fx=1 / SHRINK, fy=1 / SHRINK,
                         interpolation=cv2.INTER_AREA)
    f = FRAME / SHRINK
    lp_size, r = (SMALL_COLS, SMALL_ROWS), RADIUS / SHRINK

    def prepare(lp):                        # mean 0, size 1, window -> Fourier
        z = (lp - lp.mean(axis=(-2, -1), keepdims=True))
        z /= z.std(axis=(-2, -1), keepdims=True) + 1e-6
        return sfft.rfft2(z * SMALL_WINDOW, workers=-1)

    T = prepare(log_polar_at(small_t, (f + anchor[0] / SHRINK, f + anchor[1] / SHRINK),
                             lp_size, r))
    hs, ws = h // SHRINK, w // SHRINK
    spots = [(x, y) for y in range(hs) for x in range(ws)]
    cross_map = np.zeros(len(spots), np.float32)
    phase_map = np.zeros(len(spots), np.float32)
    batch = 2000                            # do the math for 2000 spots at once (faster)
    for start in range(0, len(spots), batch):
        part = spots[start:start + batch]
        lps = np.stack([log_polar_at(small_o, (f + x + 0.5, f + y + 0.5), lp_size, r)
                        for (x, y) in part])
        prod = np.conj(prepare(lps)) * T
        shape = (SMALL_ROWS, SMALL_COLS)
        cross = sfft.irfft2(prod, s=shape, workers=-1) / (SMALL_ROWS * SMALL_COLS)
        phase = sfft.irfft2(prod / (np.abs(prod) + 1e-9), s=shape, workers=-1)
        cross_map[start:start + len(part)] = cross.max(axis=(1, 2))
        phase_map[start:start + len(part)] = phase.max(axis=(1, 2))
    return cross_map.reshape(hs, ws), phase_map.reshape(hs, ws)


def shortlist(score_map, n=SHORTLIST):
    """The n best spots of a map (not too close to each other), in full-size pixels."""
    m = score_map.copy()
    spots = []
    for _ in range(n):
        y, x = np.unravel_index(np.argmax(m), m.shape)
        spots.append(((x + 0.5) * SHRINK, (y + 0.5) * SHRINK))
        m[max(0, y - 3):y + 4, max(0, x - 3):x + 4] = -np.inf
    return spots


def match_score(original, test, angle, scale, shift):
    """How well do the pictures REALLY match with these numbers?
    Put the test picture back (like Step 5) and compare brightness patterns
    on the visible part: 1 = perfect, 0 = no match (normalized correlation)."""
    h, w = original.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    m[:, 2] += shift
    back = cv2.warpAffine(test, m, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    seen = cv2.warpAffine((test > 0).astype(np.uint8), m, (w, h),
                          flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP) > 0
    if seen.sum() < 1000:
        return 0.0
    a, b = original[seen] - original[seen].mean(), back[seen] - back[seen].mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


def search_from_anchor(original_framed, test_framed, anchor, size):
    """Rough search (2 judges) + exact search for ONE anchor of the test picture."""
    h, w = size
    middle = (w / 2, h / 2)
    cross_map, phase_map = rough_scores(original_framed, test_framed, anchor, size)
    candidates = []
    for c in shortlist(cross_map) + shortlist(phase_map):    # drop spots proposed twice
        if all(np.hypot(c[0] - d[0], c[1] - d[1]) > 6 for d in candidates):
            candidates.append(c)
    B_test = spectrum(log_polar_at(test_framed, (FRAME + anchor[0], FRAME + anchor[1])))
    # middle search: half-size clock pictures, every pixel near each proposed spot
    mid_size = (MID_COLS, MID_ROWS)
    a = (FRAME + anchor[0], FRAME + anchor[1])
    B_mid = np.fft.fft2((lambda l: (l - l.mean()) * MID_WINDOW)(
        log_polar_at(test_framed, a, mid_size)))
    best_mid = (-1.0, None)
    for (cx, cy) in candidates:
        for oy in range(-FINE_RANGE, FINE_RANGE + 1):
            for ox in range(-FINE_RANGE, FINE_RANGE + 1):
                x, y = FRAME + cx + ox, FRAME + cy + oy
                lp = log_polar_at(original_framed, (x, y), mid_size)
                _, _, peak = phase_correlation(np.fft.fft2((lp - lp.mean()) * MID_WINDOW), B_mid)
                if peak > best_mid[0]:
                    best_mid = (peak, (x, y))
    # final: full-size clock picture, +-1 px around the best
    bx, by = best_mid[1]
    finest = [(bx + ox, by + oy) for oy in (-1, 0, 1) for ox in (-1, 0, 1)]
    best, _ = search(original_framed, B_test, finest)
    spot = (best["x"] - FRAME, best["y"] - FRAME)
    angle, scale = slide_to_rotation_scale(best["dx"], best["dy"])
    shift = shift_from_spot(spot, middle, angle, scale, anchor)
    return {"angle": angle, "scale": scale, "shift": shift, "spot": spot,
            "anchor": anchor, "peak": best["peak"], "candidates": candidates,
            "cross_map": cross_map, "phase_map": phase_map}


def find_turn_zoom_shift(original, test):
    """The whole improved Step 4 for one test picture.
    E. Try 2 anchors (the middle, and the most detailed spot), then keep the
    answer whose put-back picture REALLY matches the original best."""
    h, w = original.shape
    O = add_gray_frame(original, np.ones(original.shape, bool))
    T = add_gray_frame(test, test > 0)
    anchors = [(w / 2, h / 2)]
    detailed = pick_anchor(test)
    if np.hypot(detailed[0] - w / 2, detailed[1] - h / 2) > 3:
        anchors.append(detailed)
    best = None
    for anchor in anchors:
        r = search_from_anchor(O, T, anchor, (h, w))
        r["match"] = match_score(original, test, r["angle"], r["scale"], r["shift"])
        if best is None or r["match"] > best["match"]:
            best = r
    return best


def main():
    with open(TRUTH_PATH) as f:
        truth = json.load(f)

    original = load_gray(truth["original"])
    h, w = original.shape
    print(f"Picture {w} x {h}, look radius {RADIUS} px")
    print(f"Search: WHOLE picture (rough on {SHRINK}x smaller copy, 2 judges x {SHORTLIST} spots, "
          f"then exact +-{FINE_RANGE} px, 2 anchors)\n")

    header = (f"{'test':6} {'anchor':>12} {'spot found':>12} {'peak':>6} | {'angle':>8} {'true':>5} {'err':>6} | "
              f"{'zoom':>7} {'true':>5} {'err':>6} | {'shift found':>15} {'true':>11} {'err':>6} | verdict")
    print(header)
    print("-" * len(header))

    results, maps = [], []
    for t in truth["tests"]:
        start = time.time()
        test = load_gray(t["file"])
        r = find_turn_zoom_shift(original, test)
        angle, scale, shift = r["angle"], r["scale"], r["shift"]

        true_angle = (t["angle"] + 180) % 360 - 180
        a_err = angle_error(angle, true_angle)
        s_err = abs(scale - t["scale"]) / t["scale"] * 100
        sh_err = float(np.hypot(shift[0] - t["shift_x"], shift[1] - t["shift_y"]))
        ok = a_err < 1.0 and s_err < 2.0 and sh_err < 3.0
        secs = time.time() - start

        print(f"{t['name']:6} ({r['anchor'][0]:4.0f},{r['anchor'][1]:4.0f}) "
              f"({r['spot'][0]:4.0f},{r['spot'][1]:4.0f}) {r['peak']:6.3f} | "
              f"{angle:7.2f}° {true_angle:4.0f}° {a_err:5.2f}° | "
              f"{scale:6.3f}x {t['scale']:4.2f}x {s_err:5.2f}% | "
              f"({shift[0]:6.1f},{shift[1]:6.1f}) ({t['shift_x']:4},{t['shift_y']:4}) {sh_err:5.1f}px | "
              f"{'CORRECT' if ok else 'WRONG'}  ({secs:.1f}s)")

        results.append({"name": t["name"],
                        "anchor_in_test": [round(r["anchor"][0], 1), round(r["anchor"][1], 1)],
                        "spot_found": [float(r["spot"][0]), float(r["spot"][1])],
                        "peak": round(r["peak"], 4), "match": round(r["match"], 4),
                        "angle_found": round(angle, 3), "angle_true": true_angle,
                        "angle_error_deg": round(a_err, 3),
                        "scale_found": round(scale, 4), "scale_true": t["scale"],
                        "scale_error_percent": round(s_err, 3),
                        "shift_found": [round(float(shift[0]), 2), round(float(shift[1]), 2)],
                        "shift_true": [t["shift_x"], t["shift_y"]],
                        "shift_error_px": round(sh_err, 2),
                        "correct": bool(ok), "seconds": round(secs, 2)})
        maps.append((t, r))

    out_json = os.path.join(OUT_DIR, "step4_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {out_json}")

    # ---- Figure: rough-search scores over the whole original (2 judges) ----
    n = len(maps)
    fig, axes = plt.subplots(2, n, figsize=(2.6 * n, 8))
    ext = [0, w, h, 0]
    for i, (t, r) in enumerate(maps):
        for j, (key, label) in enumerate([("cross_map", "cross-correlation (like the paper)"),
                                          ("phase_map", "phase correlation")]):
            ax = axes[j, i]
            ax.imshow(r[key], cmap="inferno", extent=ext)
            ax.plot(r["spot"][0], r["spot"][1], "o", mfc="none", mec="cyan", ms=12, mew=2)
            ax.set_title(f"{t['name']}\n{label}", fontsize=9)
            ax.set_xticks([])
            ax.set_yticks([])
    fig.suptitle("Rough search over the WHOLE original: bright = good match\n"
                 "(cyan circle = final best spot after the exact search)", fontsize=11)
    plt.tight_layout(h_pad=2.5)
    out_png = os.path.join(OUT_DIR, "step4_search_maps.png")
    plt.savefig(out_png, dpi=110, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_png}")


if __name__ == "__main__":
    main()
