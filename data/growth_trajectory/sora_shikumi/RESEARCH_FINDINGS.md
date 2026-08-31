# @sora_shikumi — Growth Trajectory Research Findings

Collected 2026-08-31 UTC. Requested up to 1,000 roots; profile exhausted at 492 unique roots / 492 valid texts, spanning 2026-06-01 to 2026-08-31.

This is observational evidence. Engagement score is an internal comparison proxy built from public like/reply/repost/quote counts. No view count, buyer data, mentor identity, or causal control is available.

## 1. Fast adaptation is visible, but not monotonic improvement

A rolling 25-post change detector found an early change around post 26 (2026-06-07): median engagement moved from 8 to 21 in the adjacent windows.

The important content observation is that the successful post did not introduce an entirely new worldview. It sharpened an already emerging format: concrete money problem → dialogue simulation → contrast → explanation → action/CTA. The preceding post already used a similar dialogue structure, so this is better interpreted as rapid iteration/refinement than a clean one-time intervention.

Do not infer a mentor from this alone.

## 2. Best sustained regime was mid-trajectory, not the latest regime

50-post rolling blocks, oldest → newest, engagement medians:

- 1–50: 11
- 51–100: 12
- 101–150: 15
- 151–200: 13
- 201–250: **22.5**
- 251–300: 17
- 301–350: 13
- 351–400: 14
- 401–450: 14
- 451–492: 12.5

The strongest sustained block was posts 201–250 (2026-07-09 to 2026-07-19), not the newest content.

Therefore, “latest creator behavior = best practice” is false for this corpus.

## 3. Commercialization increased while sustained engagement later declined

Commercial/offer CTA feature rate:

- oldest 50: 0.16
- 201–250 peak block: 0.92
- 251–300: 0.78
- 301–350: 0.72
- 351–400: 0.92
- 401–450: 0.66
- newest block: 0.762

Important distinction: save/follow engagement CTAs were already common early. The later shift is mainly toward product/note/profile conversion behavior, not simply “more CTA of every kind.”

The co-occurrence of heavier commercial CTA and lower later engagement is not causal proof. Possible explanations include saturation, audience fatigue, campaign lifecycle, content mix, account-level distribution changes, or product focus.

Implementation implication: never copy a creator’s late-stage conversion density into Normal Feed as a default rule.

## 4. Surface optimization also overshot

Short-line rate rose sharply in later periods. Example:

- oldest 50: 0.320
- 201–250 peak: 0.239
- 301–350: 0.627
- 401–450: 0.528
- newest 50: 0.533

The highest sustained block was not the shortest-line / most fragmented block.

Implementation implication: readability formatting is a tool, not a target metric. Do not optimize “Threads-looking” formatting independently of thought quality.

## 5. Science language was reduced substantially

Science-term rate:

- oldest 50: 0.80
- peak 201–250: 0.38
- newest 50: 0.26

This does not prove science language hurts performance. It does show that high science density is not necessary for the account’s strongest sustained regime.

Several posts also make unsupported neuroscience/RAS claims. For Life-OS, P3 Truth Gate remains superior to copying this authority mechanism.

## 6. Category remained strong while content purpose changed

Spiritual-category rate stayed high overall (0.866) and rose from 0.72 in oldest 50 to about 0.9 in newest 50.

The account did not grow by drifting into generic psychology. It stayed category-recognizable while changing delivery, product density, and subtopics.

This supports P3 Category Gate: variation should happen inside a recognizable category rather than by abandoning it.

## 7. Winning microformats should be learned functionally, not frozen

Observed high-engagement functions include:

- dialogue simulation: person ↔ universe/subconscious
- concrete money/relationship scenario
- authority/person-name hook
- numbered diagnosis/checklist
- contrast / belief flip
- one immediate action
- product or continuation CTA

But these formats were repeatedly reused and later did not sustain the mid-period engagement regime.

Rule: a winner earns a controlled retest, not permanent promotion to universal template.

## 8. Relationship to @osabori_space_human

Functional feature-vector similarity was high from the first 50-post block and increased modestly later. Lexical 8-character overlap with @osabori_space_human was consistently above the Dara historical control in most blocks.

Shared phrases/formulas included examples such as:

- 脳科学的に見ても
- 引き寄せがうまく…
- 脳のフィルターが…
- 豊かさを受け取る…
- 追いかけるのをやめ…

This is evidence of shared language/formulas, not evidence of a specific relationship. Plausible explanations include same-niche convergence, common sources, imitation, common training material, or mentorship.

Do not label a mentor without independent evidence.

## 9. Market-learning rules extracted

1. Analyze external creators chronologically, not only as one averaged corpus.
2. Separate discovery, exploitation, conversion, and saturation regimes.
3. Use rolling medians and windows; do not let one viral post define the rule.
4. A winning format gets a retest budget, not permanent canonical status.
5. Track commercial CTA separately from engagement CTA.
6. Watch for saturation: rising repetition/promotion with falling rolling outcomes.
7. Preserve category recognition while rotating Thinking Mode and surface form.
8. Copy functions, never biography, persona, distinctive phrasing, or unsupported authority claims.

## 10. Data locations

- `raw.json` — 492 raw roots
- `annotated.json` — feature annotations
- `trajectory_analysis.json` — windows/change points/reference similarity
- `TRAJECTORY_REPORT.md` — compact machine report
- `deep_dive.json` — lexical/formula/change-point content analysis
- `DEEP_DIVE.md` — human-readable deep dive
