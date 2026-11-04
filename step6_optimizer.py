"""
Step 6 (bonus) - The optimizer: fine-tune the numbers so the photos line up even better.

Simple idea (from the paper, Section 3):
  Step 4 gives a GOOD first guess (turn, zoom, shift), but a little bit off
  (test4: zoom x1.96 instead of x2.00).
  The optimizer turns 6 "knobs" a tiny bit at a time and keeps the change if
  the photos match better. It stops when no change helps any more.

The 6 knobs (the paper's a1..a6):
      new_x = a1*x + a2*y + a3
      new_y = a4*x + a5*y + a6
  They can describe turn, zoom, shift AND slant (shear), so the optimizer can
  also fix small slanting errors that Step 4 cannot describe.

How "match better" is measured (the paper's SSD):
  For every pixel: (original brightness - fixed test brightness)^2, then add them all up.
  Smaller = better match. 0 = perfect.

The method that turns the knobs is Levenberg-Marquardt (same as the paper),
from scipy: least_squares(method="lm").

Like walking blindfolded downhill: feel which way is down, take a small step,
repeat. It only works if you START close to the bottom - that is why we need
Step 4 first (the paper's main point).

Output:
  results/step6_results.json     numbers before and after the optimizer
  results/step6_compare.png      overlay after Step 4 vs. after Step 6 (zoomed in)
"""

import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares

TRUTH_PATH = "results/test_cases.json"
FOUND_PATH = "results/step4_results.json"
OUT_DIR = "results"
BLUR_STEPS = [4.0, 2.0, 1.0, 0.5]   # first match VERY blurry photos (easier), then sharper ones
                                   # (version 2: idea from my friend; old version was [2.0, 1.0])
OLD_BLUR_STEPS = [2.0, 1.0]
EDGE_MARGIN = 6           # ignore pixels this close to the edge of the test photo


def make_matrix(width, height, angle, scale, shift_x, shift_y):
    """Same recipe as Step 1 (original -> test)."""
    m = cv2.getRotationMatrix2D((width / 2, height / 2), angle, scale)
    m[0, 2] += shift_x
    m[1, 2] += shift_y
    return m


