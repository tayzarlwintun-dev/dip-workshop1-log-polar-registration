# Project Journal

## Step 0 – Setup (2026-11-04)
**Did:** made the project folder, a Python virtual environment (`.venv`),
installed opencv-python, numpy, matplotlib, scipy, started git, added a test photo.

**Photo:** `images/original.jpg` – Bangkok skyline, 418 × 625 pixels.
Lots of buildings and roads (good detail for matching). The top part is
mostly sky (smooth, little detail).

**Problems:** none. Added `.gitignore` so the big `.venv` folder is not saved in git.

**Next:** Step 1 – make test pictures with a known rotation, zoom and shift.

## Step 1 – Make test pictures (2026-11-04)
**Did:** wrote `step1_make_test_images.py`. It takes `original.jpg` and makes
4 changed copies where we know the true answer:

| Test | Rotation | Zoom | Shift (x, y) | Idea |
|---|---|---|---|---|
| test1 | 30° | ×1.0 | (0, 0) | rotation only |
| test2 | 0° | ×1.5 | (0, 0) | zoom only |
| test3 | 45° | ×1.5 | (20, −15) | all three |
| test4 | 135° | ×2.0 | (−25, 30) | hard case |
| test5 | 90° | ×1.2 | (10, 10) | my own test (added by me) |

Order of the change: rotate + zoom around the picture center, then shift.
Positive angle = counter-clockwise. True answers saved in `results/test_cases.json`.

**Problems:** the titles in the overview picture were cut off at the top.
Fixed with `bbox_inches="tight"` when saving.

**Results:** test1 has ~18% black corners (rotation pushes picture out of the frame).
Zoomed tests have no black, but lose the outer part of the scene
(test4 at ×2 keeps only the middle quarter).

**Limits:** the test pictures are made by the computer, so they are "perfect"
(no new noise, no lighting change). Real photos would be harder.

**Extra:** I added test5 myself (90°, ×1.2, shift (10, 10)). It ran fine.
At 90° the tall photo turns sideways, so black bars appear at the top and bottom.

**Next:** Step 2 – log-polar transform.

## Step 2 – Log-polar transform (2026-11-04)
**Goal:** turn each picture into its log-polar ("unrolled") form and check the
lecture idea: rotation = slide up/down, zoom = slide right.

**Did:** wrote `step2_log_polar.py`.
- Pictures are used in grayscale (only brightness is needed for matching).
- `cv2.warpPolar` with `WARP_POLAR_LOG`, centered on the picture center (209, 312).
- Size: 360 rows (1 row = 1°) × 256 columns (log distance). Max radius = 375.9 px
  (half the diagonal, so the corners are included).
- Check: slide the ORIGINAL's log-polar picture by the expected amount and compare
  it with each test's log-polar picture (average brightness difference, ignoring black).

**Results:**

| Test | Expected slide (rows, cols) | Difference before | After sliding | Verdict |
|---|---|---|---|---|
| test1 (30°) | (−30, 0) | 27.4 | **2.0** | match ✅ |
| test2 (×1.5) | (0, 17.5) | 24.9 | **6.5** | match ✅ |
| test3 (45°, ×1.5, shift) | (−45, 17.5) | 34.7 | 29.9 | no match (shifted) |
| test4 (135°, ×2, shift) | (−135, 29.9) | 59.9 | 42.7 | no match (shifted) |
| test5 (90°, ×1.2, shift) | (−90, 7.9) | 74.8 | 50.2 | no match (shifted) |

- Rotation really is a slide along the angle axis, and zoom really is a slide
  along the log-distance axis. The lecture idea is confirmed.
- Zoom ×1.5 → log(1.5) on OpenCV's log ruler = 17.5 columns.

**Problems / surprises:**
- Sign: a counter-clockwise turn gives a slide of **−30** rows (up), not +30.
  OpenCV's y-axis points down, so it measures angles clockwise. Same idea,
  opposite direction. Must remember this in Step 3.
