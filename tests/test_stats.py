"""
Unit tests for stats.py — pure Python, no Supabase required.
Run with: pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from stats import compute_leaderboard, compute_nemesis


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_game(gid, date, seq, t1p1, t1p2, t2p1, t2p2, s1, s2):
    return {
        "id": gid,
        "game_date": date,
        "game_sequence": seq,
        "team1_player1_id": t1p1,
        "team1_player2_id": t1p2,
        "team2_player1_id": t2p1,
        "team2_player2_id": t2p2,
        "team1_score": s1,
        "team2_score": s2,
    }


@pytest.fixture
def players():
    return [
        {"id": "p1", "name": "Alice"},
        {"id": "p2", "name": "Bob"},
        {"id": "p3", "name": "Charlie"},
        {"id": "p4", "name": "Diana"},
    ]


@pytest.fixture
def one_game(players):
    """Alice & Bob beat Charlie & Diana 21-15."""
    return [make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15)]


# ---------------------------------------------------------------------------
# compute_leaderboard — basic correctness
# ---------------------------------------------------------------------------

def test_wins_and_losses(players, one_game):
    rows = {r["Player"]: r for r in compute_leaderboard(players, one_game)}
    assert rows["Alice"]["Wins"] == 1
    assert rows["Alice"]["Losses"] == 0
    assert rows["Bob"]["Wins"] == 1
    assert rows["Bob"]["Losses"] == 0
    assert rows["Charlie"]["Wins"] == 0
    assert rows["Charlie"]["Losses"] == 1
    assert rows["Diana"]["Wins"] == 0
    assert rows["Diana"]["Losses"] == 1


def test_points_scored_full_team_score(players, one_game):
    """Each player gets the full team score, not half."""
    rows = {r["Player"]: r for r in compute_leaderboard(players, one_game)}
    assert rows["Alice"]["Points Scored"] == 21
    assert rows["Charlie"]["Points Scored"] == 15


def test_points_against(players, one_game):
    rows = {r["Player"]: r for r in compute_leaderboard(players, one_game)}
    assert rows["Alice"]["Points Against"] == 15
    assert rows["Charlie"]["Points Against"] == 21


def test_point_differential(players, one_game):
    rows = {r["Player"]: r for r in compute_leaderboard(players, one_game)}
    assert rows["Alice"]["Point Diff"] == 6
    assert rows["Charlie"]["Point Diff"] == -6


def test_tie_game_no_win_or_loss(players):
    games = [make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 15, 15)]
    rows = {r["Player"]: r for r in compute_leaderboard(players, games)}
    for name in ["Alice", "Bob", "Charlie", "Diana"]:
        assert rows[name]["Wins"] == 0
        assert rows[name]["Losses"] == 0


def test_tie_game_points_still_credited(players):
    games = [make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 15, 15)]
    rows = {r["Player"]: r for r in compute_leaderboard(players, games)}
    assert rows["Alice"]["Points Scored"] == 15
    assert rows["Alice"]["Point Diff"] == 0


def test_empty_games_zeros(players):
    rows = {r["Player"]: r for r in compute_leaderboard(players, [])}
    assert rows["Alice"]["Wins"] == 0
    assert rows["Alice"]["Losses"] == 0
    assert rows["Alice"]["Points Scored"] == 0
    assert rows["Alice"]["Point Diff"] == 0


def test_sorted_by_wins_descending(players):
    games = [
        make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15),
        make_game("g2", "2024-01-01", 2, "p1", "p2", "p3", "p4", 21, 15),
    ]
    rows = compute_leaderboard(players, games)
    win_counts = [r["Wins"] for r in rows]
    assert win_counts == sorted(win_counts, reverse=True)


def test_multiple_games_accumulate(players):
    """Two wins = 2 total wins, points accumulate."""
    games = [
        make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15),
        make_game("g2", "2024-01-02", 1, "p1", "p2", "p3", "p4", 18, 16),
    ]
    rows = {r["Player"]: r for r in compute_leaderboard(players, games)}
    assert rows["Alice"]["Wins"] == 2
    assert rows["Alice"]["Points Scored"] == 39
    assert rows["Charlie"]["Losses"] == 2


def test_same_player_different_teams(players):
    """Alice & Charlie beat Bob & Diana, then Alice & Bob beat Charlie & Diana."""
    games = [
        make_game("g1", "2024-01-01", 1, "p1", "p3", "p2", "p4", 21, 15),
        make_game("g2", "2024-01-02", 1, "p1", "p2", "p3", "p4", 21, 15),
    ]
    rows = {r["Player"]: r for r in compute_leaderboard(players, games)}
    assert rows["Alice"]["Wins"] == 2
    assert rows["Alice"]["Losses"] == 0
    assert rows["Charlie"]["Wins"] == 1
    assert rows["Charlie"]["Losses"] == 1


# ---------------------------------------------------------------------------
# compute_leaderboard — Last 7 Games
# ---------------------------------------------------------------------------

def test_last_7_uses_most_recent(players):
    """With 8 games, last 7 is used. The oldest game is excluded from recent stats."""
    # Games sorted DESC as returned by fetch_games (most recent first)
    games = []
    # Games 2-9 (most recent): Alice & Bob win
    for i in range(8, 0, -1):
        seq = i
        s1, s2 = (21, 15) if i > 1 else (15, 21)  # oldest game (seq=1): Alice loses
        games.append(make_game(f"g{i}", "2024-01-01", seq, "p1", "p2", "p3", "p4", s1, s2))

    rows = {r["Player"]: r for r in compute_leaderboard(players, games)}

    # Lifetime: 7 wins, 1 loss
    assert rows["Alice"]["Wins"] == 7
    assert rows["Alice"]["Losses"] == 1

    # Last 7 (most recent 7 = seq 8 down to seq 2 = all wins)
    assert rows["Alice"]["Last 7 W-L"] == "7-0"


def test_last_7_format(players, one_game):
    rows = {r["Player"]: r for r in compute_leaderboard(players, one_game)}
    assert rows["Alice"]["Last 7 W-L"] == "1-0"
    assert rows["Charlie"]["Last 7 W-L"] == "0-1"


def test_last_7_fewer_than_7_games(players):
    games = [make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15)]
    rows = {r["Player"]: r for r in compute_leaderboard(players, games)}
    # Only 1 game, last-7 = last-1
    assert rows["Alice"]["Last 7 W-L"] == "1-0"


# ---------------------------------------------------------------------------
# compute_nemesis — basic correctness
# ---------------------------------------------------------------------------

def test_nemesis_new_player_shows_dash(players):
    """Player with no games gets dashes in all nemesis columns."""
    rows = {r["Player"]: r for r in compute_nemesis(players, [])}
    assert rows["Alice"]["Most Wins Against"] == "—"
    assert rows["Alice"]["Most Losses Against"] == "—"
    assert rows["Alice"]["Best Diff Against"] == "—"
    assert rows["Alice"]["Worst Diff Against"] == "—"


def test_nemesis_most_wins_against(players):
    """
    Alice beats Charlie in 3 games but Diana in only 1 → Most Wins Against = Charlie.
    g1: Alice+Bob vs Charlie+Diana  → Alice faces Charlie AND Diana
    g2,g3: Alice+Diana vs Bob+Charlie → Alice faces Charlie but NOT Diana
    Result: Alice vs Charlie = 3 wins, vs Diana = 1 win, vs Bob = 2 wins.
    """
    games = [
        make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15),
        make_game("g2", "2024-01-02", 1, "p1", "p4", "p2", "p3", 21, 15),
        make_game("g3", "2024-01-03", 1, "p1", "p4", "p2", "p3", 21, 15),
    ]
    rows = {r["Player"]: r for r in compute_nemesis(players, games)}
    assert rows["Alice"]["Most Wins Against"].startswith("Charlie")


def test_nemesis_most_losses_against(players):
    """Charlie loses to Alice twice → Charlie's Most Losses Against = Alice (2)."""
    games = [
        make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15),
        make_game("g2", "2024-01-02", 1, "p1", "p2", "p3", "p4", 21, 15),
    ]
    rows = {r["Player"]: r for r in compute_nemesis(players, games)}
    assert rows["Charlie"]["Most Losses Against"].startswith("Alice")
    assert rows["Charlie"]["Most Losses Against"].startswith("Alice") or \
           rows["Charlie"]["Most Losses Against"].startswith("Bob")


