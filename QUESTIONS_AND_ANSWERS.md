# Questions and Answers

My own questions while doing the workshop, with simple answers.

---

## Q1. In Step 2, what did we do "manually"?

We did NOT let the computer find anything. **We already knew the answer**
(from `results/test_cases.json`), so we told the program exactly how far to slide.

What the program did, step by step:
1. Unroll the original picture (log-polar).
2. Unroll test1 (log-polar).
3. **We calculated** how far it should slide, using the known answer:
   - test1 is rotated 30°  → 30 / 360 × 360 rows = **30 rows** (−30 = up, because of OpenCV's y-axis)
   - test2 is zoomed ×1.5   → log(1.5) on the log ruler = **17.5 columns** right
4. Slide the original's unrolled picture by that amount.
5. Compare it with test1's unrolled picture → difference 27.4 → **2.0** (almost the same).

So Step 2 only **proved the idea** ("rotation = slide, zoom = slide").
It is like checking a math answer when you already have the answer key.

---

## Q2. In Step 3, what does the computer do by itself?

Now the program does **NOT** get the answer. It must find the slide itself.

1. Unroll the original and the test picture (same as Step 2).
2. **Try every possible slide** – every number of rows up/down (360 options)
   × every number of columns left/right (256 options) = **92,160 slides**.
3. For each slide, give a **score**: how well the two unrolled pictures match.
4. Keep the slide with the **highest score**.
5. Turn it into answers:
   - rows slid  → rotation angle  (−30 rows → 30°)
   - columns slid → zoom           (17.1 columns → ×1.49)

Scoring 92,160 slides one by one is slow, so we use **phase correlation**:
a math trick (Fourier transform) that scores **all slides at once**.
The answer is the same as trying them one by one, just much faster.

---

## Q3. Does Step 3 find the CENTER of the picture?

**No.** Step 3 does **not** search for the center.
It always unrolls both pictures around the **middle of the picture** (209, 312).

- This is fine for test1 and test2, because they were only rotated / zoomed
  **around the middle**, so the middle is still the same spot of the city.
- For test3, test4 and test5 the picture was also **shifted**, so the middle
  of the test picture is now a **different spot of the city**.
  Both pictures get unrolled around different spots → they don't match well.

**Finding the right center is Step 4.**

---

## Q4. What is the "peak"?

The **peak = the highest score** in the score map = how strongly the best
slide matches. It tells us **how sure** the program is.

Small 1-D example (one row of pixels):
```
Picture 1:  0 0 5 9 5 0 0 0
Picture 2:  0 0 0 0 5 9 5 0
```
| Slide | Score |
|---|---|
| 0 | 25 |
| 1 | 90 |
| 2 | **131** ← highest = the peak |
| 3 | 90 |

The best slide is 2, and the peak value is 131.

In phase correlation, scores are scaled so that:
- **peak = 1.0** → the two pictures are exactly the same after sliding (perfect)
- **peak ≈ 0** → nothing matches, the "best" slide is basically a guess

Our results:
| Test | Peak | Meaning |
|---|---|---|
| test1 | 0.85 | very sure (clean map, one bright dot) |
| test2 | 0.70 | sure (a bit lower: zoom pushed some picture off the edge) |
| test3–5 | 0.03–0.04 | very unsure (noisy map, faint dot) – picture is shifted |

In `results/step3_peaks.png`, the peak is the **bright dot inside the circle**.

---

## Q5. "Off by 1–2" – off by what? The center?

**No, not the center.** It is the error in the **rotation angle**, in **degrees**.

| Test | True angle | Found angle | Error |
|---|---|---|---|
| test3 | 45° | 46.15° | 1.15° |
| test4 | 135° | 137.34° | 2.34° |
| test5 | 90° | 88.02° | 1.98° |

The zoom also has an error (in **percent**): test5 found ×1.26 instead of ×1.20 → 5% off.

Why is it close but not exact? The shift is small (10–25 pixels), so the two
centers are only a little apart → the unrolled pictures still look a bit alike.
But the match is weak (low peak), so the answer is not exact and not reliable.
With a bigger shift it could be completely wrong.

---

## Q6. Summary of Steps 2, 3, 4

| Step | Center used | Slide | Who knows the answer? |
|---|---|---|---|
| 2 | middle of picture | **we calculate it** from the answer key | we do (check only) |
| 3 | middle of picture | **computer finds it** (phase correlation) | computer finds rotation + zoom |
| 4 | **computer searches** many centers | computer finds it for each center | computer finds rotation + zoom + shift |

---

## Q7. Simple summary of Steps 1–3 (example: test1, photo turned 30°)

**Big goal:** photo 2 is turned, zoomed and moved. The computer must tell us how much.

**Step 1 – make a puzzle with an answer key.**
We turned the photo 30° ourselves (test1) and wrote the answer in `test_cases.json`.
Like a teacher writing a test AND the answer sheet.

**Step 2 – unroll and check the idea (using the answer key).**
1. Unroll the original (log-polar) – like peeling a can label flat.
2. Unroll test1.
3. They look the same, just one is moved up.
4. WE calculate from the answer key: 30° = move up 30 rows.
5. Move the original's flat picture up 30 rows and compare → difference 2.0 (almost identical).
→ Turning = flat picture moves up/down. Zooming = flat picture moves right.
→ The computer found NOTHING here. We gave it the answer. We only proved the idea.
Like a teacher checking that the answer sheet is correct.

**Step 3 – the computer finds it by itself (no answer key).**
1. Put flat picture 2 on top of flat picture 1 (like two transparent sheets).
2. Try every position (92,160 of them), give each a score.
3. Keep the best one (the peak): "up 30 rows, right 0 columns".
4. Convert: 30 rows → turned 30°, 0 columns → zoom ×1.0.
5. Grade with the answer key → exactly right.
Like the student solving the test alone.

| | Step 2 | Step 3 |
|---|---|---|
| Who decides how far to move? | we do (answer key) | the computer (tries all, picks best) |
| Purpose | prove the idea | actually solve the problem |
| Output | "yes, they match" | "turned 30°, zoom ×1.0" |

**Why test3/4/5 are not solved yet:** both photos are unrolled around their own MIDDLE.
test3 was also moved 20 px, so its middle is a DIFFERENT building → the flat pictures
don't match well → low peak, unsure answer. Step 4: try many middles, keep the best.

**One line each:**
- Step 1: make the puzzle + write the answer.
- Step 2: show "turned" = "flat picture moved" (using the answer).
- Step 3: computer finds how far it moved → turn + zoom.
- Step 4: computer also finds where the middle is → shift.

---

## Q8. What does "unrolling" mean?

Unrolling = turning a round view into a flat rectangle (log-polar transform).

How the computer does it – imagine standing on ONE spot of the photo with a laser pointer:
1. Point right (0°). Walk outward along the laser, write down every color you pass
   (sky, sky, building, road...). That list = **row 0**.
2. Turn 1°, do it again → **row 1**.
3. Keep turning, all the way to 359° → 360 rows.
4. Stack the rows → the unrolled picture.
   - each row = what you see in one direction
   - left = close to where you stand, right = far away

Like peeling a can label flat, or turning around in a room and drawing a panorama.

**Key point:** the unrolled picture depends completely on WHERE YOU STAND.
Different spot → different flat picture.

## Q9. Why are test3/4/5 not solved in Step 3?

The program always stands at the MIDDLE PIXEL of each photo, (209, 312).

- **test1 (only turned):** turned around its middle, and the middle doesn't move when
  you spin around it (like the center of a wheel). Middle of original = building A,
  middle of test1 = still building A. Same spot → same view, just starting from
  another direction → flat picture only slides. ✅
- **test3 (turned + moved 20 px):** everything moved 20 px, but the program still stands
  at pixel (209, 312), which now shows building B. Standing on two DIFFERENT buildings
  → every direction shows something slightly different → the flat pictures are
  different pictures, not slid copies → low peak. ❌

Like two people describing the view from a rooftop: same roof → descriptions match
(maybe one started facing another way). Different roofs → they don't match.

**Fix (Step 4):** try many standing spots in the test photo, keep the one whose
flat picture matches best. That spot tells us the shift.

---

## Q10. VERY simple version (no technical words)

**Three words:**
- **Middle** = the center point of a photo. All photos are the same size, so the middle is
  always the same spot on the screen, pixel (209, 312). But WHAT is shown there can differ.
- **Turned** = photo rotated, like turning a paper on a table.
- **Shift / moved** = photo slid sideways or up/down, without turning.

**Example:** a tiny city with a house, a tree, a car. Red dot = middle of each photo.
- Original: dot is on the HOUSE.
- Turned 90°: dot is STILL on the house (spinning doesn't move the center).
- Moved left 45 px: dot is now on the TREE.

**"Unrolling" = describing what you see around the dot, like a clock.**
- Original (on house): 3 o'clock → tree, 7 o'clock → car.
- Turned (on house): everything moved by the SAME number of hours → "turned 90°". Step 3 can do this ✅
- Moved (on tree): a totally different list (things closer, farther, odd directions).
  Can't compare → Step 3 fails ❌

**Middle of which picture?** BOTH. Step 3 stands on the middle of the original AND the middle
of the test photo, then compares the two clock lists.
- only turned → both middles show the same thing (house) ✅
- moved → middles show different things (house vs tree) ❌

**How Step 4 helps:**
1. Stand on the middle of the TEST photo (the tree). Write its clock list. Keep it.
2. In the ORIGINAL, stand on many spots one by one, write a clock list at each.
3. Compare each with the test photo's list.
4. Best match = the spot in the original that is the tree.
   Tree is 45 px right of the original's middle, but at the middle of the test photo
   → the photo was moved 45 px LEFT = **the shift**.
   At that spot the clock lists also give the turn and zoom (like Step 3).

**In 4 lines:**
- Step 1: make test photos we turned/zoomed/moved ourselves + write the answers.
- Step 2: check that "turned" = "clock list moved by the same hours" (using the answers).
- Step 3: computer finds how many hours everything moved → turn + zoom (only if not moved).
- Step 4: computer searches the original for the spot matching the test's middle → shift (+ turn + zoom).

---

## Q11. Checking my understanding (Steps 2–4)

**Words:** Turned = rotated (spun). Zoomed = bigger/smaller. Shifted = MOVED (slid). Moved and shifted are the same.

- **Step 3 finds turned + zoomed, not shifted — why?** It stands on the middle of both photos.
  Shifted photo → middles show different things (house vs tree) → no match. ✅ correct
- **Step 4 finds turned + zoomed + shifted, almost correct?** Yes. Errors: turn < 0.3°,
  zoom < 2%, shift < 2 px. ✅ correct
- **Is Step 4 only searching for the middle?** No. It searches for the MATCHING SPOT and runs
  Step 3 at every spot. Best spot → where it is = shift; Step 3 answer there = turn + zoom.
  **Step 4 = Step 3 + searching for the right spot.**
- **If we find the spot, do we know if it was shifted?** Yes. Best spot = exact middle → not
  shifted (test1, test2). Best spot elsewhere → shifted, distance = how much (test3/4/5).

**Step 2 pictures:**
- `step2_log_polar.png` – "log polar" = official name for the CLOCK-LIST picture.
  Top row: normal photos. Bottom row: clock-list pictures.
  Going down (0→359) = clock direction. Going right = distance from the middle (left close, right far).
- `step2_slide_check.png` – test that "turning = sliding the clock-list picture".
  Left: original's clock-list. Middle: same, slid by the expected amount (from the answer key).
  Right: test1's real clock-list. Middle and right look the same (difference 2.0) → the idea works.
  Step 2 found nothing by itself; it only PROVED the trick so Step 3 can use it.

**One line each:**
- Step 2: prove "turned photo" = "slid clock-list picture" (using answers).
- Step 3: find the slide by itself → turned + zoomed (fails if shifted).
- Step 4: Step 3 at many spots, keep the best → turned + zoomed + shifted.

---

## Q12. Slide, 0–359, slide check, and why log-polar (simple)

(Seen with an interactive demo: little city with tree, car, sun, house; photo A = original,
photo B = turned; C = clock picture of A, D = C slid down, E = clock picture of B.)

**Why 0 to 359?** A full circle = 360 degrees (0°…359°, then back to 0°, like a clock after 11:59).
The clock picture has one row per direction around the dot:
0° = looking right, 90° = looking down, 180° = looking left, 270° = looking up.

**What is "slide"?** Move the whole picture down without changing it. What falls off the bottom
comes back at the top. Example, turn 90°: the tree was at row 0° (right of the dot), after turning
it is at row 90° (below the dot). Tree, car, sun, house ALL move down 90° = a slide.

**What is the "slide check"?** A test that turning = sliding:
1. C = clock picture of the original.
2. Slide C down by the turn amount → D.
3. E = clock picture of the turned photo.
4. D and E look exactly the same → turning really is sliding ✅
This is what "middle and right should look the same" means in `step2_slide_check.png`.

**Why log-polar? Can't we use normal pictures?**
Put normal photos on top of each other: a turned photo gives DOUBLE shapes. Sliding a normal
photo can never fix a turn. With normal pictures the computer would have to try every angle
(1°…359°) × every zoom = thousands of tries (slow).
In the clock picture, turn = slide down, zoom = slide right. Finding a slide is fast and easy.

**Can't we just find the middle in normal pictures?** That only gives the SHIFT, not the turn or
zoom. Step 4 does both: search for the matching spot (shift) + clock pictures there (turn + zoom).

---

## Q13. Clock picture and sliding – the 8-box version (simplest)

(Seen with a demo: 8 things around a dot – tree, road, car, grass, sun, sky, house, cloud.)

**Clock picture** = stand on the dot, look all the way around, write what you see in each direction,
then put it in a ROW:
`0° tree | 45° road | 90° car | 135° grass | 180° sun | 225° sky | 270° house | 315° cloud`
(Real program: 360 directions instead of 8, and each direction also shows near and far.)

**Sliding** = turn the photo 45° → in the row, EVERY box moves 1 place to the right
(the last one wraps around to the start). Same order, just moved along.
`0° cloud | 45° tree | 90° road | 135° car | ...`
Turn 90° → every box moves 2 places.
- Turning = what happens in the normal photo.
- Sliding = what you see in the clock picture. Two views of the same thing.

**Why we care:** the computer is bad at "how much was this photo turned?" but very good at
"how many places did the boxes move?" – try 0, 1, 2... places, see which matches.
Moved 2 places → turned 2 × 45° = 90°. That is Step 3.

**Why check the slide (Step 2)?** Test a trick once where you KNOW the answer before trusting it –
like testing a new calculator with 2 + 2. We knew test1 was turned 30°, moved the original's
clock picture 30 places, it matched → trick works → Step 3 can use it.

---

## Q14. My summary of Steps 2–4 (checked)

- **Step 2** – only a test to prove "turning = sliding". The final program does not need it,
  but keep it for the report: it is the proof that the method is correct. ✅
- **Step 3** – finds turn + zoom, not the shift. ✅
- **Step 4** – tries every SPOT in the original photo near its middle (±60 px), not every row/column
  of the clock picture. At each spot it uses the Step 3 method and gets a score. Best score =
  where the TEST photo's middle is in the original.
- **`step4_search_maps.png`:** `+` = middle of the original (209, 312). Circle = best spot found.
  - Circle on the + → not moved (test1, test2).
  - Circle away from the + → moved; the distance (adjusted for turn and zoom) = the shift.
  - Example test3: + (209, 312), circle (192, 310) → 17 px left, 2 px up in the original.
    Converted with turn 45° and zoom ×1.5 → shift (20, −16). True: (20, −15). ✅

**Summary:** Step 4 tries many spots in the original, uses Step 3 at each, keeps the best spot
(circle). Distance from + to circle (adjusted for turn and zoom) = shift; Step 3 at that spot =
turn and zoom.

---

## Q15. What does Step 5 do? (simple)

Step 4 found HOW each test photo was changed (e.g. test3: turned 45°, zoomed ×1.5, moved (20, −15)).
Step 5 does the OPPOSITE: un-move, un-zoom, un-turn. If the numbers are right, it fits exactly
on top of the original. (Like undoing a turn + crop on a phone photo.)

**Red/cyan overlay:** original = red, test photo = cyan.
- gray = lined up ✅
- red + cyan double edges = not lined up ❌
- plain red = part of the original the test photo doesn't show (cut off by zoom)

**Numbers:** "before" = difference before fixing (45–110), "after" = after fixing (4–16),
"pixels off" = how far from perfect (under 1 px for most, 2 px for test4).

**Why test4 is worst:** turned 135° AND zoomed ×2; Step 4 found ×1.96 instead of ×2.00.
A small zoom error grows far from the middle, like a slightly wrong-size photocopy.
Step 6 (optimizer) fixes this kind of small leftover error.

---

## Q16. What does Step 6 (optimizer) do? (simple)

Step 4 = good guess, not perfect (test4 zoom ×1.96 instead of ×2.00).
Optimizer: start from that guess → change the numbers a tiny bit → better match? keep it.
Worse? try another direction → repeat until nothing helps. Like tuning an old radio.

"Better match" = SSD: for every pixel, (brightness difference)², add all up. Smaller = better.
6 knobs (a1..a6) like the paper – can also fix slant.

Why Step 4 first? The optimizer is like walking blindfolded downhill: it only finds the lowest
point if it starts nearby. That is the paper's main idea: rough guess (log-polar) + fine-tuning.

Result: all tests under 0.05 px from perfect (test4: 2.04 → 0.01 px, zoom exactly ×2.0000).

## Q17. What do the B and C tests mean? (simple)
They are 8 extra, HARDER test photos (my own tests are test1–test5).

**B = "paper-style" (friend-style) tests.** They copy the paper's own example (Fig. 3), which my
friend also used: the photo is turned **201° clockwise**, **zoomed ×2.13**, slightly **stretched**
(the paper's numbers) and gets a little camera noise. B0–B3 only differ in **how far it was moved**:

| Test | How far moved | Special |
|---|---|---|
| B0 | 186 px | the original's middle is NOT in the test photo (old me and my friend both failed) |
| B1 | 50 px | small move |
| B2 | 106 px | big move |
| B3 | 100 px | big move, the test photo's middle is in empty sky (hardest) |

**C = extra tests** to check the new version is not just lucky: other turns and zooms, big moves,
no stretch.

| Test | Turn | Zoom | How far moved |
|---|---|---|---|
| C1 | 300° | ×3.0 | 90 px |
| C2 | 60° | ×1.3 | 108 px |
| C3 | −120° | ×1.8 | 114 px |
| C4 | 10° | ×1.1 | 192 px |

Pictures: `images/generated/B0_friend_style.png` … `C4_extra.png`, and `results/step7_hard_tests.png`.

## Q18. Why are some numbers a tiny bit different on my Mac?
Different computers round numbers very slightly differently (e.g. B3: 0.027 px on my Mac,
0.044 px on Claude's computer). All verdicts (OK / BAD) are the same, so the conclusions do not
change. When the optimizer gets LOST (optimizer alone), where it ends up is almost random,
so those big numbers can differ a lot (2,037 vs 15,058 px) – both just mean "lost".

## Q19. Is zooming in / out in the paper? How far does my method work?
**The paper:** yes, zoom is the main point. It says log-polar handles up to **×10** zoom, and
"in practice" up to **×4**. Its examples: ×4 (mandrill) and 0.469 (= ×2.13 the other way round).
It doesn't test "zoom out" separately, because zoom out = zoom in with the two pictures swapped.

**My method (tested in `step8_zoom_limits.py`):** works from **×0.5 to ×2** (×3 only sometimes). Fails at ×4 and more,
and at ×0.35 and less. So for big zoom the paper's claim is better than my method right now.

**Why (simple):** imagine finding a small close-up photo of ONE window in a photo of the whole city.
- My rough search first makes the city photo 4× smaller to be fast. At ×4 zoom the window
  becomes ~3 pixels – you can't recognise it any more, so the right spot never makes the short list.
- At ×6+ the close-up itself is a blurry blown-up piece of my small photo (a real camera zoom
  would show real detail).
- Zoom out ×0.25: the test photo is 94% black with a tiny city in the middle.

## Q20. Why do zoom in and zoom out fail? (simplest)
Finding a close-up of ONE building in a photo of the whole city:
- **Zoom in ×3 – ×5:** to be fast, the first rough look uses a 4× smaller city photo. The building
  is then a tiny 22 × 22 blob, but the test photo shows it big → too different to recognise.
  (Fix tested: also shrink the test photo, so both are the same size.)
- **Zoom in ×6+:** the test photo is a tiny piece of my small photo blown up → very blurry,
  almost nothing left to match.
- **Zoom out ×0.35 and less:** the test photo is mostly black with a tiny city inside.
  (Fix tested: swap the photos and look for the city photo inside the test photo.)
Picture: `experiments/zoom_fix/why_zoom_fails.png`.

## Q21. Why do we need log-polar? What is "sliding"? (with picture)
Picture: `explanations/log_polar_explained.png` (make it again: `python explanations/make_log_polar_explained.py`).

**Sliding** = moving a whole picture in one direction, every pixel by the SAME amount
(like sliding a sheet of paper across the table). A slide is easy to find: try every slide, keep the best match.

**The problem:** turning or zooming a photo is NOT a slide. When you turn a photo, pixels near the
middle move a little, pixels at the edge move a lot, in different directions. So you can't just slide
photo 2 back over photo 1.

**The clock picture (log-polar)** = re-draw the photo as seen from the middle:
- each ROW = one direction (360 rows = 360 degrees, like the hand of a clock going around),
- each COLUMN = how far from the middle (on a log ruler: 1, 2, 4, 8, 16 … are equally spaced).

**Why it helps:**
- Turn the photo 45° → everything is now 45° further around the clock → the whole clock picture
  slides 45 rows (pie example, row 1 of the picture: same colour stripes, just one stripe lower).
- Zoom the photo ×2 → everything is twice as far from the middle → on the log ruler "twice as far"
  is always the same step → the whole clock picture slides right by one step (rings example, row 2).
- My photo: test1 turned 30° → the tower moves from row 307 to row 277 (30 rows);
  test2 zoomed ×1.5 → the tower moves from column 229 to 247 (17.5 columns).

So log-polar turns the HARD problem (turn + zoom) into the EASY problem (find a slide).
How many rows it slid = the turn; how many columns = the zoom.
Why the log? Without it, zoom would STRETCH the stripes (near ones a little, far ones a lot) instead
of sliding them. The log makes every "×2" the same width, so a zoom becomes a slide.

**Script parts 3 and 4 in one sentence each:**
- Part 3: the clock picture turns a turn into a slide down and a zoom into a slide right.
- Part 4: phase correlation tries every slide at once and finds the best one (test1: 30 rows = 30°;
  test2: 17.1 columns = ×1.487). For moved photos (test3–5) it fails, because the middle of the test
  photo shows a different place, so the two clock pictures are of different things.

## Q22. The Step 3 picture: what is the dot, the peak, phase correlation, 360, 256, 376?
- **Each box** = a map of every possible slide (up/down = rows slid = turn, left/right = columns
  slid = zoom). **The dot in the circle** = the best slide. Its position gives turn and zoom
  (test1: 30 up, 0 right = 30°, no zoom). The dot does NOT measure the move.
- **Peak** = brightness of the best dot = how well the clock pictures match (1 perfect, 0 none).
  Bigger = more sure. test1 0.85, test2 0.70, test3–5 0.03 (moved photos: middles show different
  places, so no slide matches). Step 4 keeps the standing spot with the highest peak.
- **Phase correlation** = turn both pictures into waves (Fourier), compare only WHERE each wave sits
  (the phase), every wave "votes" for a slide; the bright dot is where the votes agree. All slides
  at once, very fast, sharp answer.
- **360 rows** = one per degree (1 row = 1° of turn).
- **376 px** = the farthest point from the middle = a corner: √(209² + 312.5²) = 376 (half the diagonal),
  code: `np.hypot(w / 2, h / 2)`.
- **256 columns** = distance steps from 1 to 376 px on a log ruler: each column = 376^(1/256) = ×1.023
  = 2.3% farther. Zoom ×2 = 30 columns; ×1.5 = 17.5 columns. In Step 4 (180 px): 2.0% per column.

## Q23. Is 256 columns (2.3% per column) better?
256 is a CHOICE (balance), and 2.3% is the RESULT of choosing 256 (with 376 px), not the reason.
Test (Step 3, test2 = zoom ×1.5, time per try on Claude's computer):

| Columns | 1 column = | test2 zoom error | Time per try |
|---|---|---|---|
| 64 | 9.7% | 2.69% | 1.5 ms |
| 128 | 4.7% | 0.40% | 2.3 ms |
| 256 | 2.3% | 0.88% | 4.5 ms |
| 512 | 1.2% | 0.29% | 9.7 ms |
| 1024 | 0.6% | 0.36% | 20.3 ms |

- More columns = finer steps but SLOWER (double columns ≈ double time).
- From 128 columns on, the error stays around 0.3–0.9%: other things limit it (the zoomed photo is
  re-calculated = a little blurry, black corners), and the parabola already reads between columns.
- So 256 is a reasonable choice, not the proven best; the optimizer (Step 6) makes it exact anyway.
- Speed matters in Step 4: it makes thousands of clock pictures per test.
- Turn (test1) was exactly 30.00° for every number of columns (columns only affect zoom).

## Q24. Phase or cross-correlation? What does the Step 4 picture show? What does Step 4 do?
- **The Step 4 picture** shows the rough score of EVERY spot for each method. The 6 best spots of each
  method are not marked; the cyan circle = the ONE final best spot after the exact search.
- **The teacher's slide 11 and the paper use cross-correlation.** Phase correlation was my own choice
  (made while building the project): it is a standard method (the paper mentions it, ref [2] Kuglin & Hines,
  used in Fourier–Mellin methods) and gives a sharper peak. My final Step 4 uses BOTH.
- Step 2 uses neither: it only unrolls the pictures and checks the slide with the known answer.
- **Cross-correlation in Step 3 (tested, Step 3 settings):**

| Test | True | Phase correlation | Cross-correlation |
|---|---|---|---|
| test1 | 30°, ×1.0 | 30.0°, ×1.000 | 30.0°, ×1.000 |
| test2 | 0°, ×1.5 | 0.0°, ×1.487 | 0.0°, ×1.483 |
| test3 | 45°, ×1.5 | 46.1°, ×1.519 | 15.0°, ×2.050 (wrong) |
| test4 | 135°, ×2.0 | 137.3°, ×2.060 | 127.0°, ×1.123 (wrong) |
| test5 | 90°, ×1.2 | 88.0°, ×1.260 | 112.0°, ×0.675 (wrong) |

  Both find turn + zoom for test1–2; NEITHER can handle the moved photos (3–5), because the problem
  is the different middle, not the matching method. Cross-correlation's best slide is only a little
  better than the 50th best (0.29 vs 0.26: a gentle hill); phase correlation gives a clear spike.
- **Step 4 exactly:** (1) pick the test photo's standing spot (middle + most detailed spot);
  (2) rough search: score every spot of the 4× smaller original with both methods; (3) each method
  keeps its 6 best spots (12); (4) exact search around those 12 at full size, best peak wins → that
  spot gives the MOVE, the slide there gives TURN + ZOOM; (5) put the photo back for each standing spot
  and keep the answer that really lines up best.

## Q25. Step 4: which "middle"? Where are the 12 places and the cyan circle?
Picture: `explanations/step4_explained.png` (test4).
- "The middle" = the middle of the TEST photo (red dot). It stays fixed. Question: where is THIS
  building in the original?
- The search happens in the ORIGINAL photo. The 12 short-listed places (orange dots) and the cyan
  circle (best place) are all in the ORIGINAL.
- Compare the cyan circle with the ORIGINAL's middle (white +, at 209, 312):
  test4 circle at (211, 332) = 20 px below. That gap, turned 135° and zoomed ×2, gives the move
  (−24, 30); true (−25, 30). Not moved (test2) → the circle sits exactly on the original's middle.
- Order: shrink BOTH photos 4× → both methods score every place → 6 best each = 12 → full size,
  every pixel around the 12 with phase correlation → best = cyan circle → put the photo back to check.

