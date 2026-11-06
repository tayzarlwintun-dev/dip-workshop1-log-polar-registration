# Report Notes – Workshop 1: Image Registration with the Log-Polar Transform

Digital Image Processing (TGGS, 1st semester) – Tayzar Lwin Tun
Paper: G. Wolberg & S. Zokai, *"Robust Image Registration Using Log-Polar Transform"*
Code: Python 3.14 + OpenCV + NumPy + SciPy + Matplotlib, 7 scripts (`step1_...py` to `step7_...py`).

Use this file as the skeleton of the report. Each section says what to write and which
picture/table to use.

---

## 1. Goal (1 short paragraph)

**Image registration** = lining up two pictures of the same scene so the same point of the
scene sits on the same pixel in both. Here the second picture is **turned (rotation),
zoomed (scale) and moved (translation)**. The program must find these 3 amounts by itself
and then put picture 2 back on top of picture 1.
This workshop does NOT look for differences between the pictures – it only aligns them
(finding differences, stitching, comparing scans etc. would come AFTER alignment).

## 2. Background – the idea of the paper (2–3 short paragraphs)

- In normal (x, y) pixels, a **turn moves every pixel differently** → cannot be found by
  simply sliding one picture over the other.
- **Log-polar transform**: describe every pixel by its **angle** and **log of its distance**
  from a center point. Rows = angle (0–359°), columns = log(distance).
  - turn the picture by θ → the log-polar picture **slides up/down** by θ
  - zoom the picture by s → the log-polar picture **slides right** by log(s)
  - a slide is easy to find with cross-correlation (try every slide, keep the best score)
- Problem: this only works if both pictures use the **same center**. If picture 2 is also
  moved, the paper **searches over many centers** and keeps the best match → gives the shift.
- The log-polar result is a **rough but robust** first guess (works for any turn and big
  zoom). The paper then **fine-tunes** it with a Levenberg–Marquardt optimizer on 6 affine
  parameters (a1..a6) minimizing SSD. The optimizer alone fails if the start is far off
  (needs < 45° and < ×2), so the two methods together work best.
- Older method (Fourier–Mellin) uses log-polar on the Fourier magnitude: removes the shift,
  but only works up to about ×2 zoom. The paper's spatial log-polar works up to ×10.

Simple explanation for the reader (optional box): "clock picture" – stand on the center,
write down what you see in each direction; turning the photo just moves everything along
the list by the same amount (see `QUESTIONS_AND_ANSWERS.md` Q8, Q12, Q13).

## 3. Test data (Step 1)

- Original: `images/original.jpg`, Bangkok skyline, 418 × 625 px (lots of buildings and
  roads; top third mostly smooth sky).
- 5 test pictures made by the program with KNOWN answers (rotate + zoom around the middle,
  then shift; positive angle = counter-clockwise):

| Test | Turn | Zoom | Shift (x, y) | Idea |
|---|---|---|---|---|
| test1 | 30° | ×1.0 | (0, 0) | turn only |
| test2 | 0° | ×1.5 | (0, 0) | zoom only |
| test3 | 45° | ×1.5 | (20, −15) | all three |
| test4 | 135° | ×2.0 | (−25, 30) | hard case |
| test5 | 90° | ×1.2 | (10, 10) | my own test |

**Figure 1:** `results/step1_test_images.png` – original + 5 test pictures.

## 4. Method (one paragraph per step)

**Step 2 – Log-polar transform + proof.** `cv2.warpPolar` with `WARP_POLAR_LOG`, center =
middle of the picture, 360 rows (1 row = 1°) × 256 columns, max radius 375.9 px (half the
diagonal). Proof: slide the original's log-polar picture by the expected amount and compare
with the test's log-polar picture.
Note: a counter-clockwise turn slides UP (−30 rows for 30°) because OpenCV's y-axis points down.

**Step 3 – Find turn and zoom by itself.** Phase correlation (fast cross-correlation with
the Fourier transform) scores all 360 × 256 slides at once. Best slide → turn = −rows/360·360°,
zoom = e^(cols·log R / 256). Sub-pixel by a parabola fit; Hanning window on the left/right
edges. "Peak" = height of the best score (1 = perfect, ~0 = guessing).

**Step 4 – Find the shift (search for the center).** Log-polar of the TEST picture around
its middle is kept fixed. In the ORIGINAL, try many centers (±60 px), log-polar around each
(look radius 180 px), phase correlation → peak. Best peak = the spot in the original that
is the test picture's middle. Coarse-to-fine: every 4th pixel (961 spots), then every pixel
±4 around the best (81 spots). Shift = −zoom · rotate(spot − middle).

**Step 5 – Put the test picture back.** Build the transform from the found numbers and
apply it backwards (`cv2.WARP_INVERSE_MAP`). Show a red/cyan overlay (red = original,
cyan = fixed test): gray = lined up, double red/cyan edges = not lined up.

