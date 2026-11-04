"""
Step 8 - Compare my method with my friend's method on the SAME pictures.

Part A: run my FRIEND's code (friend_version/registration.py) on MY 5 test photos.
        -> Does their method find the right turn, zoom and shift? How fast?
("My code" here = my OLD version 1. Step 9 tests the improved version 2.)
Part B: run MY code (Step 4 + Step 6) on a FRIEND-STYLE test:
        a big shift (the middle of the test photo is far from the middle of the
        original) + a small "stretch" (shear) like in the paper's Fig. 3.
        -> Does my method still work when the shift is big?

Both methods use the same "pixels off" score as Step 5/6:
on average, how many pixels each visible point lands away from the right place.
"""
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, os.path.join(HERE, "friend_version"))

import registration as friend                            # friend's method
import step4_find_shift as my4                           # my Step 4
import step6_optimizer as my6                            # my Step 6

TRUTH_PATH = "results/test_cases.json"
OUT_PATH = "results/step8_comparison.json"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def pixels_off(m_found, m_true, test):
    """Same score as Step 6: average distance (original-photo pixels)."""
    return my6.pixels_off(np.asarray(m_found, float), np.asarray(m_true, float), test)


def read_matrix(m, width, height):
    """Turn a 2x3 matrix into MY words: turn (counter-clockwise), zoom, shift."""
    scale = float(np.hypot(m[0, 0], m[0, 1]))
    angle = float(np.degrees(np.arctan2(m[0, 1], m[0, 0])))
    center = np.array([width / 2, height / 2])
    shift = m[:, 2] - (center - m[:, :2] @ center)
    return angle, scale, shift


def angle_err(a, b):
    return abs((a - b + 180) % 360 - 180)


def my_method(original, test):
    """My OLD method (version 1, before the improvements of Step 9):
    Step 4 search only +-60 px around the middle + Step 6 with blur 2 -> 1.
    Kept fixed so the numbers in COMPARISON_WITH_FRIEND.md stay true."""
    h, w = original.shape
    start = time.time()
    r = my4.find_turn_zoom_shift_OLD(original, test)
    m4 = my6.make_matrix(w, h, r["angle"], r["scale"], r["shift"][0], r["shift"][1])
    t4 = time.time() - start
    start = time.time()
    m6, _ = my6.optimize(original, test, m4, blur_steps=my6.OLD_BLUR_STEPS)
    t6 = time.time() - start
    return m4, t4, m6, t6, r["peak"]


def friend_method(original, test):
    """Friend's log-polar search (slide 11) + their Levenberg-Marquardt."""
    lp = friend.register_logpolar(original.astype(float), test.astype(float))
    lm = friend.refine_affine_lm(original.astype(float), test.astype(float), lp["A"])
    return lp["A"], lp["seconds"], lm["A"], lm["seconds"], lp["score"]


# ---------------------------------------------------------------------------
# Part A: friend's method on my 5 test photos
# ---------------------------------------------------------------------------
def part_a(truth, original):
    h, w = original.shape
    print("PART A - FRIEND's method on MY 5 test photos")
    print(f"{'test':6} | {'turn found':>10} {'true':>5} | {'zoom':>6} {'true':>5} | "
          f"{'shift found':>14} {'true':>10} | {'px off (log-polar)':>18} {'px off (+LM)':>12} | time")
    print("-" * 112)
    rows = []
    for t in truth["tests"]:
        test = cv2.imread(t["file"], cv2.IMREAD_GRAYSCALE).astype(np.float32)
        m_true = np.array(t["matrix"])
        A1, s1, A2, s2, score = friend_method(original, test)
        angle, scale, shift = read_matrix(A1, w, h)
        off1, off2 = pixels_off(A1, m_true, test), pixels_off(A2, m_true, test)
        print(f"{t['name']:6} | {angle % 360:9.2f}° {t['angle']:4}° | {scale:5.3f}x {t['scale']:4.2f}x | "
              f"({shift[0]:6.1f},{shift[1]:6.1f}) ({t['shift_x']:3},{t['shift_y']:3}) | "
              f"{off1:18.2f} {off2:12.3f} | {s1:.1f}s + {s2:.1f}s")
        rows.append({"name": t["name"], "angle_found": round(angle % 360, 2),
                     "scale_found": round(scale, 4),
                     "shift_found": [round(float(shift[0]), 2), round(float(shift[1]), 2)],
                     "angle_error_deg": round(angle_err(angle, t["angle"]), 3),
                     "pixels_off_logpolar": round(off1, 3), "pixels_off_lm": round(off2, 3),
                     "score": round(float(score), 3),
                     "seconds_logpolar": round(s1, 2), "seconds_lm": round(s2, 2)})
    return rows


