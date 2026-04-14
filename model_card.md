# Model Card: Music Recommender Simulation

---

## 1. Model Name

**TuneMatcher 1.0**

A content-based music recommender that scores songs against a user's taste profile and returns the closest matches — built as a learning simulation of how platforms like Spotify decide what to play next.

---

## 2. Goal / Task

TuneMatcher tries to answer one question: *"Given what a user likes, which songs in the catalog are they most likely to enjoy?"*

It does not predict a rating or a play count. Instead, it computes a compatibility score between a user's preferences (genre, mood, energy level, tempo, and emotional tone) and each song's features. Songs are then ranked by that score, and the top results are returned as recommendations.

The system is optimizing for **relevance** — songs that feel like a match — not for novelty or diversity. That distinction matters because a system that only optimizes for relevance tends to keep recommending things the user already knows they like, rather than helping them discover something new.

---

## 3. Data Used

The catalog is stored in `data/songs.csv` and contains **19 songs**.

Each song has the following features:

| Feature | What it represents |
|---|---|
| `genre` | Musical category (e.g., pop, rock, lofi, jazz, metal) |
| `mood` | Emotional tone label (e.g., happy, chill, intense, melancholic) |
| `energy` | How intense or active the song feels, on a scale of 0.0 to 1.0 |
| `tempo_bpm` | Beats per minute — roughly how fast the song moves |
| `valence` | How positive or upbeat the song sounds, 0.0 (dark) to 1.0 (cheerful) |
| `danceability` | How easy the song is to dance to, 0.0 to 1.0 |
| `acousticness` | How acoustic (vs. electronic/produced) the song sounds, 0.0 to 1.0 |

**Genres represented:** pop, lofi, rock, ambient, jazz, synthwave, indie pop, r&b, country, hip-hop, soul, metal, classical

**Moods represented:** happy, chill, intense, relaxed, focused, moody, melancholic, peaceful

**Limitations of this dataset:**

- 19 songs is tiny. A real system like Spotify operates on a catalog of tens of millions.
- The data is hand-crafted and synthetic — feature values were assigned manually, not measured from real audio.
- Several genres appear only once (classical, country, soul, r&b). Users who prefer those styles get one strong match and then fall through to unrelated songs.
- The mood labels are simplified. Real emotional nuance in music is much harder to capture with a single word.

---

## 4. Algorithm Summary

Here is how TuneMatcher scores a single song, explained without code:

**Step 1 — Genre check (+2.0 points)**
If the song's genre matches one of the user's preferred genres, it earns 2.0 points. If not, it gets nothing for genre. Genre is the single biggest factor in the score.

**Step 2 — Mood check (+1.0 points)**
If the song's mood label matches one of the user's preferred moods, it earns 1.0 point. This is an exact match — "intense" and "energetic" are treated as completely different even though they feel similar.

**Step 3 — Numerical similarity (up to ~4.0 more points)**
For each numerical feature the user specified — energy, tempo, and valence — the system measures how close the song's value is to the user's target. A song with energy 0.90 scores nearly full points against a user who wants 0.90, but a song with energy 0.30 scores much less. The closer the match, the higher the points, up to 1.0 per feature. Acousticness works the same way but contributes a smaller maximum of 0.5.

**Step 4 — Sum and rank**
All the points are added together. Every song gets a total score, and the songs are sorted from highest to lowest. The top 5 (or however many the caller asks for) are returned.

The maximum possible score is roughly **6.5** (2.0 genre + 1.0 mood + 1.0 energy + 1.0 tempo + 1.0 valence + 0.5 acousticness).

---

## 5. Observed Behavior and Biases

**Genre dominates.** Because genre is worth 2.0 points on its own, a song that matches the genre but is otherwise mediocre will almost always rank above a song that is a perfect numerical match but in the wrong genre. In testing, the top two results for every standard profile were genre matches — regardless of how well or poorly they matched energy, tempo, or valence.

**Filter bubble effect.** Because only genre-matching songs consistently appear in the top results, users tend to see the same small set of songs recommended repeatedly. A pop fan will always get the two pop songs. A lofi fan will always get the three lofi songs. The system has no mechanism to introduce variety or suggest that a jazz-adjacent song might suit someone who likes relaxed lofi.

**Imbalanced catalog.** Some genres appear 3–4 times (lofi, pop, synthwave) while others appear only once (classical, country, soul). This means users of majority genres get richer, more differentiated recommendations, while minority-genre users get one good match and then noise.

**Mood matching is brittle.** The match is exact string comparison. A user who prefers "calm" or "energetic" will score zero mood points across the entire catalog, because neither of those words appears in the dataset. The system does not warn about this — it just silently ignores the preference.

**Conflicting preferences are not handled gracefully.** When tested with a user who wanted both high energy *and* a melancholic mood, the system returned metal songs with no mood match at the top, and the only melancholic song (which was low-energy) ranked third. The system cannot communicate "your preferences are contradictory" — it just quietly picks the side with more point weight.