**Step 6 – Optimizer (bonus).** 6 affine knobs a1..a6, SSD cost, Levenberg–Marquardt
(`scipy.optimize.least_squares(method="lm")`), starting from Step 4's numbers. Two rounds:
blurred (σ = 2) then sharper (σ = 1). Exact bilinear sampling (`map_coordinates`) and a
trimmed edge strip (see "problems").

## 5. Results

### 5.1 Step 2 – turning/zooming really is sliding

| Test | Expected slide (rows, cols) | Difference before | After sliding |
|---|---|---|---|
| test1 (30°) | (−30, 0) | 27.4 | **2.0** ✅ |
| test2 (×1.5) | (0, 17.5) | 24.9 | **6.5** ✅ |
| test3/4/5 (also shifted) | – | 34.7 / 59.9 / 74.8 | 29.9 / 42.7 / 50.2 (no match → need Step 4) |

**Figure 2:** `results/step2_log_polar.png` – pictures and their log-polar versions.
**Figure 3:** `results/step2_slide_check.png` – original slid vs. test (should look the same).

### 5.2 Step 3 vs Step 4 vs Step 6 – found values

| Test | True | Step 3 (no center search) | Step 4 (center search) | Step 6 (optimizer) |
|---|---|---|---|---|
| test1 | 30°, ×1.0, (0,0) | 30.00°, ×1.000 – peak 0.85 | 30.00°, ×1.000, (0,0) | 30.00°, ×1.0000 |
| test2 | 0°, ×1.5, (0,0) | 0.00°, ×1.487 – peak 0.70 | 0.02°, ×1.493, (0,0) | 0.00°, ×1.4996 |
| test3 | 45°, ×1.5, (20,−15) | 46.15°, ×1.519 – peak 0.03 ❌ | 44.71°, ×1.504, (20.3,−15.9) | 45.00°, ×1.5000 |
| test4 | 135°, ×2.0, (−25,30) | 137.34°, ×2.060 – peak 0.04 ❌ | 135.10°, ×1.961, (−23.5,29.2) | 135.00°, ×2.0000 |
| test5 | 90°, ×1.2, (10,10) | 88.02°, ×1.260 – peak 0.04 ❌ | 89.87°, ×1.201, (9.6,9.6) | 90.00°, ×1.2000 |

- Step 3 is exact when there is no shift, but for shifted pictures the peak drops ~20×
  (0.85 → 0.03) and the answer is unreliable.
- Step 4 fixes this: peaks 0.29–0.67, angle error ≤ 0.29°, zoom error ≤ 1.93%, shift error ≤ 1.7 px.
- Step 6 makes everything almost exact.

**Figure 4:** `results/step3_peaks.png` – score maps: one sharp dot (sure) vs. noisy (unsure).
**Figure 5:** `results/step4_search_maps.png` – peak for every center tried (+ = middle,
circle = best spot; circle away from + = picture was moved).

### 5.3 How well the pictures line up

| Test | Difference before fixing | After Step 4 numbers | Pixels off after Step 4 | Pixels off after Step 6 | SSD Step 4 → Step 6 |
|---|---|---|---|---|---|
| test1 | 45.6 | 4.2 | 0.01 | 0.00 | 61.1 → 61.1 |
| test2 | 42.6 | 6.7 | 0.64 | 0.04 | 144.4 → 33.0 |
| test3 | 58.4 | 9.9 | 0.93 | 0.00 | 346.9 → 36.2 |
| test4 | 110.6 | 16.5 | 2.04 | 0.01 | 786.5 → 22.7 |
| test5 | 85.6 | 7.4 | 0.56 | 0.02 | 183.8 → 57.1 |

("Pixels off" = average distance between where each visible pixel lands and where it
should land, in original-picture pixels.)

**Figure 6 (main result):** `results/step5_overlay.png` – BEFORE (messy red/cyan double
picture) vs AFTER (clean gray) for all 5 tests.
**Figure 7:** `results/step6_compare.png` – zoom on an edge, Step 4 vs Step 6 (test4 cars:
double edges → clean).

### 5.4 Comparison with the paper

| | Paper (real building photos) | This workshop (synthetic tests) |
|---|---|---|
| Log-polar result | scale 0.469, rotation −201°, shift (−11, −51) | up to 135°, ×2, shift up to (−25, 30), all found |
| Optimizer correction | near identity (1.008, 0.006, −1.669 / 0.003, 1.045, 0.203) | near identity, e.g. test4 (1.0196, −0.0018, −4.51 / 0.0017, 1.0196, −6.19) |
| Conclusion | log-polar = good start, optimizer = sub-pixel | same: Step 4 gets within ~2 px, Step 6 within 0.05 px |

## 5.5 Version 2 – improvements after comparing with my friend (Step 9)

Use `results/step9_old_vs_new.png` and `results/step7_hard_tests.png` as figures and
`IMPROVEMENTS.md` for the text. Hard tests run with `step7_hard_tests.py` (8/8 under 0.1 px).
- Changes: search whole picture; rough search on 4× smaller copy with two judges
  (cross-correlation + phase correlation, 6 spots each); gray fill of black areas; two anchors
  (middle + most detailed) with a real-match check; optimizer blur 4 → 2 → 1 → 0.5.
