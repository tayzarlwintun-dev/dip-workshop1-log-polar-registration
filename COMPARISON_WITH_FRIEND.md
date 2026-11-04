# My Work vs My Friend's Work – Workshop 1 (Log-Polar Registration)

My friend's version: `Workshop1_Demo.ipynb` + `registration.py` + `demo_tools.py`
(a copy of the two `.py` files is in `friend_version/`, so the test can be run again).
Test script: `step8_compare_with_friend.py` → `results/step8_comparison.json` and
`results/step8_comparison.png`.

---

## 1. The short answer

**We both solved the same problem with the same big idea** (log-polar to find turn + zoom,
then a search to find the shift, then Levenberg–Marquardt to fine-tune).
On **my 5 test photos, both methods are correct**, and after the optimizer both are
almost perfect (under 0.06 pixels off).

**The biggest difference is HOW we search for the shift:**

- 🔍 **Me:** I only search in a **small box** (±60 px) around the middle of the original.
  Fast, but if the photo is moved further than that, my method gets lost.
- 🔍 **My friend:** searches **the whole picture**, exactly like the paper (slide 11).
  Slower (about 2.5× slower), but works even with a very big shift.

**Example:** you lost your friend in a crowd photo.
I only look at the people near the middle of the photo – quick, but if my friend stands
at the edge, I never find them. My friend's method looks at every face in the whole
photo – slow, but always finds them (as long as they are in the photo at all).

---

## 2. Same and different – table