---

## 6. Evaluation Process

The system was tested with six user profiles.

**Three standard profiles** were designed to represent common, coherent listener types:

- *High-Energy Pop* — wanted upbeat, fast, high-energy pop songs. The system correctly placed *Gym Hero* first and *Sunrise City* second, both pop songs that matched genre, mood, and energy. The remaining ranked songs dropped sharply in score once genre matches ran out.

- *Chill Lofi / Low Energy* — wanted slow, calm, acoustic songs. The top four results were all lofi or ambient genre matches. Among those, *Library Rain* beat *Focus Flow* for first place purely because its energy (0.35) exactly matched the user's target (0.35). Even a 0.05 difference was enough to change the ranking.

- *Deep Intense Rock* — wanted heavy, fast, intense songs. *Storm Runner* (rock) ranked above *Iron Cathedral* (metal) even though Iron Cathedral had higher energy, because Storm Runner's tempo (152 BPM) was much closer to the user's target (155 BPM). This shows that all numerical features contribute to the outcome, not just energy.

**Three adversarial edge-case profiles** were designed to break or stress-test the system:

- *Conflicting preferences* (high energy + melancholic mood): The system surfaced metal songs at the top because genre + energy weight beat the single mood match. The user's actual mood request was effectively ignored.

- *Classical only* (one song in that genre): First result was a near-perfect score (~5.98). Results 2–5 dropped below 3.0 and were acoustically similar songs from completely different genres — not useful recommendations.

- *Neutral / Average everything* (mid-range targets, pop/happy): The genre bonus still drove the ranking. *Sunrise City* ranked first despite being numerically far from "average" because it was the only song with both a genre and a mood match.

**Sensitivity experiment:** Genre weight was halved (2.0 → 1.0) and energy weight was doubled (1.0 → 2.0). For the High-Energy Pop profile, the top two songs stayed the same, but *Storm Runner* (rock) rose from rank 4 to rank 3. The system became more acoustically accurate but less genre-consistent — a user asking for pop received a rock song in their top 3.

---

## 7. Intended and Non-Intended Use

**This system is intended for:**

- Learning how content-based filtering works
- Exploring how scoring weights affect recommendation quality
- Practicing Python and data-driven system design in a classroom or personal project setting
- Thinking critically about bias and fairness in AI recommendation systems

**This system should NOT be used for:**

- Real-world music discovery for actual users — the catalog is far too small and the data is synthetic
- Making decisions about what music artists or labels to promote
- Any production environment or public-facing application
- Drawing conclusions about what makes music "objectively" good or bad — the scores reflect a simplified preference model, not musical quality

---

## 8. Ideas for Improvement

**1. Replace linear distance with a Gaussian (bell-curve) similarity function.**
Right now, a song that is 0.1 away in energy scores only slightly better than one 0.2 away. A Gaussian formula would reward very close matches much more strongly while still giving partial credit to reasonable matches. This would make the system far more discriminating within the same genre.

**2. Expand and balance the catalog.**
Even adding 5–10 songs per genre would dramatically improve results for underrepresented genres like classical and country. Ideally, the dataset would use real audio feature data (Spotify provides this via their API) rather than hand-assigned values, which would make the similarity math meaningful.

**3. Add a diversity rule to the ranking step.**
After scoring, before returning the top K songs, apply a simple rule: no more than two songs by the same artist or in the same genre in a single recommendation set. This breaks the filter bubble and surfaces songs the user might not have thought to ask for — which is actually what makes Spotify's "Discover Weekly" feel useful rather than repetitive.

---

## 9. Reflection

The biggest thing I learned from building this is how much of a recommendation system's "personality" comes from the weights, not the algorithm itself. The scoring math is simple addition and subtraction. But by choosing to make genre worth 2.0 points and energy worth 1.0, I made a design decision that locked every user into genre-first results — whether or not that is what they actually wanted. Changing a single number flipped the behavior of the whole system. That was surprising to see so concretely.

AI tools helped a lot during development for things like sketching out the scoring formula, drafting documentation, and debugging edge cases quickly. But the moments that required the most manual attention were the ones where the system did something technically correct but intuitively wrong — like ranking a metal song above the only melancholic song when a user asked for "melancholic metal." The code was doing exactly what it was told; the problem was that the instructions were incomplete. No tool can catch that without someone thinking through the user's intent.

What surprised me most was how useful even a basic point-scoring system can be. Before this project, I assumed recommenders had to be complicated — neural networks, massive datasets, collaborative signals from millions of users. But even with 19 songs and five hand-tuned weights, the system produced results that felt intuitive for most standard profiles. Simple rules, applied consistently, go further than expected.

If I continued this project, the first thing I would build is a feedback loop: after a recommendation is made, ask the user whether they liked it, and use that to adjust the weights over time. Right now the weights are fixed by whoever wrote the code. A real system learns them from behavior. That gap — between a static scoring function and one that adapts — is essentially the gap between this simulation and what Spotify actually does.