def undo(img, m, width, height):
    """Put the test photo back (same as Step 5)."""
    return cv2.warpAffine(img, m, (width, height),
                          flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def visible_mask(test, m, width, height):
    """Pixels of the fixed photo that really come from the test photo
    (minus a small safety margin at the edges)."""
    inside = (test > 0).astype(np.uint8) * 255
    # BORDER_CONSTANT: also trim the outer frame of the photo (not only black areas)
    inside = cv2.erode(inside, np.ones((3, 3), np.uint8), iterations=EDGE_MARGIN,
                       borderType=cv2.BORDER_CONSTANT, borderValue=0)
    back = cv2.warpAffine(inside, m, (width, height),
                          flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return back > 0


def ssd(original, test, m, mask):
    """The paper's SSD: sum of (difference)^2 over the visible pixels (shown as average)."""
    h, w = original.shape
    d = undo(test, m, w, h)[mask] - original[mask]
    return float(np.mean(d ** 2))


def sample(test, m, xs, ys):
    """Exact brightness of the fixed photo at pixels (xs, ys).
    We do NOT use cv2.warpAffine here: it rounds positions to 1/32 pixel, so the
    optimizer's tiny test-steps would see no change at all (we found this bug!)."""
    tx = m[0, 0] * xs + m[0, 1] * ys + m[0, 2]
    ty = m[1, 0] * xs + m[1, 1] * ys + m[1, 2]
    return map_coordinates(test, [ty, tx], order=1, mode="constant", cval=0.0)


def optimize(original, test, m_start, blur_steps=None):
    """Turn the 6 knobs (Levenberg-Marquardt) to make SSD as small as possible."""
    h, w = original.shape
    m = m_start.copy()
    total_steps = 0
    for sigma in (blur_steps or BLUR_STEPS):
        o = cv2.GaussianBlur(original, (0, 0), sigma)
        t = cv2.GaussianBlur(test, (0, 0), sigma)
        ys, xs = np.nonzero(visible_mask(test, m, w, h))
        xs, ys = xs.astype(np.float64), ys.astype(np.float64)
        target = o[ys.astype(int), xs.astype(int)]

        # knobs are stored as CHANGES from the current matrix, scaled so that
        # 1 unit of each knob moves the picture by about 1 pixel
        base = m.copy()
        size = np.array([w / 2, h / 2, 1.0, w / 2, h / 2, 1.0])

        def residuals(knobs):
            mm = base + (knobs / size).reshape(2, 3)
            return sample(t, mm, xs, ys) - target

        res = least_squares(residuals, np.zeros(6), method="lm",
                            x_scale=np.ones(6), diff_step=1e-4)
        m = base + (res.x / size).reshape(2, 3)
        total_steps += res.nfev
    return m, total_steps


def pixels_off(m_found, m_true, test):
    """Average distance (in original-photo pixels) between where each visible
    pixel lands with our numbers and where it should land (same as Step 5)."""
    inv_f = cv2.invertAffineTransform(m_found)
    inv_t = cv2.invertAffineTransform(m_true)
    ys, xs = np.nonzero(test > 0)
    pts = np.stack([xs, ys, np.ones(xs.size)]).astype(np.float64)
    return float(np.linalg.norm(inv_f @ pts - inv_t @ pts, axis=0).mean())


def describe(m):
    """Read turn and zoom back out of a matrix (for printing)."""
    zoom = np.sqrt(abs(np.linalg.det(m[:, :2])))
    angle = np.degrees(np.arctan2(m[0, 1], m[0, 0]))
    return angle, zoom


def main():
    with open(TRUTH_PATH) as f:
        truth = json.load(f)
    with open(FOUND_PATH) as f:
        found = {r["name"]: r for r in json.load(f)}

    original = cv2.imread(truth["original"], cv2.IMREAD_GRAYSCALE).astype(np.float64)
    h, w = original.shape

    print(f"{'test':6} | {'pixels off':>21} | {'SSD (difference^2)':>21} | "
          f"{'zoom':>17} {'true':>5} | {'angle':>17} {'true':>5} | steps")
    print(f"{'':6} | {'Step 4':>10} {'Step 6':>10} | {'Step 4':>10} {'Step 6':>10} | "
          f"{'Step 4':>8} {'Step 6':>8} {'':>5} | {'Step 4':>8} {'Step 6':>8} {'':>5} |")
    print("-" * 118)

    results, rows = [], []
    for t in truth["tests"]:
        r = found[t["name"]]
        test = cv2.imread(t["file"], cv2.IMREAD_GRAYSCALE).astype(np.float64)

        m4 = make_matrix(w, h, r["angle_found"], r["scale_found"], *r["shift_found"])
        m_true = make_matrix(w, h, t["angle"], t["scale"], t["shift_x"], t["shift_y"])
        m6, steps = optimize(original, test, m4)

        mask = visible_mask(test, m_true, w, h)
        off4, off6 = pixels_off(m4, m_true, test), pixels_off(m6, m_true, test)
        ssd4, ssd6 = ssd(original, test, m4, mask), ssd(original, test, m6, mask)
        a4, z4 = describe(m4)
        a6, z6 = describe(m6)

        print(f"{t['name']:6} | {off4:8.2f}px {off6:8.2f}px | {ssd4:10.1f} {ssd6:10.1f} | "
              f"{z4:7.4f}x {z6:7.4f}x {t['scale']:4.2f}x | "
              f"{a4:7.2f}° {a6:7.2f}° {t['angle']:4}° | {steps}")

        # the paper's check: how big was the correction? (close to "do nothing" = good first guess)
        m4_full = np.vstack([m4, [0, 0, 1]])
        m6_full = np.vstack([m6, [0, 0, 1]])
        correction = (m6_full @ np.linalg.inv(m4_full))[:2]

        results.append({"name": t["name"],
                        "pixels_off_step4": round(off4, 3), "pixels_off_step6": round(off6, 3),
                        "ssd_step4": round(ssd4, 2), "ssd_step6": round(ssd6, 2),
                        "zoom_step4": round(z4, 4), "zoom_step6": round(z6, 4), "zoom_true": t["scale"],
                        "angle_step4": round(a4, 3), "angle_step6": round(a6, 3), "angle_true": t["angle"],
                        "knobs_a1_to_a6_step6": m6.round(5).ravel().tolist(),
                        "correction_matrix": correction.round(4).tolist(),
                        "optimizer_steps": steps})
        rows.append((t, test, m4, m6, off4, off6))

    print("\nCorrection made by the optimizer (paper: should be close to 'do nothing' = 1 0 0 / 0 1 0):")
    for res in results:
        c = res["correction_matrix"]
        print(f"  {res['name']}:  [{c[0][0]:.4f} {c[0][1]:+.4f} {c[0][2]:+.2f}]   "
              f"[{c[1][0]:+.4f} {c[1][1]:.4f} {c[1][2]:+.2f}]")

    with open(os.path.join(OUT_DIR, "step6_results.json"), "w") as fp:
        json.dump(results, fp, indent=2)
    print("\nSaved results/step6_results.json")

    # ---- Figure: zoom in on a corner of the overlay, Step 4 vs Step 6 ----
    n = len(rows)
    fig, axes = plt.subplots(n, 2, figsize=(7, 3.4 * n))
    o8 = original.astype(np.uint8)
    for i, (t, test, m4, m6, off4, off6) in enumerate(rows):
        mask = visible_mask(test, m6, w, h)
        ys, xs = np.nonzero(mask)
        # zoom into the part of the visible area that is farthest from the middle
        far = np.argmax((xs - w / 2) ** 2 + (ys - h / 2) ** 2)
        cx, cy = int(0.8 * xs[far] + 0.2 * w / 2), int(0.8 * ys[far] + 0.2 * h / 2)
        y0, y1 = max(cy - 60, 0), min(cy + 60, h)
        x0, x1 = max(cx - 60, 0), min(cx + 60, w)
        for j, (m, off, label) in enumerate([(m4, off4, "after Step 4"), (m6, off6, "after Step 6")]):
            fixed = undo(test, m, w, h).astype(np.uint8)
            overlay = np.dstack([o8, fixed, fixed])[y0:y1, x0:x1]
            axes[i, j].imshow(overlay, interpolation="nearest")
            axes[i, j].set_title(f"{t['name']} {label}: {off:.2f} px off", fontsize=9)
            axes[i, j].axis("off")
    fig.suptitle("Zoomed into the edge of the overlay (red = original, cyan = test)\n"
                 "fewer red/cyan edges = better", fontsize=11, y=1.01)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "step6_compare.png")
    plt.savefig(out, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
