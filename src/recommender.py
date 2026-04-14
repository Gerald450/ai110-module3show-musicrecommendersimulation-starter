import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Song:
    """Represents a single song and all of its audio/metadata attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Extended fields — default values preserve backwards compatibility with tests
    popularity: int = 0
    release_decade: str = ""
    mood_tags: str = ""


@dataclass
class UserProfile:
    """Stores a user's taste preferences used to score and rank songs."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS: Dict[str, float] = {
    "genre":        2.0,   # categorical exact-match bonus
    "mood":         1.0,   # categorical exact-match bonus
    "mood_tags":    1.0,   # partial tag-overlap bonus (max = this value)
    "energy":       1.0,   # max numerical similarity contribution
    "tempo":        1.0,   # max numerical similarity (normalised over 200 BPM)
    "valence":      1.0,   # max numerical similarity contribution
    "popularity":   0.3,   # small bonus; 0.3 = fully popular song
    "decade":       0.5,   # bonus if song's decade matches user preference
    "acousticness": 0.5,   # applied only when target_acousticness is set
}

# ---------------------------------------------------------------------------
# Scoring Modes — Strategy Pattern via weight configurations
#
# Each mode is a complete weight dictionary that is merged over DEFAULT_WEIGHTS
# inside score_song.  Adding a new mode requires only a new dict entry here;
# no scoring logic needs to change.  The caller selects a mode by name and
# passes it to recommend_songs(mode=...).
# ---------------------------------------------------------------------------

SCORING_MODES: Dict[str, Dict[str, float]] = {
    "genre_first": {
        # Heavy genre anchor; numerical and tag features are fine-tuning only.
        "genre":        3.0,
        "mood":         0.8,
        "mood_tags":    0.6,
        "energy":       0.6,
        "tempo":        0.4,
        "valence":      0.4,
        "popularity":   0.2,
        "decade":       0.3,
        "acousticness": 0.3,
    },
    "mood_first": {
        # Prioritises how a song feels over what genre it is.
        # mood_tags enables partial emotional matching beyond the single mood label.
        "genre":        1.0,
        "mood":         1.5,
        "mood_tags":    2.0,
        "energy":       0.8,
        "tempo":        0.5,
        "valence":      1.0,
        "popularity":   0.2,
        "decade":       0.3,
        "acousticness": 0.3,
    },
    "energy_focused": {
        # Treats energy and tempo as the dominant signals.
        # Useful for workout / activity playlists where intensity matters most.
        "genre":        1.0,
        "mood":         0.5,
        "mood_tags":    0.5,
        "energy":       2.5,
        "tempo":        1.5,
        "valence":      0.5,
        "popularity":   0.2,
        "decade":       0.2,
        "acousticness": 0.3,
    },
}


# ---------------------------------------------------------------------------
# OOP interface (used by existing tests)
# ---------------------------------------------------------------------------

class Recommender:
    """OOP wrapper that scores and ranks a song catalog against a UserProfile."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k songs ranked by how well they match the given UserProfile."""
        user_prefs = {
            "preferred_genres":    [user.favorite_genre],
            "preferred_moods":     [user.favorite_mood],
            "target_energy":       user.target_energy,
            "target_acousticness": 0.8 if user.likes_acoustic else 0.1,
        }
        song_dicts = [s.__dict__ for s in self.songs]
        results = recommend_songs(user_prefs, song_dicts, k)
        id_to_song = {s.id: s for s in self.songs}
        return [id_to_song[r[0]["id"]] for r in results if r[0]["id"] in id_to_song]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended."""
        user_prefs = {
            "preferred_genres": [user.favorite_genre],
            "preferred_moods":  [user.favorite_mood],
            "target_energy":    user.target_energy,
        }
        _, reasons = score_song(user_prefs, song.__dict__)
        return "; ".join(reasons) if reasons else "No strong match found."


# ---------------------------------------------------------------------------
# Functional API
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file and return a list of song dicts with typed fields."""
    songs = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    songs.append({
                        "id":             int(row["id"]),
                        "title":          row["title"].strip(),
                        "artist":         row["artist"].strip(),
                        "genre":          row["genre"].strip().lower(),
                        "mood":           row["mood"].strip().lower(),
                        "energy":         float(row["energy"]),
                        "tempo_bpm":      float(row["tempo_bpm"]),
                        "valence":        float(row["valence"]),
                        "danceability":   float(row["danceability"]),
                        "acousticness":   float(row["acousticness"]),
                        # Extended fields — gracefully absent from older CSVs
                        "popularity":     int(row.get("popularity") or 0),
                        "release_decade": (row.get("release_decade") or "").strip(),
                        "mood_tags":      (row.get("mood_tags") or "").strip(),
                    })
                except (ValueError, KeyError) as e:
                    print(f"  [warning] Skipping malformed row: {e}")
    except FileNotFoundError:
        print(f"[error] CSV file not found: {csv_path}")
    return songs


