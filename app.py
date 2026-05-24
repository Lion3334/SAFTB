import streamlit as st
import pandas as pd
from datetime import date

import db
import stats

st.set_page_config(
    page_title="SAFTB Lifetime Leaderboard",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
/* ---------- typography & base ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* ---------- hide Streamlit chrome ---------- */
#MainMenu, footer, header { visibility: hidden; }

/* ---------- hero cards ---------- */
.hero-grid {
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
    flex-wrap: wrap;
}
.hero-card {
    background: linear-gradient(145deg, #1c2333 0%, #161b22 100%);
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 18px 24px;
    flex: 1;
    min-width: 110px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.35);
}
.hero-card .hc-val {
    font-size: 2.2rem;
    font-weight: 800;
    color: #F97316;
    line-height: 1;
    margin-bottom: 5px;
    letter-spacing: -0.02em;
}
.hero-card .hc-lbl {
    font-size: 0.72rem;
    color: #7d8590;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    font-weight: 600;
}

/* ---------- section headers ---------- */
.sectionhead {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 4px 0 18px 0;
}
.sectionhead span {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e6edf3;
    white-space: nowrap;
}
.sectionhead hr {
    flex: 1;
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #F97316 0%, #30363d 100%);
    margin: 0;
}

/* ---------- rank badge ---------- */
.rank-badge {
    display: inline-block;
    font-size: 1rem;
    width: 28px;
    text-align: center;
}

/* ---------- tab bar ---------- */
.stTabs [data-baseweb="tab-list"] {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 4px 6px;
    gap: 4px;
    margin-bottom: 24px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 28px;
    font-weight: 600;
    font-size: 0.92rem;
    color: #8b949e;
    border: none !important;
    background: transparent !important;
    transition: all 0.15s ease;
}
.stTabs [aria-selected="true"] {
    background-color: #F97316 !important;
    color: #fff !important;
}

/* ---------- form inputs ---------- */
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] {
    border-radius: 8px !important;
    border-color: #30363d !important;
    background-color: #161b22 !important;
}

/* ---------- buttons ---------- */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.88rem;
    letter-spacing: 0.01em;
    border: 1px solid #30363d;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    border-color: #F97316;
    color: #F97316;
}

/* ---------- expanders ---------- */
.streamlit-expanderHeader {
    border-radius: 8px !important;
    font-size: 0.88rem;
    font-weight: 500;
    color: #8b949e !important;
}