- test3, test4 and test5 do not match. Not a bug: these pictures are also SHIFTED,
  so their center sits on a different part of the city and the unrolling starts
  from the wrong point. This is the translation problem from the paper → Step 4.

**Limits:**
- Black bumps on the right: the picture is a rectangle, so in some directions
  it ends before the max radius (like the baboon slide).
- Left side is blurry: near the center only a few pixels are stretched over many
  columns (log-polar gives the center too much space, the edges too little).
- Zoom: content pushed past the right edge is lost (no wrap-around), so the
  zoom match (6.5) is not as perfect as the rotation match (2.0).

**Next:** Step 3 – let the computer FIND the slide by itself (cross-correlation),
then turn it into rotation angle and zoom.

## Step 3 – Find rotation and zoom by itself (2026-11-04)
**Goal:** the computer finds the slide WITHOUT the answer key, then turns it
into rotation angle and zoom.

**Did:** wrote `step3_find_rotation_scale.py`.
- Unroll original and test picture (same as Step 2, center = middle of picture).
- Phase correlation: scores all 360 × 256 = 92,160 possible slides at once
  (Fourier transform), keeps the best one. Sub-pixel accuracy with a small
  parabola fit around the best spot. Hanning window softens the cut left/right edges.
- rows slid → angle = −rows / 360 × 360°;  columns slid → zoom = e^(cols × log(375.9) / 256)
- "Peak" = how strong the best match is (1 = perfect, ~0 = guessing).

**Results:**

| Test | True | Found | Angle error | Zoom error | Peak | Verdict |
|---|---|---|---|---|---|---|
| test1 | 30°, ×1.0 | 30.00°, ×1.000 | 0.00° | 0.00% | 0.850 | correct ✅ |
| test2 | 0°, ×1.5 | 0.00°, ×1.487 | 0.00° | 0.88% | 0.697 | correct ✅ |
| test3 | 45°, ×1.5 + shift | 46.15°, ×1.519 | 1.15° | 1.26% | 0.031 | weak, shifted |
| test4 | 135°, ×2.0 + shift | 137.34°, ×2.060 | 2.34° | 3.01% | 0.041 | weak, shifted |
| test5 | 90°, ×1.2 + shift | 88.02°, ×1.260 | 1.98° | 5.01% | 0.039 | weak, shifted |

**Problems / surprises:**
- The shifted tests are surprisingly CLOSE (1–2° off), because the shift is small
  (10–25 px). But the peak is ~20× weaker (0.03 vs 0.85), so the result is not reliable.
- Changed the verdict text from "wrong" to "not exact, weak peak" to be honest about this.

**Limits:**
- Center is always the middle of the picture → only works without shift.
- test2 peak (0.70) is lower than test1 (0.85): zoom pushes part of the picture
  off the right edge of the log-polar picture, so there is less to match.

**Questions I had:** see `QUESTIONS_AND_ANSWERS.md` (peak, what was manual in
Step 2, what Step 3 does, does it find the center).

**Next:** Step 4 – search for the right center to find the shift.

## Step 4 – Find the shift by searching for the right center (2026-11-04)
**Goal:** solve the shifted tests (test3/4/5) by finding WHERE the test photo's middle
is in the original.