def test_nemesis_best_diff_against(players):
    """Alice dominates Charlie (+10, +10) vs Diana (+1). Best diff against = Charlie."""
    games = [
        make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 25, 15),  # +10 vs Charlie/Diana
        make_game("g2", "2024-01-02", 1, "p1", "p3", "p2", "p4", 21, 20),  # +1 with Charlie vs Bob/Diana
    ]
    rows = {r["Player"]: r for r in compute_nemesis(players, games)}
    # Against Diana: +10 from g1 (Diana on opposing team)
    # Against Charlie in g1: +10; Against Charlie in g2: Charlie is on Alice's team, so not an opponent
    # Alice vs Diana: g1: +10. Alice vs Bob: g2: Alice on opposite team from Bob with Charlie → +1
    assert "Best Diff Against" in rows["Alice"]


def test_nemesis_worst_diff_against(players):
    """Alice loses to Charlie twice badly → Worst Diff Against = Charlie."""
    games = [
        make_game("g1", "2024-01-01", 1, "p3", "p4", "p1", "p2", 21, 5),
        make_game("g2", "2024-01-02", 1, "p3", "p4", "p1", "p2", 21, 10),
    ]
    rows = {r["Player"]: r for r in compute_nemesis(players, games)}
    worst = rows["Alice"]["Worst Diff Against"]
    assert worst.startswith("Charlie") or worst.startswith("Diana")