/* ---------- divider ---------- */
hr { border-color: #21262d; }

/* ---------- dataframe container ---------- */
.stDataFrame {
    border: 1px solid #21262d;
    border-radius: 10px;
    overflow: hidden;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def player_options(players: list[dict]) -> dict[str, str]:
    return {p["name"]: p["id"] for p in players}


def player_name_map(players: list[dict]) -> dict[str, str]:
    return {p["id"]: p["name"] for p in players}


def validate_game(t1p1, t1p2, t2p1, t2p2) -> str | None:
    ids = [t1p1, t1p2, t2p1, t2p2]
    if len(set(ids)) < 4:
        return "A player cannot appear on both teams or twice on the same team."
    return None


def hero_cards(total_games: int, total_players: int, total_points: int) -> None:
    st.markdown(f"""
    <div class="hero-grid">
        <div class="hero-card">
            <div class="hc-val">{total_games}</div>
            <div class="hc-lbl">Games Played</div>
        </div>
        <div class="hero-card">
            <div class="hc-val">{total_players}</div>
            <div class="hc-lbl">Players</div>
        </div>
        <div class="hero-card">
            <div class="hc-val">{total_points:,}</div>
            <div class="hc-lbl">Points Scored</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(emoji: str, title: str) -> None:
    st.markdown(
        f'<div class="sectionhead"><span>{emoji}&nbsp;&nbsp;{title}</span><hr/></div>',
        unsafe_allow_html=True,
    )


RANK_ICONS = {1: "🥇", 2: "🥈", 3: "🥉"}


def style_leaderboard(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """Apply color coding to differential columns."""

    def diff_color(val):
        if not isinstance(val, (int, float)):
            return ""
        if val > 0:
            return "color: #3fb950; font-weight: 600"
        if val < 0:
            return "color: #f85149; font-weight: 600"
        return "color: #8b949e"

    def record_color(val):
        return "font-weight: 600; color: #e6edf3"

    styler = (
        df.style
        .applymap(diff_color, subset=["Point Diff", "Last 7 Diff"])
        .applymap(record_color, subset=["Wins", "Losses"])
        .set_properties(subset=["Player", "Rank"], **{"font-weight": "600"})
        .set_table_styles([
            {"selector": "thead th", "props": [
                ("background-color", "#161b22"),
                ("color", "#7d8590"),
                ("font-size", "0.75rem"),
                ("text-transform", "uppercase"),
                ("letter-spacing", "0.08em"),
                ("border-bottom", "1px solid #21262d"),
            ]},
            {"selector": "tbody tr:hover", "props": [
                ("background-color", "#1c2333"),
            ]},
            {"selector": "td", "props": [
                ("border-bottom", "1px solid #21262d"),
                ("padding", "10px 14px"),
            ]},
        ])
        .hide(axis="index")
    )
    return styler


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

def _init_state():
    for k, v in {
        "admin_authed": False,
        "confirm_delete_id": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown(
    "<h1 style='font-size:2rem;font-weight:800;letter-spacing:-0.03em;margin-bottom:4px'>"
    "🏐 SAFTB Lifetime Leaderboard</h1>"
    "<p style='color:#7d8590;font-size:0.9rem;margin-top:0;margin-bottom:24px'>"
    "Beach volleyball stats, lifetime records &amp; bragging rights.</p>",
    unsafe_allow_html=True,
)

tab_lb, tab_admin = st.tabs(["🏆  Leaderboard", "🔧  Admin Panel"])

# ===========================================================================
# LEADERBOARD TAB
# ===========================================================================

with tab_lb:
    players = db.fetch_players()
    games = db.fetch_games()

    if not players:
        st.info("No players yet. Ask the admin to add players in the Admin Panel.")
    else:
        # Hero summary cards
        total_pts = sum(g["team1_score"] + g["team2_score"] for g in games)
        hero_cards(len(games), len(players), total_pts)

        # ---- Lifetime stats ----
        section_header("📊", "Lifetime Stats")

        lb_rows = stats.compute_leaderboard(players, games)

        # Insert rank column
        ranks = []
        for i, r in enumerate(lb_rows, start=1):
            ranks.append(RANK_ICONS.get(i, str(i)))

        display_cols = ["Player", "Wins", "Losses", "Points Scored",
                        "Points Against", "Point Diff", "Last 7 W-L", "Last 7 Diff"]
        lb_df = pd.DataFrame(lb_rows)[display_cols].copy()
        lb_df.insert(0, "Rank", ranks)

        st.dataframe(
            style_leaderboard(lb_df),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Nemesis view ----
        section_header("⚔️", "Nemesis View")

        nemesis_rows = stats.compute_nemesis(players, games)
        nemesis_df = pd.DataFrame(nemesis_rows)

        styled_nemesis = (
            nemesis_df.style
            .set_properties(subset=["Player"], **{"font-weight": "600"})
            .set_table_styles([
                {"selector": "thead th", "props": [
                    ("background-color", "#161b22"),
                    ("color", "#7d8590"),
                    ("font-size", "0.75rem"),
                    ("text-transform", "uppercase"),
                    ("letter-spacing", "0.08em"),
                    ("border-bottom", "1px solid #21262d"),
                ]},
                {"selector": "td", "props": [
                    ("border-bottom", "1px solid #21262d"),
                    ("padding", "10px 14px"),
                ]},
            ])
            .hide(axis="index")
        )
        st.dataframe(styled_nemesis, use_container_width=True, hide_index=True)


# ===========================================================================
# ADMIN TAB
# ===========================================================================

with tab_admin:

    if not st.session_state["admin_authed"]:
        col_auth, _ = st.columns([1, 2])
        with col_auth:
            st.markdown(
                "<p style='color:#7d8590;font-size:0.88rem;margin-bottom:8px'>"
                "Enter the admin password to log games and manage players.</p>",
                unsafe_allow_html=True,
            )
            pw = st.text_input("Password", type="password", key="pw_input",
                               label_visibility="collapsed",
                               placeholder="Admin password")
            if st.button("Unlock Admin Panel", use_container_width=True):
                if pw == st.secrets.get("admin_password", ""):
                    st.session_state["admin_authed"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    else:
        players = db.fetch_players()
        options = player_options(players)
        names = list(options.keys())

        # -----------------------------------------------------------------------
        # Add Game
        # -----------------------------------------------------------------------
        section_header("➕", "Log a Game")

        def _clear_seq():
            st.session_state.pop("ag_seq", None)

        col_date, col_seq, _ = st.columns([2, 1, 3])
        with col_date:
            game_date = st.date_input("Date", value=date.today(), key="ag_date",
                                      on_change=_clear_seq)
        with col_seq:
            next_seq = db.get_next_game_sequence(str(game_date))
            game_seq = st.number_input("Game #", min_value=1, value=next_seq,
                                       step=1, key="ag_seq")

        if len(names) < 4:
            st.info("Add at least 4 players below before logging games.")
        else:
            col_t1, col_vs, col_t2 = st.columns([5, 1, 5])

            with col_t1:
                st.markdown(
                    "<p style='font-weight:700;font-size:0.95rem;color:#F97316;"
                    "margin-bottom:6px'>TEAM 1</p>",
                    unsafe_allow_html=True,
                )
                t1p1_name = st.selectbox("Player 1", names, key="ag_t1p1",
                                          label_visibility="collapsed")
                t1p2_name = st.selectbox("Player 2", names, index=1, key="ag_t1p2",
                                          label_visibility="collapsed")
                t1_score = st.number_input("Score", min_value=0, value=0, step=1,
                                           key="ag_t1s", label_visibility="collapsed",
                                           placeholder="Score")

            with col_vs:
                st.markdown(
                    "<div style='display:flex;align-items:center;justify-content:center;"
                    "height:100%;padding-top:40px'>"
                    "<span style='font-size:1.4rem;font-weight:800;color:#30363d'>VS</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )

            with col_t2:
                st.markdown(
                    "<p style='font-weight:700;font-size:0.95rem;color:#58a6ff;"
                    "margin-bottom:6px'>TEAM 2</p>",
                    unsafe_allow_html=True,
                )
                t2p1_name = st.selectbox("Player 1", names, index=2, key="ag_t2p1",
                                          label_visibility="collapsed")
                t2p2_name = st.selectbox("Player 2", names, index=3, key="ag_t2p2",
                                          label_visibility="collapsed")
                t2_score = st.number_input("Score", min_value=0, value=0, step=1,
                                           key="ag_t2s", label_visibility="collapsed",
                                           placeholder="Score")

            def _build_payload():
                return {
                    "game_date": str(game_date),
                    "game_sequence": int(game_seq),
                    "team1_player1_id": options[t1p1_name],
                    "team1_player2_id": options[t1p2_name],
                    "team2_player1_id": options[t2p1_name],
                    "team2_player2_id": options[t2p2_name],
                    "team1_score": int(t1_score),
                    "team2_score": int(t2_score),
                }

            btn_c1, btn_c2, _ = st.columns([2, 2, 3])

            with btn_c1:
                if st.button("💾  Save Game", use_container_width=True):
                    err = validate_game(options[t1p1_name], options[t1p2_name],
                                        options[t2p1_name], options[t2p2_name])
                    if err:
                        st.error(err)
                    else:
                        try:
                            db.add_game(_build_payload())
                            for k in ["ag_t1p1", "ag_t1p2", "ag_t2p1", "ag_t2p2",
                                      "ag_t1s", "ag_t2s", "ag_seq"]:
                                st.session_state.pop(k, None)
                            st.success("Game saved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving game: {e}")

            with btn_c2:
                if st.button("💾➕  Save & Next Game", use_container_width=True):
                    err = validate_game(options[t1p1_name], options[t1p2_name],
                                        options[t2p1_name], options[t2p2_name])
                    if err:
                        st.error(err)
                    else:
                        try:
                            db.add_game(_build_payload())
                            st.session_state["ag_t1s"] = 0
                            st.session_state["ag_t2s"] = 0
                            st.session_state.pop("ag_seq", None)
                            st.success("Saved! Prepped for next game.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving game: {e}")

        st.markdown("<br>", unsafe_allow_html=True)

        # -----------------------------------------------------------------------
        # Edit / Delete Games
        # -----------------------------------------------------------------------
        section_header("✏️", "Edit / Delete Games")

        games = db.fetch_games()
        id_to_name = player_name_map(players)

        if not games:
            st.markdown(
                "<p style='color:#7d8590;font-size:0.9rem'>No games recorded yet.</p>",
                unsafe_allow_html=True,
            )
        else:
            for g in games:
                t1p1 = id_to_name.get(g["team1_player1_id"], "?")
                t1p2 = id_to_name.get(g["team1_player2_id"], "?")
                t2p1 = id_to_name.get(g["team2_player1_id"], "?")
                t2p2 = id_to_name.get(g["team2_player2_id"], "?")

                s1, s2 = g["team1_score"], g["team2_score"]
                winner_marker = " ✓" if s1 > s2 else (" ✓" if s2 > s1 else "")
                t1_label = f"{t1p1} & {t1p2}{winner_marker if s1 > s2 else ''}"
                t2_label = f"{t2p1} & {t2p2}{winner_marker if s2 > s1 else ''}"

                label = (
                    f"{g['game_date']}  ·  G{g['game_sequence']}  "
                    f"  {t1_label}  {s1} – {s2}  {t2_label}"
                )

                with st.expander(label):
                    gid = g["id"]

                    if st.session_state["confirm_delete_id"] == gid:
                        st.warning("Delete this game permanently?")
                        dc1, dc2, _ = st.columns([1, 1, 3])
                        with dc1:
                            if st.button("Yes, delete", key=f"del_confirm_{gid}",
                                         use_container_width=True):
                                db.delete_game(gid)
                                st.session_state["confirm_delete_id"] = None
                                st.rerun()
                        with dc2:
                            if st.button("Cancel", key=f"del_cancel_{gid}",
                                         use_container_width=True):
                                st.session_state["confirm_delete_id"] = None
                                st.rerun()
                    else:
                        if st.button("🗑  Delete", key=f"del_{gid}"):
                            st.session_state["confirm_delete_id"] = gid
                            st.rerun()

                    st.markdown("<hr style='margin:10px 0'>", unsafe_allow_html=True)

                    ec1, ec2, ec3 = st.columns([2, 1, 3])
                    with ec1:
                        e_date = st.date_input(
                            "Date", value=date.fromisoformat(g["game_date"]),
                            key=f"e_date_{gid}")
                    with ec2:
                        e_seq = st.number_input("Game #", min_value=1,
                                                value=g["game_sequence"],
                                                step=1, key=f"e_seq_{gid}")

                    et1c, et2c = st.columns(2)
                    with et1c:
                        st.markdown("<p style='font-size:0.8rem;color:#F97316;"
                                    "font-weight:700;margin-bottom:4px'>TEAM 1</p>",
                                    unsafe_allow_html=True)
                        et1p1 = st.selectbox(
                            "P1", names,
                            index=names.index(id_to_name.get(g["team1_player1_id"], names[0])),
                            key=f"e_t1p1_{gid}", label_visibility="collapsed")
                        et1p2 = st.selectbox(
                            "P2", names,
                            index=names.index(id_to_name.get(g["team1_player2_id"], names[0])),
                            key=f"e_t1p2_{gid}", label_visibility="collapsed")
                        et1s = st.number_input("Score", min_value=0,
                                               value=g["team1_score"],
                                               step=1, key=f"e_t1s_{gid}",
                                               label_visibility="collapsed")
                    with et2c:
                        st.markdown("<p style='font-size:0.8rem;color:#58a6ff;"
                                    "font-weight:700;margin-bottom:4px'>TEAM 2</p>",
                                    unsafe_allow_html=True)
                        et2p1 = st.selectbox(
                            "P1", names,
                            index=names.index(id_to_name.get(g["team2_player1_id"], names[0])),
                            key=f"e_t2p1_{gid}", label_visibility="collapsed")
                        et2p2 = st.selectbox(
                            "P2", names,
                            index=names.index(id_to_name.get(g["team2_player2_id"], names[0])),
                            key=f"e_t2p2_{gid}", label_visibility="collapsed")
                        et2s = st.number_input("Score", min_value=0,
                                               value=g["team2_score"],
                                               step=1, key=f"e_t2s_{gid}",
                                               label_visibility="collapsed")

                    if st.button("💾  Save Changes", key=f"e_save_{gid}"):
                        err = validate_game(options[et1p1], options[et1p2],
                                            options[et2p1], options[et2p2])
                        if err:
                            st.error(err)
                        else:
                            try:
                                db.update_game(gid, {
                                    "game_date": str(e_date),
                                    "game_sequence": int(e_seq),
                                    "team1_player1_id": options[et1p1],
                                    "team1_player2_id": options[et1p2],
                                    "team2_player1_id": options[et2p1],
                                    "team2_player2_id": options[et2p2],
                                    "team1_score": int(et1s),
                                    "team2_score": int(et2s),
                                })
                                st.success("Updated.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

        st.markdown("<br>", unsafe_allow_html=True)

        # -----------------------------------------------------------------------
        # Manage Players
        # -----------------------------------------------------------------------
        section_header("👥", "Manage Players")

        if players:
            player_display = "  ·  ".join(p["name"] for p in players)
            st.markdown(
                f"<p style='color:#8b949e;font-size:0.9rem;margin-bottom:12px'>"
                f"{player_display}</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p style='color:#7d8590;font-size:0.9rem'>No players yet.</p>",
                unsafe_allow_html=True,
            )

        col_inp, col_btn, _ = st.columns([3, 1, 3])
        with col_inp:
            new_name = st.text_input("Player name", key="new_player_name",
                                     label_visibility="collapsed",
                                     placeholder="New player name")
        with col_btn:
            if st.button("Add Player", use_container_width=True):
                if not new_name.strip():
                    st.error("Name cannot be blank.")
                else:
                    try:
                        db.add_player(new_name)
                        st.success(f"Added {new_name.strip()}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