**Did:** wrote `step4_find_shift.py` (the paper's algorithm, slide 11).
1. Unroll the TEST photo around its middle (fixed). Test photo is used as the fixed one
   because it is zoomed in, so its content surely exists in the original.
2. In the ORIGINAL, try many standing spots (±60 px around the middle), unroll around each,
   run phase correlation (Step 3) → peak + slide.
3. Keep the spot with the highest peak.
4. Slide → rotation + zoom. Spot → shift: shift = −zoom × rotate(spot − middle).
- Looks 180 px around each spot (circle).
- Coarse-to-fine (like the paper): every 4th pixel first (961 spots), then every pixel
  ±4 px around the best (81 spots).

**Results (all 5 CORRECT):**

| Test | True (angle, zoom, shift) | Found | Angle err | Zoom err | Shift err | Peak |
|---|---|---|---|---|---|---|
| test1 | 30°, ×1.0, (0,0) | 30.00°, ×1.000, (0,0) | 0.00° | 0.00% | 0.0 px | 0.671 |
| test2 | 0°, ×1.5, (0,0) | 0.02°, ×1.493, (0,0) | 0.02° | 0.47% | 0.0 px | 0.562 |
| test3 | 45°, ×1.5, (20,−15) | 44.71°, ×1.504, (20.3,−15.9) | 0.29° | 0.28% | 0.9 px | 0.321 |
| test4 | 135°, ×2.0, (−25,30) | 135.10°, ×1.961, (−23.5,29.2) | 0.10° | 1.93% | 1.7 px | 0.288 |
| test5 | 90°, ×1.2, (10,10) | 89.87°, ×1.201, (9.6,9.6) | 0.13° | 0.05% | 0.6 px | 0.504 |

Compared with Step 3 (shifted tests): angle error 1–2° → 0.1–0.3°, peak ~0.04 → 0.29–0.50
(about 10× more sure). Time: 1.7 s per test on my MacBook Air.

**Problems / surprises:**
- Peaks are a bit lower than in Step 3 for test1/test2 (0.85 → 0.67), because now we only
  look 180 px around the spot, not the whole picture. Still clearly correct.
- I was very confused about "middle", "unrolling" and "shift" → wrote a very simple
  explanation in `QUESTIONS_AND_ANSWERS.md` (Q10, house/tree/car example).

**Limits:**
- Spots are whole pixels only → shift error up to ~1–2 px. The optimizer (Step 6) can fix this.
- Only searches ±60 px. A bigger shift would need a bigger search area (slower).
- test4 (×2 zoom, 135°) is the hardest: lowest peak (0.288), biggest zoom error (1.93%).

**Next:** Step 5 – use the found numbers to put the test photo back on top of the original
and show they line up.

## Step 5 – Put the test photo back on the original (2026-11-04)
**Goal:** use the turn, zoom and shift from Step 4 to UNDO the change, and show that the
fixed test photo lines up with the original.

**Did:** wrote `step5_align_and_overlay.py`.
- Build the same recipe as Step 1 (turn + zoom around the middle, then shift) from the
  numbers Step 4 found, and run it BACKWARDS (`cv2.WARP_INVERSE_MAP`): un-shift, un-zoom, un-turn.
- Color overlay: original in RED, test photo in CYAN. Lined up → gray. Not lined up →
  red/cyan double edges. Plain red = part of the original the test photo does not show.
- Measured: difference before fixing, after fixing (our numbers), after fixing (true
  numbers = best possible), and "pixels off" (how far each visible pixel is from perfect).
- Fixed photos saved in `images/aligned/`.

**Results (all 5 lined up):**

| Test | Difference before | After (ours) | After (true) | Pixels off |
|---|---|---|---|---|
| test1 | 45.6 | 4.2 | 4.2 | 0.01 px |
| test2 | 42.6 | 6.7 | 3.2 | 0.64 px |
| test3 | 58.4 | 9.9 | 3.4 | 0.93 px |
| test4 | 110.6 | 16.5 | 3.0 | 2.04 px |
| test5 | 85.6 | 7.4 | 4.2 | 0.56 px |

`results/step5_overlay.png`: BEFORE = messy red/cyan double picture, AFTER = clean gray.

**Problems / fixes:**
- First "pixels off" for test4 said 7.98 px. It was measured over the WHOLE original, but
  test4 (zoom ×2) only shows the middle part. Small zoom errors grow far from the middle.
  Fixed: only measure pixels the test photo really shows → 2.04 px.
- Big title overlapped the first row of the figure → moved it up.

**Limits:**
- Not perfect: "after (ours)" is a bit higher than "after (true)" (e.g. test4 16.5 vs 3.0),
  because Step 4's numbers are slightly off (test4 zoom ×1.96 instead of ×2.00).
- Even with the true numbers the difference is not 0 (3–4), because turning/zooming
  a photo blurs it slightly (pixels are re-calculated).

**Next:** Step 6 (bonus) – optimizer: nudge the numbers a tiny bit at a time until the
overlay is as clean as possible (like the paper's Levenberg–Marquardt step).

## Step 6 – Optimizer fine-tuning (bonus) (2026-11-04)
**Goal:** the paper's second half – start from Step 4's good guess and fine-tune it
until the photos match as well as possible.

**Did:** wrote `step6_optimizer.py`.
- 6 knobs (the paper's a1..a6): new_x = a1·x + a2·y + a3, new_y = a4·x + a5·y + a6
  (can describe turn, zoom, shift AND slant).
- Measure of match = SSD (the paper's): sum of (brightness difference)² over visible pixels.
- Levenberg–Marquardt (same as the paper) via scipy `least_squares(method="lm")`.
- Start from Step 4's numbers. Two rounds: blurry photos first (σ = 2), then sharper (σ = 1).
- Like tuning a radio / walking blindfolded downhill: only works if you START close,
  so Step 4 must come first (the paper's main point).

**Results:**

| Test | Pixels off Step 4 → 6 | SSD Step 4 → 6 | Zoom Step 4 → 6 (true) | Angle Step 4 → 6 (true) |
|---|---|---|---|---|
| test1 | 0.01 → 0.00 | 61.1 → 61.1 | 1.0000 → 1.0000 (1.00) | 30.00 → 30.00 (30) |
| test2 | 0.64 → 0.04 | 144.4 → 33.0 | 1.4929 → 1.4996 (1.50) | 0.02 → 0.00 (0) |
| test3 | 0.93 → 0.00 | 346.9 → 36.2 | 1.5042 → 1.5000 (1.50) | 44.71 → 45.00 (45) |
| test4 | 2.04 → 0.01 | 786.5 → 22.7 | 1.9615 → 2.0000 (2.00) | 135.10 → 135.00 (135) |
| test5 | 0.56 → 0.02 | 183.8 → 57.1 | 1.2005 → 1.2000 (1.20) | 89.87 → 90.00 (90) |

- All tests now under 0.05 px from perfect. test4: SSD about 35× smaller.
- Correction matrix (how much the optimizer changed) is close to "do nothing"
  (1 0 0 / 0 1 0), like the paper: the log-polar guess was already very close.
- `results/step6_compare.png`: test4 cars have red/cyan double edges after Step 4,
  clean gray after Step 6.

**Problems / fixes (2 bugs):**
1. Optimizer did not move at all (stopped after 1 look). Cause: `cv2.warpAffine` rounds
   positions to 1/32 pixel, the optimizer's tiny test-steps saw "no change".
   Fix: use exact bilinear sampling (`scipy.ndimage.map_coordinates`) in the optimizer.
2. test2 and test4 barely improved. Cause: these photos fill the whole frame, so pixels at
   the very edge slipped outside when the zoom changed → big "punishment" → optimizer
   refused to change the zoom. Fix: trim a thin strip around the outer frame too
   (`cv2.erode` with `BORDER_CONSTANT`).

**Limits:**
- Needs a good start (from Step 4). Alone, from "no change", it would get lost on big turns.
- Slower than Step 4's search per step, and test photos are perfect (no noise / lighting change).
- Zoomed comparison picture for test1/2/5 shows mostly sky, so the difference is easier
  to see in the numbers than by eye.

**Next:** Step 7 – report notes.

## Step 7 – Report notes (2026-11-04)
**Did:** wrote `REPORT_NOTES.md`: goal, background of the paper, test data, method per step,
all results tables (Steps 2–6), list of the 7 figures to use, comparison with the paper,
differences from the paper, 5 problems fixed, limits, conclusion, suggested report layout,
how to reproduce.

**Result:** all 7 workshop steps done. Final accuracy: all 5 tests within 0.05 px after Step 6.

**Next:** write the report from `REPORT_NOTES.md`; compare with my friend's work.
