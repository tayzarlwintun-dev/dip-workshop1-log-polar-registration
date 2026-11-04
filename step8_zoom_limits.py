"""
Step 8 - How far can we zoom? (zoom IN up to x10, zoom OUT down to x0.25)

The paper says:
  - the log-polar part can handle up to TEN-fold (x10) zoom differences,
  - "in practice we don't expect scale changes beyond factors of four" (x4),
  - the optimizer alone only works within x2 zoom and 45 degrees.
The paper's examples: x4 zoom + 45 degrees (Fig. 2), and scale 0.469 (= x2.13 the other
way round) + 201 degrees (Fig. 3).

Here every test photo is made like the hard tests of Step 7: turned 40 degrees,
moved a little (spot offset (20, -15)), zoomed by the factor below, a little noise.
  zoom > 1 = zoom IN  (test photo shows a SMALLER part of the city, bigger)
  zoom < 1 = zoom OUT (test photo shows the WHOLE city, smaller, black around it)

Output: results/step8_zoom_limits.json
"""
import json
import os
import time

import numpy as np

import step4_find_shift as s4
import step6_optimizer as s6
import step7_hard_tests as s7

ZOOMS = [4, 5, 6, 8, 10, 0.75, 0.5, 0.35, 0.25]
GOOD = 0.1


def main():
    original = s4.load_gray("images/original.jpg")
    h, w = original.shape
    print(f"{'zoom':>6} | {'found turn':>10} {'found zoom':>10} | {'px off: search':>14} -> "
          f"{'optimizer':>10} | {'photo filled':>12} | {'time':>5} | verdict")
    print("-" * 92)
    results = []
    for z in ZOOMS:
        test, m_true = s7.make_hard_test(original, 40, z, (20, -15), s7.NO_STRETCH)
        start = time.time()
        r = s4.find_turn_zoom_shift(original, test)
        m4 = s6.make_matrix(w, h, r["angle"], r["scale"], r["shift"][0], r["shift"][1])
        m6, _ = s6.optimize(original, test, m4)
        secs = time.time() - start
        off4, off6 = s6.pixels_off(m4, m_true, test), s6.pixels_off(m6, m_true, test)
        filled = 100 * float((test > 0).mean())
        ok = off6 < GOOD
        print(f"{z:6} | {r['angle']:9.2f}° {r['scale']:9.3f}x | {off4:14.2f} -> {off6:10.3f} | "
              f"{filled:11.0f}% | {secs:4.0f}s | {'PERFECT' if ok else 'FAILED'}")
        results.append({"zoom": z, "turn_true": 40, "turn_found": round(r["angle"], 2),
                        "zoom_found": round(r["scale"], 3),
                        "pixels_off_after_search": round(off4, 2),
                        "pixels_off_after_optimizer": round(off6, 3),
                        "photo_filled_percent": round(filled, 1),
                        "seconds": round(secs, 1), "practically_perfect": bool(ok)})
    with open(os.path.join("results", "step8_zoom_limits.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved results/step8_zoom_limits.json")


if __name__ == "__main__":
    main()
