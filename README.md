# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

This recommender uses a **content-based filtering** approach. Rather than relying on what other users listened to (collaborative filtering), it scores each song by directly comparing its audio features and metadata against a stored user preference profile. Every song in the catalog receives a numerical score; songs are then sorted in descending order and the top K results are returned as recommendations.

### Algorithm Recipe

Each song is scored by summing weighted contributions from categorical matches and Gaussian-based numerical similarity:

```
score = genre_score + mood_score + energy_score + tempo_score
      + valence_score + danceability_score + acousticness_score
```

**Categorical features (exact match):**

| Rule | Points |
|---|---|
| Genre matches user's preferred genre | +3.0 |
| Mood matches user's preferred mood | +2.0 |

**Numerical features (Gaussian similarity):**

Each numerical score uses `weight × exp(−(song_val − target)² / (2σ²))`, which gives 1.0 for a perfect match and falls off smoothly as the values diverge.

| Feature | Weight | Sigma (σ) | Notes |
|---|---|---|---|
| Energy | 2.0 | 0.15 | Most discriminative continuous feature |
| Tempo | 1.0 | 0.10 (normalized) | Tempo divided by 200 before scoring |
| Valence | 1.0 | 0.20 | Musical positivity/mood |
| Danceability | 0.5 | 0.20 | Fine-tuning signal |
| Acousticness | 0.5 | 0.20 | Tiebreaker between sub-genres |

**Maximum possible score: 10.0**

### Flow

```
User Preferences  →  Score every song in songs.csv  →  Sort by score  →  Return top K
```

For each song: compute genre + mood matches, apply Gaussian similarity for each numerical feature, sum all contributions into one final score, and append `(song, score)` to the ranked list.

### Limitations and Potential Biases

- **Genre dominance:** At 3.0 points, genre can overshadow good numerical matches. A song that is nearly perfect on all numerical features but in the wrong genre will always lose to a weak genre match.
- **Mood vocabulary mismatch:** If a user's preferred mood string does not exactly match a song's mood label (e.g. `"energetic"` vs `"intense"`), the 2.0 points are silently lost even though the songs are semantically similar.
- **Small catalog:** With ~19 songs, the top-K results are sensitive to how the catalog was curated — certain genres or moods may be over- or under-represented.
- **No listening history:** The system has no feedback loop. It cannot learn that a user skipped every high-energy recommendation and adjust over time.

---

## Features Used in the Simulation

### Song Object

Each song in the catalog is represented with the following attributes:

- `title` — the name of the song
- `artist` — the performing artist or band
- `genre` — musical genre (e.g., pop, rock, jazz, hip-hop)
- `energy` — perceived intensity and activity level, float in [0.0, 1.0]
- `tempo` — beats per minute (BPM), e.g., 90–180
- `valence` — musical positivity or mood, float in [0.0, 1.0] (low = sad, high = happy)
- `duration` — song length in seconds

### UserProfile Object

Each user profile stores the following preference attributes:

- `preferred_genres` — list of genres the user enjoys (e.g., `["pop", "indie"]`)
- `preferred_artists` — list of favorite artists
- `target_energy` — the user's ideal energy level, float in [0.0, 1.0]
- `target_tempo` — the user's preferred BPM range or target value
- `target_valence` — the user's preferred mood level, float in [0.0, 1.0]
- `feature_weights` — a dictionary mapping each feature to a relative importance weight (e.g., `{"genre": 0.35, "energy": 0.25, ...}`)

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

