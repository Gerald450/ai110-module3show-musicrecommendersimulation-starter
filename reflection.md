# Reflection: Comparing User Profiles

This document compares how the recommender behaved across six test profiles — three standard and three adversarial — and explains what each comparison reveals about the scoring logic.

---

## Standard Profiles

### Profile 1 vs Profile 2 — High-Energy Pop vs Chill Lofi

These two profiles are near-opposites, and the system handled them correctly in broad strokes: pop/intense songs dominated the first ranking, lofi/chill songs dominated the second. What is interesting is *why* specific songs won within each group.

For **High-Energy Pop**, *Gym Hero* beat *Sunrise City* despite both being pop songs with mood matches. The difference came entirely from the numerical features: Gym Hero's energy (0.93) and tempo (132 BPM) were closer to the targets (0.90, 130 BPM) than Sunrise City's (0.82 energy, 118 BPM). The genre and mood bonuses put both songs in the same tier; the numerical features decided the order within that tier.

For **Chill Lofi**, *Library Rain* beat *Focus Flow* even though Focus Flow had a slightly better valence match. Library Rain won because it achieved a *perfect energy match* — its energy value (0.35) was exactly equal to the target (0.35), contributing the maximum 1.0 energy point. Focus Flow's energy (0.40) left 0.05 on the table. This shows that **energy is the decisive tiebreaker** when genre, mood, and other features are close.

**Key takeaway for a non-programmer:** Imagine sorting through resumes. If a job requires "five years of experience" and two candidates both have that, you then compare their other qualifications. That is what the system does — genre and mood narrow the field, and the numerical features pick the winner.

---

### Profile 2 vs Profile 3 — Chill Lofi vs Deep Intense Rock

These profiles show how tempo functions differently at different energy levels. For the Chill Lofi profile, tempo differences of ±5 BPM (around a target of 75) mattered enough to separate the top three songs. For the Deep Rock profile, the tempo difference between *Storm Runner* (152 BPM) and *Iron Cathedral* (168 BPM) was decisive even though both are heavy, high-energy songs — Storm Runner ranked first specifically because 152 is closer to the target of 155, not because it was more "rock."

This is a limitation: **the system does not understand that 168 BPM heavy metal might feel more correct to a metal fan than 152 BPM rock, even if the math says otherwise.** Numerical proximity does not equal perceptual correctness.

---

## Adversarial Profiles

### Profile 4 — Conflicting Preferences (High Energy + Melancholic Mood)

This is the most revealing failure case. The user asked for high-energy metal with a melancholic mood. There is no such song in the catalog — the only melancholic song is *Broken Compass*, a low-energy country track.

The result: *Iron Cathedral* (metal, intense) ranked first with a score of ~4.77, beating *Broken Compass* (country, melancholic) at ~3.27, even though *Broken Compass* was the only song that matched the requested mood. Genre weight (2.0) plus energy proximity outscored the mood bonus (1.0) plus better-matching numerical values on *Broken Compass*.

**What this means:** When a user's preferences conflict — wanting an emotional quality that tends to appear only in low-energy music while also wanting high energy — the system silently resolves the conflict in favor of whichever preference has more point weight. It does not warn the user that their preferences are contradictory, and it does not attempt to balance them. A real system like Spotify would likely surface a "we could not find a perfect match" message, or try to blend the two preference signals differently.

---

### Profile 5 — Extremely Narrow (Classical Only)

With only one classical song in the catalog (*Morning Prelude*), this profile exposed the cold-start problem clearly. The first result scored ~5.98 — an almost-perfect match. The second through fifth results scored below 3.0 and were songs like *Spacewalk Thoughts* (ambient) and *Library Rain* (lofi) — unrelated genres that happened to have similar energy and tempo values.

**What this means:** The system has no concept of "I could not find enough songs you would like, so I will not pad the list." It always returns K results, even when most of them are effectively random from the user's perspective. A real recommender would either expand the catalog, lower the threshold for what counts as a recommendation, or honestly show fewer results.

---

### Profile 6 — Neutral / Average Everything

Setting all numerical targets to the middle of the scale (energy 0.50, tempo 100, valence 0.50) exposed how heavily the categorical features drive rankings. *Sunrise City* ranked first not because it was numerically close to the targets — it was actually fairly far (energy 0.82, valence 0.84) — but purely because it matched both the genre ("pop") and mood ("happy") bonuses, worth a combined 3.0 points.

The second through fifth results were songs that matched the genre or mood but not both, and their rankings were spread across very different styles (country, r&b, jazz) purely because their numerical features happened to sit near the average target values.

**What this means:** A neutral profile does not produce neutral recommendations — it produces genre-anchored recommendations with numerically mid-range songs filling in the remaining slots. Users with genuinely eclectic tastes are poorly served.

---

## Sensitivity Experiment — Energy Weight Doubled, Genre Weight Halved

When genre weight was cut from 2.0 to 1.0 and energy weight doubled from 1.0 to 2.0, the High-Energy Pop profile kept the same top two songs (*Gym Hero*, *Sunrise City*) but their scores dropped relative to non-pop songs. *Storm Runner* (rock, intense, energy 0.91) rose from rank 4 to rank 3, overtaking pop-adjacent songs that had weaker energy matches.

**Is this more accurate or just different?**

More *acoustically* accurate — the top 3 songs genuinely share the energy profile the user described. But less *genre-coherent* — a user who said "I want pop" would now get a rock song in their top 3. Whether this is correct depends on what the user actually values. If someone uses genre as a shortcut for a sound profile (bright, produced, energetic), the experiment improves results. If they literally want songs from the pop genre, it is a regression.

This is the core tension in all recommender systems: **features are proxies, not ground truth.** Adjusting weights does not make the system more accurate in an absolute sense — it makes it more accurate for a specific interpretation of what the user wants.

---

## Overall Observations

1. **Genre weight dominates.** In almost every profile, the top 2 results were genre matches. Songs without a genre match rarely broke into the top 2 unless the user set extreme numerical targets.
2. **Energy is the strongest numerical discriminator.** Across all profiles, energy proximity separated songs within the same genre+mood tier more reliably than tempo or valence.
3. **Mood is fragile.** A single vocabulary mismatch silently zeroes out 1.0 point. The conflicting profile showed that mood can be completely overridden by genre + energy.
4. **The system always returns K results**, regardless of how poor the lower-ranked matches are. For narrow profiles, results 3–5 are often misleading.