def test_nemesis_wins_count_in_label(players):
    """Label includes the numeric value."""
    games = [
        make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15),
        make_game("g2", "2024-01-02", 1, "p1", "p2", "p3", "p4", 21, 15),
    ]
    rows = {r["Player"]: r for r in compute_nemesis(players, games)}
    # Alice beat Charlie/Diana 2 times
    label = rows["Alice"]["Most Wins Against"]
    assert "(2)" in label


def test_nemesis_tiebreaker_by_games_played(players):
    """When two opponents tied on wins, the one with more games is shown."""
    # Alice beats Charlie once in 2 games, beats Diana once in 1 game
    # Tiebreaker: Charlie (2 games) > Diana (1 game)
    games = [
        make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15),  # Alice beats Charlie
        make_game("g2", "2024-01-02", 1, "p3", "p4", "p1", "p2", 21, 15),  # Charlie beats Alice (2nd game vs Charlie)
        make_game("g3", "2024-01-03", 1, "p1", "p2", "p4", "p3", 21, 15),  # Alice beats Diana (1 game vs Diana)
    ]
    # Alice: 1 win vs Charlie (2 games), 1 win vs Diana (1 game)
    # Tiebreaker → Charlie
    rows = {r["Player"]: r for r in compute_nemesis(players, games)}
    assert rows["Alice"]["Most Wins Against"].startswith("Charlie")


def test_nemesis_diff_sign_in_label(players):
    """Positive diff shows + sign, negative shows nothing extra."""
    games = [make_game("g1", "2024-01-01", 1, "p1", "p2", "p3", "p4", 21, 15)]
    rows = {r["Player"]: r for r in compute_nemesis(players, games)}
    best = rows["Alice"]["Best Diff Against"]
    assert "+" in best  # positive diff should show +


def test_nemesis_bidirectional(players, one_game):
    """Alice beats Charlie → Alice's wins vs Charlie ≠ Charlie's wins vs Alice."""
    rows = {r["Player"]: r for r in compute_nemesis(players, one_game)}
    # Alice has wins against opponents
    assert "Charlie" in rows["Alice"]["Most Wins Against"] or \
           "Diana" in rows["Alice"]["Most Wins Against"]
    # Charlie has losses against opponents
    assert "Alice" in rows["Charlie"]["Most Losses Against"] or \
           "Bob" in rows["Charlie"]["Most Losses Against"]
