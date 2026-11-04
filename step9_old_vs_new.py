"""
Step 9 - Is my improved method (version 2) really better?

We test 3 methods on the SAME 13 test photos:
  OLD    = my version 1: Step 4 searches only +-60 px around the middle,
           Step 6 optimizer blur 2 -> 1
  NEW    = my version 2: Step 4 searches the WHOLE picture (2 judges, 2 anchors,
           gray fill), Step 6 optimizer blur 4 -> 2 -> 1 -> 0.5
  FRIEND = my friend's code (friend_version/registration.py)

The 13 test photos:
  test1..test5  my original tests (Step 1)
  B0..B3        friend-style (like the paper's Fig. 3): turn 201° (clockwise), zoom 2.13,
                the paper's small stretch, a little noise; small and BIG shifts
                (B0 = the case where BOTH old methods failed)
  C1..C4        new extra tests: other turns and zooms (up to x3), big shifts, no stretch

Also the paper's main point: the optimizer ALONE (starting from "no change") fails.

Score = "pixels off" (same as Steps 5, 6, 8): on average, how far each visible
point lands from the right place. Under 0.1 px = practically perfect.

Output:
  results/step9_results.json
  results/step9_old_vs_new.png
  images/generated/B0_..., C1_... C4_...  (the new test photos)
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

import step4_find_shift as my4
import step6_optimizer as my6
import step8_compare_with_friend as s8          # friend's method + test-photo maker

PAPER_STRETCH = [[1.008, 0.006], [0.003, 1.045]]
NO_STRETCH = [[1.0, 0.0], [0.0, 1.0]]
GOOD = 0.1          # px: "practically perfect"


def new_method(original, test):
    """My version 2: improved Step 4 + improved Step 6."""
    h, w = original.shape
    start = time.time()
    r = my4.find_turn_zoom_shift(original, test)
    m4 = my6.make_matrix(w, h, r["angle"], r["scale"], r["shift"][0], r["shift"][1])
    t4 = time.time() - start
    start = time.time()
    m6, _ = my6.optimize(original, test, m4)
    return m4, t4, m6, time.time() - start


def old_method(original, test):
    m4, t4, m6, t6, _ = s8.my_method(original, test)
    return m4, t4, m6, t6


def friend_method(original, test):
    m4, t4, m6, t6, _ = s8.friend_method(original, test)
    return m4, t4, m6, t6


def make_tests(truth, original):
    """All 13 test photos with their true matrix."""
    tests = []
    for t in truth["tests"]:
        tests.append((t["name"], "my test", my4.load_gray(t["file"]), np.array(t["matrix"])))
    extra = [  # name, turn (my way: + = counter-clockwise), zoom, spot offset, stretch, idea
        ("B0", -201, 2.13, (110, -150), PAPER_STRETCH, "friend-style, original's middle NOT visible"),
        ("B1", -201, 2.13, (40, -30), PAPER_STRETCH, "friend-style, small shift"),
        ("B2", -201, 2.13, (70, 80), PAPER_STRETCH, "friend-style, big shift"),
        ("B3", -201, 2.13, (0, -100), PAPER_STRETCH, "friend-style, big shift, middle in sky"),
        ("C1", 300, 3.0, (-90, 0), NO_STRETCH, "zoom x3, big shift"),
        ("C2", 60, 1.3, (60, -90), NO_STRETCH, "big shift"),
        ("C3", -120, 1.8, (-70, -90), NO_STRETCH, "big shift"),
        ("C4", 10, 1.1, (120, 150), NO_STRETCH, "very big shift"),
    ]
    for name, angle, zoom, offset, stretch, idea in extra:
        test, m = s8.make_friend_style(original, angle, zoom, offset, stretch)
        cv2.imwrite(f"images/generated/{name}_friend_style.png" if name[0] == "B"
                    else f"images/generated/{name}_extra.png", test.astype(np.uint8))
        tests.append((name, f"turn {angle}°, zoom {zoom}, {idea}", test, m))
    return tests


def make_figure(rows, alone):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"old": "#8a8a8a", "new": "#2a78d6", "friend": "#eb6834"}
    labels = {"old": "my OLD (version 1)", "new": "my NEW (version 2)", "friend": "friend"}
    names = [r["name"] for r in rows]
    x = np.arange(len(names))
    fig, ax = plt.subplots(2, 1, figsize=(15, 9), gridspec_kw={"height_ratios": [1.6, 1]})

    for k, key in enumerate(["old", "new", "friend"]):
        vals = [max(r[key]["pixels_off_after_optimizer"], 1e-3) for r in rows]
        ax[0].bar(x + (k - 1) * 0.27, vals, 0.25, color=colors[key], label=labels[key])
    ax[0].set_yscale("log")
    ax[0].axhline(GOOD, color="#2e7d32", lw=1.2, ls="--")
    ax[0].text(-0.6, GOOD * 1.25, "0.1 px = practically perfect", color="#2e7d32",
               ha="left", fontsize=9)
    ax[0].axhline(1, color="#999", lw=1, ls=":")
    ax[0].set_xticks(x, names)
    ax[0].set_ylabel("pixels off after optimizer\n(log scale, lower = better)")
    ax[0].set_title("Final accuracy on 13 test photos (bars above the green line = failed or not exact)",
                    fontsize=11)
    ax[0].legend(frameon=False, ncol=3, loc="upper left")
    for k, key in enumerate(["old", "new", "friend"]):
        for xi, r in zip(x, rows):
            if r[key]["pixels_off_after_optimizer"] > 1:
                ax[0].text(xi + (k - 1) * 0.27, r[key]["pixels_off_after_optimizer"] * 1.3, "✗",
                           ha="center", fontsize=10, color="#333")

    for k, key in enumerate(["old", "new", "friend"]):
        vals = [r[key]["seconds_total"] for r in rows]
        ax[1].bar(x + (k - 1) * 0.27, vals, 0.25, color=colors[key], label=labels[key])
    ax[1].set_xticks(x, names)
    ax[1].set_ylabel("seconds per test\n(this computer, lower = faster)")
    ax[1].set_title("Time (search + optimizer)", fontsize=11)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)

    wins = {key: sum(r[key]["pixels_off_after_optimizer"] < GOOD for r in rows)
            for key in ["old", "new", "friend"]}
    fig.suptitle(f"Step 9: practically perfect on {wins['old']}/13 (old)  ·  "
                 f"{wins['new']}/13 (new)  ·  {wins['friend']}/13 (friend)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig("results/step9_old_vs_new.png", dpi=130, bbox_inches="tight")
    print("Saved results/step9_old_vs_new.png")


def main():
    with open("results/test_cases.json") as f:
        truth = json.load(f)
    original = my4.load_gray(truth["original"])
    h, w = original.shape
    tests = make_tests(truth, original)

    print(f"{'test':6} | {'OLD: search -> optimizer':>27} | {'NEW: search -> optimizer':>27} | "
          f"{'FRIEND: search -> optimizer':>27}")
    print("-" * 100)
    rows = []
    for name, idea, test, m_true in tests:
        row = {"name": name, "idea": idea}
        cells = []
        for key, fn in [("old", old_method), ("new", new_method), ("friend", friend_method)]:
            m4, t4, m6, t6 = fn(original, test)
            off4, off6 = s8.pixels_off(m4, m_true, test), s8.pixels_off(m6, m_true, test)
            row[key] = {"pixels_off_after_search": round(off4, 3),
                        "pixels_off_after_optimizer": round(off6, 4),
                        "seconds_search": round(t4, 2), "seconds_optimizer": round(t6, 2),
                        "seconds_total": round(t4 + t6, 2)}
            mark = "OK " if off6 < GOOD else ("~  " if off6 < 2 else "BAD")
            cells.append(f"{off4:8.2f} -> {off6:8.3f} px {mark}")
        print(f"{name:6} | " + " | ".join(cells), flush=True)
        rows.append(row)

    # the paper's point: the optimizer ALONE (start = "no change") gets lost
    print("\nOptimizer ALONE (start from 'no change'), new optimizer:")
    alone = []
    for name, idea, test, m_true in tests:
        if name not in ("test1", "test4", "B1", "C2"):
            continue
        m6, _ = my6.optimize(original, test, np.array([[1.0, 0, 0], [0, 1.0, 0]]))
        off = s8.pixels_off(m6, m_true, test)
        print(f"  {name}: {off:9.2f} px off  ({'lost' if off > 2 else 'ok'})")
        alone.append({"name": name, "pixels_off": round(off, 2)})

    with open("results/step9_results.json", "w") as f:
        json.dump({"tests": rows, "optimizer_alone": alone}, f, indent=2)
    print("\nSaved results/step9_results.json")
    for key in ["old", "new", "friend"]:
        good = sum(r[key]["pixels_off_after_optimizer"] < GOOD for r in rows)
        secs = np.mean([r[key]["seconds_total"] for r in rows])
        print(f"  {key:6}: practically perfect on {good}/13 tests, average {secs:.1f} s per test")
    make_figure(rows, alone)


if __name__ == "__main__":
    main()
