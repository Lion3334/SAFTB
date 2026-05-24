-- SAFTB Lifetime Leaderboard — Supabase Schema
-- Run this in the Supabase SQL editor to initialize your database.

create extension if not exists "pgcrypto";

create table if not exists players (
    id uuid primary key default gen_random_uuid(),
    name text unique not null,
    created_at timestamptz default now()
);

create table if not exists games (
    id uuid primary key default gen_random_uuid(),
    game_date date not null,
    game_sequence integer not null,
    team1_player1_id uuid not null references players(id),
    team1_player2_id uuid not null references players(id),
    team2_player1_id uuid not null references players(id),
    team2_player2_id uuid not null references players(id),
    team1_score integer not null check (team1_score >= 0),
    team2_score integer not null check (team2_score >= 0),
    created_at timestamptz default now(),
    constraint uq_game_date_sequence unique (game_date, game_sequence)
);
