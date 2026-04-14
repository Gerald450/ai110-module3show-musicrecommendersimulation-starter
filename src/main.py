"""
Command line runner for the Music Recommender Simulation.

Run with:
    python -m src.main
"""

from recommender import load_songs, recommend_songs, SCORING_MODES

# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

HIGH_ENERGY_POP = {
    "name": "High-Energy Pop",
    "preferred_genres":    ["pop"],
    "preferred_moods":     ["happy", "intense"],
    "preferred_mood_tags": ["energetic", "uplifting", "motivating"],
    "preferred_decade":    "2020s",
    "target_energy":       0.90,
    "target_tempo":        130,
    "target_valence":      0.75,
}

CHILL_LOFI = {
    "name": "Chill Lofi / Low Energy",
    "preferred_genres":    ["lofi", "ambient"],
    "preferred_moods":     ["chill", "focused"],
    "preferred_mood_tags": ["dreamy", "calm", "focused"],
    "preferred_decade":    "2020s",
    "target_energy":       0.35,
    "target_tempo":        75,
    "target_valence":      0.58,
}

DEEP_ROCK = {
    "name": "Deep Intense Rock",
    "preferred_genres":    ["rock", "metal"],
    "preferred_moods":     ["intense"],
    "preferred_mood_tags": ["aggressive", "powerful", "driving"],
    "preferred_decade":    "2010s",
    "target_energy":       0.92,
    "target_tempo":        155,
    "target_valence":      0.35,
}

CONFLICTING = {
    "name": "Edge Case — Conflicting (high energy + sad mood)",
    "preferred_genres":    ["rock", "metal"],
    "preferred_moods":     ["melancholic"],
    "preferred_mood_tags": ["sad", "dark", "longing"],
    "preferred_decade":    "2010s",
    "target_energy":       0.90,
    "target_tempo":        140,
    "target_valence":      0.25,
}

NARROW_CLASSICAL = {
    "name": "Edge Case — Narrow (classical only)",
    "preferred_genres":    ["classical"],
    "preferred_moods":     ["peaceful"],
    "preferred_mood_tags": ["calm", "serene", "contemplative"],
    "preferred_decade":    "2000s",
    "target_energy":       0.20,
    "target_tempo":        58,
    "target_valence":      0.70,
}

NEUTRAL_AVERAGE = {
    "name": "Edge Case — Neutral / Average Everything",
    "preferred_genres":    ["pop"],
    "preferred_moods":     ["happy"],
    "preferred_mood_tags": ["uplifting", "warm"],
    "preferred_decade":    "2020s",
    "target_energy":       0.50,
    "target_tempo":        100,
    "target_valence":      0.50,
}

ALL_PROFILES = [HIGH_ENERGY_POP, CHILL_LOFI, DEEP_ROCK,
                CONFLICTING, NARROW_CLASSICAL, NEUTRAL_AVERAGE]


# ---------------------------------------------------------------------------
# ASCII table helpers
# ---------------------------------------------------------------------------

_COL_WIDTHS = [2, 24, 18, 6, 44]
_HEADERS    = ["#", "Title", "Artist", "Score", "Reasons"]


def _trunc(text: str, max_len: int) -> str:
    """Truncate text to max_len characters, appending … if cut."""
    s = str(text)
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def _table_row(cells: list, widths: list) -> str:
    """Format one table row with fixed column widths."""
    return " │ ".join(f"{_trunc(str(c), w):<{w}}" for c, w in zip(cells, widths))


def _table_separator(widths: list) -> str:
    parts = ["─" * w for w in widths]
    return "─┼─".join(parts)


def _print_table(results: list, profile_name: str, mode_label: str = "") -> None:
    """Print recommendations as a clean ASCII table."""
    label = f"  {profile_name}"
    if mode_label:
        label += f"  [{mode_label}]"
    print()
    print(f"{'─' * 52}")
    print(label)
    print(f"{'─' * 52}")

    sep = _table_separator(_COL_WIDTHS)
    print("  " + _table_row(_HEADERS, _COL_WIDTHS))
    print("  " + sep)

    for rank, (song, score, reasons) in enumerate(results, start=1):
        # Show up to 3 reasons, compressed to fit the column
        top_reasons = " · ".join(reasons[:3])
        row = [
            rank,
            song["title"],
            song["artist"],
            f"{score:.2f}",
            top_reasons,
        ]
        print("  " + _table_row(row, _COL_WIDTHS))

    print("  " + sep)


# ---------------------------------------------------------------------------
# Profile runner
# ---------------------------------------------------------------------------

def _run_profile(
    songs: list,
    profile: dict,
    k: int = 5,
    mode: str = None,
    artist_penalty: float = 0.0,
    genre_penalty: float = 0.0,
) -> None:
    """Run recommend_songs for one profile and display the result as a table."""
    prefs = {key: val for key, val in profile.items() if key != "name"}
    results = recommend_songs(
        prefs, songs, k=k,
        mode=mode,
        artist_penalty=artist_penalty,
        genre_penalty=genre_penalty,
    )
    mode_label = mode or "default"
    if artist_penalty > 0 or genre_penalty > 0:
        mode_label += f"  diversity(artist={artist_penalty}, genre={genre_penalty})"
    _print_table(results, profile["name"], mode_label)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs("data/songs.csv")

    # -----------------------------------------------------------------------
    # Section 1 — Standard profiles with default scoring mode
    # -----------------------------------------------------------------------
    print("\n" + "═" * 52)
    print("  SECTION 1 — Standard Profiles (default mode)")
    print("═" * 52)

    for profile in [HIGH_ENERGY_POP, CHILL_LOFI, DEEP_ROCK]:
        _run_profile(songs, profile, k=5)

    # -----------------------------------------------------------------------
    # Section 2 — Edge-case profiles
    # -----------------------------------------------------------------------
    print("\n" + "═" * 52)
    print("  SECTION 2 — Edge-Case Profiles (default mode)")
    print("═" * 52)

    for profile in [CONFLICTING, NARROW_CLASSICAL, NEUTRAL_AVERAGE]:
        _run_profile(songs, profile, k=5)

    # -----------------------------------------------------------------------
    # Section 3 — Scoring Mode Comparison (HIGH_ENERGY_POP)
    # -----------------------------------------------------------------------
    print("\n" + "═" * 52)
    print("  SECTION 3 — Scoring Mode Comparison")
    print("  Profile: High-Energy Pop")
    print("═" * 52)

    for mode_name in SCORING_MODES:
        _run_profile(songs, HIGH_ENERGY_POP, k=5, mode=mode_name)

    # -----------------------------------------------------------------------
    # Section 4 — Diversity Penalty Demo (CHILL_LOFI)
    #
    # Without penalty: the three LoRoom songs (LoRoom artist) dominate.
    # With penalty:    the second LoRoom song gets its score cut by 0.5,
    #                  which can surface a non-lofi song in the top-5.
    # -----------------------------------------------------------------------
    print("\n" + "═" * 52)
    print("  SECTION 4 — Diversity Penalty  (Chill Lofi)")
    print("═" * 52)

    print("\n  Without diversity penalty:")
    _run_profile(songs, CHILL_LOFI, k=5, artist_penalty=0.0, genre_penalty=0.0)

    print("\n  With diversity penalty (artist=0.5, genre=0.3):")
    _run_profile(songs, CHILL_LOFI, k=5, artist_penalty=0.5, genre_penalty=0.3)

    print()


if __name__ == "__main__":
    main()
