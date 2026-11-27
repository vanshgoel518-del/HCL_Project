-- ============================================================================
-- Project #21: IPL Player Performance Star Schema (SQLite DDL)
-- ============================================================================
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_player_match_stats;
DROP TABLE IF EXISTS dim_matches;
DROP TABLE IF EXISTS dim_players;
DROP TABLE IF EXISTS dim_seasons;
DROP TABLE IF EXISTS dim_teams;

CREATE TABLE dim_teams (
    team_id    TEXT PRIMARY KEY,
    team_code  TEXT NOT NULL UNIQUE,
    team_name  TEXT NOT NULL,
    home_city  TEXT NOT NULL,
    home_venue TEXT NOT NULL
);

CREATE TABLE dim_seasons (
    season_id        TEXT PRIMARY KEY,
    season_year      INTEGER NOT NULL UNIQUE CHECK (season_year BETWEEN 2008 AND 2030),
    host_country     TEXT NOT NULL,
    total_teams      INTEGER NOT NULL CHECK (total_teams > 0),
    champion_team_id TEXT NOT NULL,
    FOREIGN KEY (champion_team_id) REFERENCES dim_teams(team_id)
);

CREATE TABLE dim_players (
    player_id     TEXT PRIMARY KEY,
    player_name   TEXT NOT NULL,
    team_id       TEXT NOT NULL,
    player_role   TEXT NOT NULL CHECK (player_role IN ('Batsman', 'Bowler', 'All-Rounder', 'Wicket-Keeper')),
    batting_hand  TEXT NOT NULL CHECK (batting_hand IN ('Right-hand', 'Left-hand')),
    bowling_style TEXT NOT NULL,
    nationality   TEXT NOT NULL CHECK (nationality IN ('India', 'Overseas')),
    is_active     INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    FOREIGN KEY (team_id) REFERENCES dim_teams(team_id)
);

CREATE TABLE dim_matches (
    match_id           TEXT PRIMARY KEY,
    season_id          TEXT NOT NULL,
    match_date         TEXT NOT NULL, -- ISO YYYY-MM-DD (Oracle uses DATE)
    venue              TEXT NOT NULL,
    city               TEXT NOT NULL,
    team1_id           TEXT NOT NULL,
    team2_id           TEXT NOT NULL,
    toss_winner_id     TEXT NOT NULL,
    toss_decision      TEXT NOT NULL CHECK (toss_decision IN ('bat', 'field')),
    winner_team_id     TEXT NOT NULL,
    win_margin_runs    INTEGER CHECK (win_margin_runs IS NULL OR win_margin_runs >= 0),
    win_margin_wickets INTEGER CHECK (win_margin_wickets IS NULL OR win_margin_wickets BETWEEN 1 AND 10),
    FOREIGN KEY (season_id) REFERENCES dim_seasons(season_id),
    FOREIGN KEY (team1_id) REFERENCES dim_teams(team_id),
    FOREIGN KEY (team2_id) REFERENCES dim_teams(team_id),
    FOREIGN KEY (toss_winner_id) REFERENCES dim_teams(team_id),
    FOREIGN KEY (winner_team_id) REFERENCES dim_teams(team_id)
);

CREATE TABLE fact_player_match_stats (
    stat_id            TEXT PRIMARY KEY,
    match_id           TEXT NOT NULL,
    player_id          TEXT NOT NULL,
    team_id            TEXT NOT NULL,
    innings_batted     INTEGER NOT NULL CHECK (innings_batted IN (0, 1)),
    runs_scored        INTEGER NOT NULL CHECK (runs_scored >= 0),
    balls_faced        INTEGER NOT NULL CHECK (balls_faced >= 0),
    fours              INTEGER NOT NULL CHECK (fours >= 0),
    sixes              INTEGER NOT NULL CHECK (sixes >= 0),
    not_out            INTEGER NOT NULL CHECK (not_out IN (0, 1)),
    overs_bowled       REAL NOT NULL CHECK (overs_bowled >= 0),
    balls_bowled       INTEGER NOT NULL CHECK (balls_bowled BETWEEN 0 AND 24),
    runs_conceded      INTEGER NOT NULL CHECK (runs_conceded >= 0),
    wickets_taken      INTEGER NOT NULL CHECK (wickets_taken BETWEEN 0 AND 10),
    maidens            INTEGER NOT NULL CHECK (maidens >= 0),
    catches            INTEGER NOT NULL CHECK (catches >= 0),
    stumpings          INTEGER NOT NULL CHECK (stumpings >= 0),
    player_of_match    INTEGER NOT NULL CHECK (player_of_match IN (0, 1)),
    balls_faced_imputed INTEGER NOT NULL DEFAULT 0 CHECK (balls_faced_imputed IN (0, 1)),
    FOREIGN KEY (match_id) REFERENCES dim_matches(match_id),
    FOREIGN KEY (player_id) REFERENCES dim_players(player_id),
    FOREIGN KEY (team_id) REFERENCES dim_teams(team_id)
);

CREATE INDEX idx_fact_match ON fact_player_match_stats(match_id);
CREATE INDEX idx_fact_player ON fact_player_match_stats(player_id);
CREATE INDEX idx_fact_team ON fact_player_match_stats(team_id);
CREATE INDEX idx_matches_season ON dim_matches(season_id);