# ---------------------------------------------------------------------------
# Part B: my method on friend-style tests (big shift + small stretch)
# ---------------------------------------------------------------------------
def make_friend_style(original, angle, scale, spot_offset, stretch):
    """Like the friend's / paper Fig. 3 test: the point `middle + spot_offset`
    of the original becomes the MIDDLE of the test photo (so a big offset = a
    big shift), turned + zoomed, plus a small stretch matrix. A little noise too."""
    h, w = original.shape
    middle = np.array([w / 2, h / 2])
    rot = cv2.getRotationMatrix2D((0, 0), angle, scale)[:, :2]   # my convention
    L = np.array(stretch) @ rot
    spot = middle + np.array(spot_offset)
    m = np.hstack([L, (middle - L @ spot)[:, None]])
    test = cv2.warpAffine(original, m, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rng = np.random.default_rng(1)
    inside = test > 0
    test = np.where(inside, np.clip(test + rng.normal(0, 2.0, test.shape), 1, 255), 0)
    return test.astype(np.float32), m


def part_b(original):
    paper_stretch = [[1.008, 0.006], [0.003, 1.045]]       # from the paper / friend
    cases = [
        ("B1 small shift",   -201, 2.13, (40, -30),   paper_stretch),
        ("B2 big shift",     -201, 2.13, (70, 80),   paper_stretch),
        ("B3 big shift",     -201, 2.13, (0, -100),  paper_stretch),
    ]
    print("\nPART B - MY method vs FRIEND's method on friend-style tests "
          "(turn 201° the other way, zoom 2.13, + stretch)")
    print(f"{'case':16} | {'method':7} | {'px off (log-polar)':>18} {'px off (+LM)':>12} | time")
    print("-" * 75)
    rows = []
    for name, angle, scale, offset, stretch in cases:
        test, m_true = make_friend_style(original, angle, scale, offset, stretch)
        cv2.imwrite(f"images/generated/{name.split()[0]}_friend_style.png", test.astype(np.uint8))
        for label, fn in [("mine", my_method), ("friend", friend_method)]:
            A1, s1, A2, s2, _ = fn(original, test)
            off1, off2 = pixels_off(A1, m_true, test), pixels_off(A2, m_true, test)
            print(f"{name:16} | {label:7} | {off1:18.2f} {off2:12.3f} | {s1:.1f}s + {s2:.1f}s")
            rows.append({"case": name, "method": label, "spot_offset": list(offset),
                         "pixels_off_logpolar": round(off1, 3), "pixels_off_lm": round(off2, 3),
                         "seconds_logpolar": round(s1, 2), "seconds_lm": round(s2, 2)})
    return rows


MINE_COLOR, FRIEND_COLOR = "#2a78d6", "#eb6834"     # blue = me, orange = friend


def make_figure(original, a, b):
    """One picture for the report:
    left  = WHERE each method can search (why my method fails on a big shift)
    middle = Part A: pixels off on my 5 tests, BEFORE the optimizer
    right  = Part B: pixels off on friend-style tests, AFTER the optimizer."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    with open("results/step6_results.json") as f:
        mine6 = {r["name"]: r for r in json.load(f)}
    h, w = original.shape
    mid = (w / 2, h / 2)
    fig, ax = plt.subplots(1, 3, figsize=(16, 5.6),
                           gridspec_kw={"width_ratios": [0.8, 1.2, 1.2]})

    # 1) where the methods look
    ax[0].imshow(original, cmap="gray")
    ax[0].add_patch(Rectangle((mid[0] - 60, mid[1] - 60), 120, 120, fill=False,
                              ec=MINE_COLOR, lw=2.5))
    ax[0].text(mid[0] - 20, mid[1] + 68, "my search box\n(±60 px)", color=MINE_COLOR,
               ha="center", va="top", fontsize=9, fontweight="bold",
               bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
    spots = {"B1": (40, -30), "B2": (70, 80), "B3": (0, -100)}
    for name, (ox, oy) in spots.items():
        ax[0].plot(mid[0] + ox, mid[1] + oy, "o", ms=9, mfc="white", mec="black", mew=2)
        ax[0].text(mid[0] + ox + 9, mid[1] + oy, name, fontsize=10, fontweight="bold",
                   color="black", va="center",
                   bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
    ax[0].set_title("Middle of each friend-style test photo\n"
                    "B2, B3 are OUTSIDE my search box", fontsize=10)
    ax[0].axis("off")

    # 2) Part A, before optimizer
    names = [r["name"] for r in a]
    x = np.arange(len(names))
    mine_a = [mine6[n]["pixels_off_step4"] for n in names]
    friend_a = [r["pixels_off_logpolar"] for r in a]
    ax[1].bar(x - 0.2, mine_a, 0.38, color=MINE_COLOR, label="me (Step 4)")
    ax[1].bar(x + 0.2, friend_a, 0.38, color=FRIEND_COLOR, label="friend (log-polar)")
    for xi, v in zip(x - 0.2, mine_a):
        ax[1].text(xi, v + 0.03, f"{v:.2f}", ha="center", fontsize=8)
    for xi, v in zip(x + 0.2, friend_a):
        ax[1].text(xi, v + 0.03, f"{v:.2f}", ha="center", fontsize=8)
    ax[1].set_xticks(x, names)
    ax[1].set_ylabel("pixels off (lower = better)")
    ax[1].set_title("Part A: my 5 tests, BEFORE optimizer\n(both methods correct)", fontsize=10)
    ax[1].legend(frameon=False)

    # 3) Part B, after optimizer (log scale: from 0.001 to 1000 px)
    cases = [r["case"].split()[0] for r in b if r["method"] == "mine"]
    xb = np.arange(len(cases))
    mine_b = [max(r["pixels_off_lm"], 1e-3) for r in b if r["method"] == "mine"]
    friend_b = [max(r["pixels_off_lm"], 1e-3) for r in b if r["method"] == "friend"]
    ax[2].bar(xb - 0.2, mine_b, 0.38, color=MINE_COLOR, label="me (Step 4 + 6)")
    ax[2].bar(xb + 0.2, friend_b, 0.38, color=FRIEND_COLOR, label="friend (log-polar + LM)")
    for xi, v in list(zip(xb - 0.2, mine_b)) + list(zip(xb + 0.2, friend_b)):
        ax[2].text(xi, v * 1.3, f"{v:.0f}" if v >= 100 else f"{v:.3g}", ha="center", fontsize=8)
    ax[2].set_yscale("log")
    ax[2].axhline(1, color="#888", lw=1, ls="--")
    ax[2].text(len(cases) - 0.5, 1.15, "1 px", color="#555", fontsize=8, ha="right")
    ax[2].set_xticks(xb, ["B1\nsmall shift", "B2\nbig shift", "B3\nbig shift"])
    ax[2].set_ylabel("pixels off, log scale (lower = better)")
    ax[2].set_title("Part B: friend-style tests, AFTER optimizer\n"
                    "(turn 201°, zoom 2.13, small stretch)", fontsize=10)
    ax[2].legend(frameon=False, loc="upper left")
    for axis in ax[1:]:
        axis.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Step 8: my method vs my friend's method", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig("results/step8_comparison.png", dpi=150, bbox_inches="tight")
    print("Saved results/step8_comparison.png")


def main():
    with open(TRUTH_PATH) as f:
        truth = json.load(f)
    original = cv2.imread(truth["original"], cv2.IMREAD_GRAYSCALE).astype(np.float32)
    a = part_a(truth, original)
    b = part_b(original)
    with open(OUT_PATH, "w") as f:
        json.dump({"part_a_friend_on_my_tests": a, "part_b_friend_style_tests": b}, f, indent=2)
    print(f"\nSaved {OUT_PATH}")
    make_figure(original, a, b)


if __name__ == "__main__":
    main()
