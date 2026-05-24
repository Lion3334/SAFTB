import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_anon_key"]
    return create_client(url, key)


@st.cache_data(ttl=60)
def fetch_players() -> list[dict]:
    client = get_client()
    res = client.table("players").select("*").order("name").execute()
    return res.data


@st.cache_data(ttl=60)
def fetch_games() -> list[dict]:
    client = get_client()
    res = (
        client.table("games")
        .select("*")
        .order("game_date", desc=True)
        .order("game_sequence", desc=True)
        .execute()
    )
    return res.data


def add_player(name: str) -> dict:
    client = get_client()
    res = client.table("players").insert({"name": name.strip()}).execute()
    fetch_players.clear()
    return res.data[0]


def get_next_game_sequence(game_date: str) -> int:
    """Returns the next game sequence number for a given date (not cached)."""
    client = get_client()
    res = (
        client.table("games")
        .select("game_sequence")
        .eq("game_date", game_date)
        .order("game_sequence", desc=True)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]["game_sequence"] + 1
    return 1


def add_game(payload: dict) -> dict:
    client = get_client()
    res = client.table("games").insert(payload).execute()
    fetch_games.clear()
    return res.data[0]


def update_game(game_id: str, payload: dict) -> dict:
    client = get_client()
    res = client.table("games").update(payload).eq("id", game_id).execute()
    fetch_games.clear()
    return res.data[0]


def delete_game(game_id: str) -> None:
    client = get_client()
    client.table("games").delete().eq("id", game_id).execute()
    fetch_games.clear()