| Thing | Me | My friend | Same? |
|---|---|---|---|
| Language | Python | Python | ✅ same |
| Libraries | OpenCV + NumPy + SciPy | NumPy + SciPy only (no OpenCV), PIL to load photos | ❌ |
| Form | 6 separate scripts (one per step) + notes files | 1 Jupyter notebook with formulas + 2 code files | ❌ |
| Photo | Bangkok skyline (418 × 625) | Mandrill (for the demo) + Shepard Hall building (paper's photo) | ❌ |
| Test photos | 5 tests, made with `cv2.warpAffine` from the same photo, black corners, no noise | 1 main test + 1 "try it yourself", rendered from a big photo (sharp like a real camera), a little noise, **plus a small stretch** like the paper | ❌ |
| Log-polar picture | 360 rows × 256 columns, `cv2.warpPolar` | 360 rows × 100 columns, own code | similar |
| How far it looks | 180 px | 0.4 × short side (167 px on my photo) | similar |
| Find the slide | **Phase correlation** + window + "in-between" (sub-pixel) fit | **Cross-correlation** like the paper, whole steps only | ❌ |
| Find the shift | Search spots in the ORIGINAL, only ±60 px | Search ALL spots in the TEST photo (like the paper) | ❌ **main difference** |
| Coarse → fine | every 4 px, then ±4 px | shrink photo 4×, try every spot, then ±4 px | similar idea |
| Optimizer (LM) | yes, `least_squares(method="lm")`, blur 2 → 1 | yes, same function, blur 4 → 2 → 1 → 0 | ✅ mostly same |
| Shows "optimizer alone fails" | no (it was in my IDEAS list) | **yes** (301 px off) | ❌ |
| Bugs written down, journal, tests table | **yes** | no | ❌ |

---

## 3. The differences explained simply

### 3.1 Finding the slide: phase correlation (me) vs cross-correlation (friend)
Both slide the two "clock pictures" over each other and look for the best match.
- **Cross-correlation (friend, like the paper):** "how much do the two pictures look alike
  at each slide position?" The answer is a whole number of rows/columns.
  Example: like a ruler with only centimeter marks – you can say "about 4 cm", not "4.3 cm".
- **Phase correlation (me):** looks only at the *pattern of edges*, not brightness, so the
  best match is a sharper, clearer spike. I also guess *between* the marks (sub-pixel),
  like reading "4.3 cm" by eye between the marks.

In practice both found the right turn and zoom. My friend's whole steps were exact here
**because all our test angles are whole degrees** (30°, 45°, 135°…). With 30.5° their
step would be up to 0.5° off before the optimizer.

### 3.2 Finding the shift: small box (me) vs whole picture (friend)
- **Me:** I keep the TEST photo's middle fixed and try spots in the ORIGINAL, but only
  ±60 px around its middle (961 + 81 spots). Fast: ~1.7 s on my Mac.
- **Friend:** keeps the ORIGINAL's middle fixed and tries EVERY spot in the TEST photo
  (on a 4× smaller copy first = about 16,000 spots, then 81). This is exactly slide 11 of
  the lecture. Slower: ~10 s per test on the same computer where mine took ~4 s.

**Their limit:** the middle of the original must still be visible in the test photo.
**My limit:** the middle of the test photo must come from within ±60 px of the original's middle.

### 3.3 Test photos
My friend made the test more like real life:
- the test photo is **rendered from a bigger photo**, so a zoomed-in view stays sharp
  (like a real camera zooming in), not blurry like my `warpAffine` zoom;
- **a little noise** (like a real camera);
- **a small stretch** (shear) taken from the paper's result (Fig. 3). Turn + zoom + shift
  alone cannot describe this, so only the optimizer can fix it.
  This shows *why* the paper needs the optimizer.

---

## 4. Fair test 1 – friend's code on MY 5 test photos (Part A)

| Test | True turn / zoom / shift | Friend found | Friend pixels off (before LM) | Me pixels off (Step 4) | Friend after LM | Me after LM (Step 6) |
|---|---|---|---|---|---|---|
| test1 | 30°, ×1.0, (0, 0) | 30.00°, ×1.000, (0.2, 0.2) | 0.26 | **0.01** | 0.053 | **0.004** |
| test2 | 0°, ×1.5, (0, 0) | 0.00°, ×1.507, (0.3, −0.2) | 0.62 | 0.64 | **0.008** | 0.038 |
| test3 | 45°, ×1.5, (20, −15) | 45.00°, ×1.507, (19.6, −15.0) | **0.66** | 0.93 | 0.006 | **0.003** |
| test4 | 135°, ×2.0, (−25, 30) | 135.00°, ×2.030, (−25.5, 30.6) | **1.49** | 2.04 | **0.002** | 0.01 |
| test5 | 90°, ×1.2, (10, 10) | 90.00°, ×1.205, (10.1, 10.4) | 0.65 | **0.56** | 0.040 | **0.02** |

**Result:** both correct on all 5. Before the optimizer, each wins some tests.
After the optimizer, both are practically perfect (all under 0.06 px).
Speed (same cloud computer): friend ~10 s per test for the search (+ 2–23 s optimizer),
me ~4 s (+ ~2 s optimizer).

## 5. Fair test 2 – friend-style tests on my photo (Part B)

New test photos made from my Bangkok photo, like my friend's test:
turn 201°, zoom ×2.13, the paper's small stretch, a little noise.
Pictures: `images/generated/B1_friend_style.png`, `B2_…`, `B3_…`.

| Case | How far the test photo's middle is from the original's middle | Me (after Step 6) | Friend (after LM) |
|---|---|---|---|
| B1 small shift | 50 px (inside my box) | 1.15 px off ⚠️ | **0.001 px** ✅ |
| B2 big shift | 106 px (outside my box) | 303 px off ❌ | **0.001 px** ✅ |
| B3 big shift | 100 px (outside my box) | 1449 px off ❌ | **0.009 px** ✅ |

(Picture: `results/step8_comparison.png` – left panel shows my search box and where
B1, B2, B3 really are.)

**What we learn:**
1. **Big shift → my method fails, friend's works.** Expected: my search box is too small.
2. **B1 (stretch):** my optimizer stopped at 1.15 px, theirs reached 0.001 px.
   I checked why: they start blurrier (blur 4 → 2 → 1 → 0, mine 2 → 1).
   Blurry first = "big smooth hill", easier to walk down blindfolded.
   **When I tried their blur steps (4, 2, 1, 0.5) in my optimizer, mine also got 0.004 px.**
   (I did not change my Step 6 yet – see IDEAS.md.)
3. A first try (spot 186 px away) where the original's middle was **outside** the test
   photo: **both** methods failed. That is my friend's limit (they say so in their notebook).

---

## 6. What my friend did better / what I did better

**My friend did better:**
- Follows the paper/slide 11 more exactly (cross-correlation, search the whole test photo).
- Works for **big shifts**.
- More realistic test photos (sharp zoom, noise, **stretch**).
- Shows the paper's main point clearly: log-polar alone ≈ 5 px, LM alone ≈ 300 px (fails),
  both together ≈ 0.04 px.
- Nice teaching demo: plain polar first (mandrill turned 90° by sliding rows), formulas
  from the paper (Eq. 1–5), and a "try it yourself" cell.
- Optimizer with more blur levels → more robust.

**I did better:**
- **Faster** (about 2.5× for the search).
- Phase correlation + sub-pixel → finer turn/zoom numbers (not limited to whole steps).
- **5 test cases** with an answer key and tables (they tested 1 case + 1 "try it").
- Shows **why** the center search is needed (Step 3 alone fails on shifted photos).
- Proof that turn = slide down, zoom = slide right (Step 2).
- Wrote down **bugs and fixes** (turn sign, measuring error only on visible part,
  warpAffine rounding, edge trimming) – good for the report discussion.
- Notes files: journal, tests table, ideas, Q&A, report notes.

---

## 7. Limits of this comparison
- My friend's photos (mandrill, Shepard Hall) were not in the upload (the notebook loads them
  from `../images/`), so I could not run their notebook exactly. Instead I made
  friend-style tests from my photo.
- Times were measured on the cloud computer, not my Mac (compare them only with each other).
- All test angles are whole degrees, which helps whole-step methods (like my friend's).

## 8. Ideas taken from my friend (also in IDEAS.md)
- Use blur steps 4 → 2 → 1 → 0.5 in my optimizer.
- Make my search box bigger, or search the whole picture coarsely first.
- Add the "optimizer alone fails" test.
- Add noise + stretch to my test photos.