def score_song(
    user_prefs: Dict,
    song: Dict,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, List[str]]:
    """Score a single song against user preferences; returns (total_score, reasons).

    Pass a custom `weights` dict (or a value from SCORING_MODES) to override
    DEFAULT_WEIGHTS. Any key absent from the custom dict falls back to the default.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    score = 0.0
    reasons = []

    # --- Categorical: genre match ---
    preferred_genres = _as_list(user_prefs, "preferred_genres", "genre")
    if song["genre"] in preferred_genres:
        score += w["genre"]
        reasons.append(f"genre match: '{song['genre']}' (+{w['genre']:.1f})")

    # --- Categorical: mood match ---
    preferred_moods = _as_list(user_prefs, "preferred_moods", "mood")
    if song["mood"] in preferred_moods:
        score += w["mood"]
        reasons.append(f"mood match: '{song['mood']}' (+{w['mood']:.1f})")

    # --- Mood tags: partial overlap ---
    # Awards a fractional bonus based on how many of the user's preferred tags
    # appear in the song's tag list.  A song with 2 of 3 requested tags scores
    # 2/3 of the full mood_tags weight.
    preferred_tags = [t.strip().lower() for t in user_prefs.get("preferred_mood_tags", [])]
    song_tags_raw = song.get("mood_tags", "") or ""
    if preferred_tags and song_tags_raw:
        song_tag_set = {t.strip().lower() for t in song_tags_raw.split(",")}
        user_tag_set = set(preferred_tags)
        matched = user_tag_set & song_tag_set
        if matched:
            sim = round(w["mood_tags"] * len(matched) / len(user_tag_set), 3)
            score += sim
            reasons.append(f"mood tags {sorted(matched)} (+{sim:.2f})")

    # --- Numerical: energy similarity ---
    target_energy = user_prefs.get("target_energy", user_prefs.get("energy"))
    if target_energy is not None:
        sim = max(0.0, round(w["energy"] * (1.0 - abs(song["energy"] - target_energy)), 3))
        score += sim
        reasons.append(f"energy similarity (+{sim:.2f})")

    # --- Numerical: tempo similarity (normalised over 200 BPM) ---
    target_tempo = user_prefs.get("target_tempo", user_prefs.get("tempo"))
    if target_tempo is not None:
        sim = max(0.0, round(w["tempo"] * (1.0 - abs(song["tempo_bpm"] - target_tempo) / 200.0), 3))
        score += sim
        reasons.append(f"tempo similarity (+{sim:.2f})")

    # --- Numerical: valence similarity ---
    target_valence = user_prefs.get("target_valence", user_prefs.get("valence"))
    if target_valence is not None:
        sim = max(0.0, round(w["valence"] * (1.0 - abs(song["valence"] - target_valence)), 3))
        score += sim
        reasons.append(f"valence similarity (+{sim:.2f})")

    # --- Numerical: acousticness similarity (only when target is set) ---
    target_acousticness = user_prefs.get("target_acousticness")
    if target_acousticness is not None:
        sim = max(0.0, round(w["acousticness"] * (1.0 - abs(song["acousticness"] - target_acousticness)), 3))
        score += sim
        reasons.append(f"acousticness similarity (+{sim:.2f})")

    # --- Popularity bonus ---
    # If the user specified a target_popularity, compute similarity.
    # Otherwise award a small constant bonus proportional to the song's raw popularity.
    pop = song.get("popularity", 0) or 0
    if w["popularity"] > 0 and pop > 0:
        target_pop = user_prefs.get("target_popularity")
        if target_pop is not None:
            sim = max(0.0, round(w["popularity"] * (1.0 - abs(pop - target_pop) / 100.0), 3))
            score += sim
            reasons.append(f"popularity match (+{sim:.2f})")
        else:
            bonus = round(w["popularity"] * pop / 100.0, 3)
            score += bonus
            reasons.append(f"popularity bonus (+{bonus:.2f})")

    # --- Release decade match (binary) ---
    preferred_decade = (user_prefs.get("preferred_decade") or "").strip().lower()
    song_decade = (song.get("release_decade") or "").strip().lower()
    if preferred_decade and song_decade and preferred_decade == song_decade:
        score += w["decade"]
        reasons.append(f"decade match: {song['release_decade']} (+{w['decade']:.1f})")

    return round(score, 4), reasons


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    weights: Optional[Dict[str, float]] = None,
    mode: Optional[str] = None,
    artist_penalty: float = 0.0,
    genre_penalty: float = 0.0,
) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song, apply optional diversity re-ranking, return top k results.

    Parameters
    ----------
    mode : str, optional
        One of the keys in SCORING_MODES ('genre_first', 'mood_first',
        'energy_focused').  Merged over DEFAULT_WEIGHTS before any explicit
        `weights` override is applied.
    artist_penalty : float
        Score deduction for each additional song by an already-selected artist.
        Set > 0 to prevent the same artist appearing multiple times in the top-K.
    genre_penalty : float
        Score deduction for each additional song of an already-selected genre.
        Set > 0 to introduce cross-genre diversity.

    Note on sort choice
    -------------------
    sorted() is used (not list.sort()) because it returns a new list without
    modifying the original catalog — safe when the same songs list is reused
    across multiple calls.

    Returns a list of (song_dict, effective_score, reasons) tuples.
    """
    # Resolve mode into a concrete weight dict
    if mode is not None:
        if mode not in SCORING_MODES:
            raise ValueError(f"Unknown mode: {mode!r}. Available: {list(SCORING_MODES)}")
        effective_weights = {**SCORING_MODES[mode], **(weights or {})}
    else:
        effective_weights = weights  # may be None; score_song handles that

    # Score every song
    scored = sorted(
        [(song, *score_song(user_prefs, song, effective_weights)) for song in songs],
        key=lambda item: item[1],
        reverse=True,
    )

    # Apply diversity re-ranking only when at least one penalty is active
    if artist_penalty > 0 or genre_penalty > 0:
        return _apply_diversity(scored, k, artist_penalty, genre_penalty)

    return scored[:k]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_diversity(
    scored: List[Tuple[Dict, float, List[str]]],
    k: int,
    artist_penalty: float,
    genre_penalty: float,
) -> List[Tuple[Dict, float, List[str]]]:
    """Greedy MMR-style selection that penalises repeated artists and genres.

    At each step the song with the highest *effective* score is selected, where:
        effective_score = raw_score
                        - (times artist already selected) × artist_penalty
                        - (times genre already selected)  × genre_penalty

    This prevents a single dominant artist or genre from filling all K slots
    while still honouring the overall relevance ordering.
    """
    taken = [False] * len(scored)
    seen_artists: Dict[str, int] = {}
    seen_genres: Dict[str, int] = {}
    selected = []

    for _ in range(min(k, len(scored))):
        best_idx = -1
        best_eff = float("-inf")

        for idx, (song, raw_score, _) in enumerate(scored):
            if taken[idx]:
                continue
            penalty = (
                seen_artists.get(song["artist"], 0) * artist_penalty
                + seen_genres.get(song["genre"], 0) * genre_penalty
            )
            eff = raw_score - penalty
            if eff > best_eff:
                best_eff = eff
                best_idx = idx

        if best_idx == -1:
            break

        taken[best_idx] = True
        song, raw_score, reasons = scored[best_idx]
        seen_artists[song["artist"]] = seen_artists.get(song["artist"], 0) + 1
        seen_genres[song["genre"]] = seen_genres.get(song["genre"], 0) + 1
        selected.append((song, round(best_eff, 4), reasons))

    return selected


def _as_list(prefs: Dict, list_key: str, scalar_key: str) -> List[str]:
    """Return a normalised lowercase list from either a list field or a scalar field."""
    value = prefs.get(list_key) or prefs.get(scalar_key)
    if value is None:
        return []
    if isinstance(value, list):
        return [v.strip().lower() for v in value]
    return [str(value).strip().lower()]
