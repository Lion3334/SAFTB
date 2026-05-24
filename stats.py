from collections import defaultdict


def _player_team(game: dict) -> tuple[list[str], list[str]]:
    """Returns (team1_ids, team2_ids) for a game."""
    t1 = [game["team1_player1_id"], game["team1_player2_id"]]
    t2 = [game["team2_player1_id"], game["team2_player2_id"]]
    return t1, t2


def compute_leaderboard(players: list[dict], games: list[dict]) -> list[dict]:
    """
    Returns one row per player with lifetime and last-7 stats.
    games must be sorted game_date DESC, game_sequence DESC (as returned by fetch_games).
    """
    pid_to_name = {p["id"]: p["name"] for p in players}

    # Per-player list of game results in recency order (already sorted by caller)
    player_games: dict[str, list[dict]] = defaultdict(list)

    for game in games:
        t1, t2 = _player_team(game)
        s1, s2 = game["team1_score"], game["team2_score"]

        for pid in t1:
            player_games[pid].append({
                "scored": s1, "against": s2,
                "win": 1 if s1 > s2 else 0,
                "loss": 1 if s1 < s2 else 0,
            })
        for pid in t2:
            player_games[pid].append({
                "scored": s2, "against": s1,
                "win": 1 if s2 > s1 else 0,
                "loss": 1 if s2 < s1 else 0,
            })

    rows = []
    for p in players:
        pid = p["id"]
        pg = player_games.get(pid, [])

        def _agg(records):
            wins = sum(r["win"] for r in records)
            losses = sum(r["loss"] for r in records)
            scored = sum(r["scored"] for r in records)
            against = sum(r["against"] for r in records)
            return wins, losses, scored, against

        lw, ll, ls, la = _agg(pg)
        r7 = pg[:7]
        rw, rl, rs, ra = _agg(r7)

        rows.append({
            "id": pid,
            "Player": pid_to_name[pid],
            "Wins": lw,
            "Losses": ll,
            "Points Scored": ls,
            "Points Against": la,
            "Point Diff": ls - la,
            "Last 7 W-L": f"{rw}-{rl}",
            "Last 7 Diff": rs - ra,
        })

    rows.sort(key=lambda r: r["Wins"], reverse=True)
    return rows


def compute_nemesis(players: list[dict], games: list[dict]) -> list[dict]:
    """
    Returns one row per player with head-to-head nemesis stats.
    For each ordered pair (player_a, opponent_b):
      wins_against, losses_against, point_diff_against, games_against
    """
    pid_to_name = {p["id"]: p["name"] for p in players}

    # h2h[a][b] = {wins, losses, diff, games}
    h2h: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {
        "wins": 0, "losses": 0, "diff": 0, "games": 0
    }))

    for game in games:
        t1, t2 = _player_team(game)
        s1, s2 = game["team1_score"], game["team2_score"]

        for a in t1:
            for b in t2:
                rec = h2h[a][b]
                rec["games"] += 1
                rec["diff"] += s1 - s2
                if s1 > s2:
                    rec["wins"] += 1
                elif s1 < s2:
                    rec["losses"] += 1
                # Reverse direction
                rec2 = h2h[b][a]
                rec2["games"] += 1
                rec2["diff"] += s2 - s1
                if s2 > s1:
                    rec2["wins"] += 1
                elif s2 < s1:
                    rec2["losses"] += 1

    def _best(pid: str, key: str, reverse: bool) -> str:
        opponents = h2h.get(pid, {})
        if not opponents:
            return "—"
        # Filter to opponents who have at least 1 game
        candidates = [(opp, data) for opp, data in opponents.items() if data["games"] > 0]
        if not candidates:
            return "—"
        # Sort by stat (desc if reverse=True), then by games desc as tiebreaker
        candidates.sort(key=lambda x: (x[1][key] * (-1 if reverse else 1), -x[1]["games"]))
        opp_id, data = candidates[0]
        val = data[key]
        label = f"{pid_to_name.get(opp_id, '?')} ({'+' if key=='diff' and val>0 else ''}{val})"
        return label

    rows = []
    for p in players:
        pid = p["id"]
        rows.append({
            "Player": pid_to_name[pid],
            "Most Wins Against": _best(pid, "wins", reverse=True),
            "Most Losses Against": _best(pid, "losses", reverse=True),
            "Best Diff Against": _best(pid, "diff", reverse=True),
            "Worst Diff Against": _best(pid, "diff", reverse=False),
        })

    return rows