- 13 tests (my 5 + 4 friend-style like the paper's Fig. 3 + 4 extra with big shifts, zoom up to ×3):
  practically perfect (< 0.1 px) old 5/13, **new 13/13**, friend 10/13.
- Optimizer alone (start "no change") gets lost on all tried tests (42–15,058 px) → paper's point.
- Search slower than version 1 (MacBook Air: 2.6–3.2 s vs 1.7 s per test), still faster than my friend's.
- Figure `results/step4_search_maps.png`: cross-correlation = gentle hills, phase correlation =
  sharp needle + fake stripes in the sky → why two judges are better than one.

## 6. Differences from the paper (be honest in the report)

- **Which picture is fixed:** we keep the TEST picture's center fixed and search centers in
  the ORIGINAL (the test pictures are zoomed in, so their content surely exists in the
  original).
- **Phase correlation** instead of plain cross-correlation (same idea, sharper peak, faster).
- **Search speed-up:** version 2: 4× smaller copy → half-size clock pictures → full size
  (similar idea to the paper's pyramid); two judges for the short list (not in the paper).
- **Anchor:** version 2 tries two anchors in the test picture and checks which answer really matches.
- **Test data:** synthetic (we made the turned/zoomed/moved copies), so there is no noise,
  lighting change or perspective. The paper used real photos.

## 7. Problems found and fixed (good for "discussion")

1. **Turn direction:** counter-clockwise turn = slide UP (−rows), because OpenCV's y-axis points down.
2. **Step 3 on shifted pictures:** close by luck (1–2° off) but very low peak → unreliable → Step 4.
3. **"Pixels off" for test4** first said 7.98 px – measured over parts the zoomed picture does
   not show. Fixed: only measure visible pixels → 2.04 px.
4. **Optimizer did not move:** `cv2.warpAffine` rounds positions to 1/32 px, so the
   optimizer's tiny test-steps saw no change. Fixed with exact `map_coordinates`.
5. **Optimizer barely improved test2/test4:** edge pixels slipped outside the picture when
   the zoom changed. Fixed by trimming the outer frame.

## 8. Limits

- Synthetic tests only; real photos (noise, lighting, perspective) would be harder.
- Only rotation + zoom + shift (+ slant in Step 6). **Perspective** (photo from a different
  side, rectangle → trapezoid) is not handled – the paper also lists this as future work.
- Center search: version 1 was limited to ±60 px (~1.7 s on a MacBook Air); version 2 searches
  the whole picture but is about 2× slower (see `IMPROVEMENTS.md`).
- Log-polar gives too much space to the center (blurry left side) and too little to the edges.
- Rectangle picture → black bumps in log-polar; rotated pictures have black corners.
- Low-detail areas (sky) are hard to match.
- Shift found to whole pixels in Step 4 (sub-pixel only after Step 6).

- **Zoom range (Step 8 test):** works ×0.5 – ×2 (×3 only sometimes); experiment `experiments/zoom_fix/`
  (zoom guesses + swap photos, test only) reaches ×0.35 – ×5, like the paper's ×4 "in practice". Main: fails at ×4+ (rough search on the 4× smaller copy
  loses the spot; ≥ ×6 the test photo is too blurry because my photo is small) and at ×0.35 or less
  (test photo mostly black). The paper claims up to ×10 (×4 in practice) → weaker than the paper here.

- **Optimizer alone (`step9_optimizer_alone.py`):** lost on all 5 tests (tens to thousands of px off);
  with log-polar first 0.001–0.015 px. Figure `results/step9_optimizer_alone.png`.

## 9. Conclusion (1 paragraph)

Log-polar turns rotation and zoom into simple slides, which phase correlation finds
reliably for any rotation angle. Searching over centers adds the shift. This rough step
alone lines the pictures up within about 2 px; the Levenberg–Marquardt optimizer started
from it brings all 5 tests within 0.05 px. This confirms the paper's idea: a robust rough
method (log-polar) + a precise local method (optimizer) works better than either alone.

## 10. Suggested report layout

1. Introduction & goal (section 1)
2. Theory: log-polar, why rotation/zoom become slides, center search, optimizer (section 2)
3. Test data – Figure 1 (section 3)
4. Method – one paragraph per step (section 4)
5. Results – tables 5.1–5.3, Figures 2–7 (section 5)
6. Discussion – comparison with paper, differences, problems fixed, limits (sections 5.4, 6, 7, 8)
7. Conclusion (section 9)

## 11. How to reproduce

```bash
source .venv/bin/activate
python step1_make_test_images.py
python step2_log_polar.py
python step3_find_rotation_scale.py
python step4_find_shift.py
python step5_align_and_overlay.py
python step6_optimizer.py
```
All numbers are saved in `results/*.json`, all figures in `results/*.png`.
