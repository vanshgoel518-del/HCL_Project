-- ============================================================================
-- Project #21: IPL Player Performance Star Schema (Oracle SQL DDL)
-- Differences from SQLite:
--   1. TEXT -> VARCHAR2(n); INTEGER -> NUMBER(p); REAL -> NUMBER(4,1)
--   2. match_date uses native DATE type (load via TO_DATE(..., 'YYYY-MM-DD'))
--   3. DROP TABLE ... CASCADE CONSTRAINTS PURGE (no IF EXISTS prior to Oracle 23c)
--   4. Explicit named CONSTRAINT clauses for PK, FK, UNIQUE, CHECK
-- ============================================================================

DROP TABLE fact_player_match_stats CASCADE CONSTRAINTS;
DROP TABLE dim_matches CASCADE CONSTRAINTS;
DROP TABLE dim_players CASCADE CONSTRAINTS;
DROP TABLE dim_seasons CASCADE CONSTRAINTS;
DROP TABLE dim_teams CASCADE CONSTRAINTS;

CREATE TABLE dim_teams (
    team_id    VARCHAR2(10)  CONSTRAINT pk_dim_teams PRIMARY KEY,
    team_code  VARCHAR2(10)  NOT NULL CONSTRAINT uq_dim_teams_code UNIQUE,
    team_name  VARCHAR2(80)  NOT NULL,
    home_city  VARCHAR2(50)  NOT NULL,
    home_venue VARCHAR2(100) NOT NULL
);

CREATE TABLE dim_seasons (
    season_id        VARCHAR2(10) CONSTRAINT pk_dim_seasons PRIMARY KEY,
    season_year      NUMBER(4)    NOT NULL CONSTRAINT uq_dim_seasons_year UNIQUE
                                  CONSTRAINT chk_season_year CHECK (season_year BETWEEN 2008 AND 2030),
    host_country     VARCHAR2(40) NOT NULL,
    total_teams      NUMBER(2)    NOT NULL CONSTRAINT chk_total_teams CHECK (total_teams > 0),
    champion_team_id VARCHAR2(10) NOT NULL,
    CONSTRAINT fk_seasons_champ FOREIGN KEY (champion_team_id) REFERENCES dim_teams(team_id)
);

CREATE TABLE dim_players (
    player_id     VARCHAR2(10) CONSTRAINT pk_dim_players PRIMARY KEY,
    player_name   VARCHAR2(80) NOT NULL,
    team_id       VARCHAR2(10) NOT NULL,
    player_role   VARCHAR2(30) NOT NULL CONSTRAINT chk_player_role CHECK (player_role IN ('Batsman', 'Bowler', 'All-Rounder', 'Wicket-Keeper')),
    batting_hand  VARCHAR2(20) NOT NULL CONSTRAINT chk_batting_hand CHECK (batting_hand IN ('Right-hand', 'Left-hand')),
    bowling_style VARCHAR2(40) NOT NULL,
    nationality   VARCHAR2(20) NOT NULL CONSTRAINT chk_nationality CHECK (nationality IN ('India', 'Overseas')),
    is_active     NUMBER(1)    NOT NULL CONSTRAINT chk_is_active CHECK (is_active IN (0, 1)),
    CONSTRAINT fk_players_team FOREIGN KEY (team_id) REFERENCES dim_teams(team_id)
);

CREATE TABLE dim_matches (
    match_id           VARCHAR2(15)  CONSTRAINT pk_dim_matches PRIMARY KEY,
    season_id          VARCHAR2(10)  NOT NULL,
    match_date         DATE          NOT NULL,
    venue              VARCHAR2(100) NOT NULL,
    city               VARCHAR2(50)  NOT NULL,
    team1_id           VARCHAR2(10)  NOT NULL,
    team2_id           VARCHAR2(10)  NOT NULL,
    toss_winner_id     VARCHAR2(10)  NOT NULL,
    toss_decision      VARCHAR2(10)  NOT NULL CONSTRAINT chk_toss_decision CHECK (toss_decision IN ('bat', 'field')),
    winner_team_id     VARCHAR2(10)  NOT NULL,
    win_margin_runs    NUMBER(3)     CONSTRAINT chk_win_runs CHECK (win_margin_runs IS NULL OR win_margin_runs >= 0),
    win_margin_wickets NUMBER(2)     CONSTRAINT chk_win_wkts CHECK (win_margin_wickets IS NULL OR win_margin_wickets BETWEEN 1 AND 10),
    CONSTRAINT fk_matches_season  FOREIGN KEY (season_id) REFERENCES dim_seasons(season_id),
    CONSTRAINT fk_matches_team1   FOREIGN KEY (team1_id) REFERENCES dim_teams(team_id),
    CONSTRAINT fk_matches_team2   FOREIGN KEY (team2_id) REFERENCES dim_teams(team_id),
    CONSTRAINT fk_matches_toss    FOREIGN KEY (toss_winner_id) REFERENCES dim_teams(team_id),
    CONSTRAINT fk_matches_winner  FOREIGN KEY (winner_team_id) REFERENCES dim_teams(team_id)
);

CREATE TABLE fact_player_match_stats (
    stat_id             VARCHAR2(15) CONSTRAINT pk_fact_player_stats PRIMARY KEY,
    match_id            VARCHAR2(15) NOT NULL,
    player_id           VARCHAR2(10) NOT NULL,
    team_id             VARCHAR2(10) NOT NULL,
    innings_batted      NUMBER(1)    NOT NULL CONSTRAINT chk_innings_batted CHECK (innings_batted IN (0, 1)),
    runs_scored         NUMBER(4)    NOT NULL CONSTRAINT chk_runs_scored CHECK (runs_scored >= 0),
    balls_faced         NUMBER(4)    NOT NULL CONSTRAINT chk_balls_faced CHECK (balls_faced >= 0),
    fours               NUMBER(3)    NOT NULL CONSTRAINT chk_fours CHECK (fours >= 0),
    sixes               NUMBER(3)    NOT NULL CONSTRAINT chk_sixes CHECK (sixes >= 0),
    not_out             NUMBER(1)    NOT NULL CONSTRAINT chk_not_out CHECK (not_out IN (0, 1)),
    overs_bowled        NUMBER(3,1)  NOT NULL CONSTRAINT chk_overs_bowled CHECK (overs_bowled >= 0),
    balls_bowled        NUMBER(2)    NOT NULL CONSTRAINT chk_balls_bowled CHECK (balls_bowled BETWEEN 0 AND 24),
    runs_conceded       NUMBER(4)    NOT NULL CONSTRAINT chk_runs_conceded CHECK (runs_conceded >= 0),
    wickets_taken       NUMBER(2)    NOT NULL CONSTRAINT chk_wickets_taken CHECK (wickets_taken BETWEEN 0 AND 10),
    maidens             NUMBER(2)    NOT NULL CONSTRAINT chk_maidens CHECK (maidens >= 0),
    catches             NUMBER(2)    NOT NULL CONSTRAINT chk_catches CHECK (catches >= 0),
    stumpings           NUMBER(2)    NOT NULL CONSTRAINT chk_stumpings CHECK (stumpings >= 0),
    player_of_match     NUMBER(1)    NOT NULL CONSTRAINT chk_pom CHECK (player_of_match IN (0, 1)),
    balls_faced_imputed NUMBER(1)    DEFAULT 0 NOT NULL CONSTRAINT chk_bf_imp CHECK (balls_faced_imputed IN (0, 1)),
    CONSTRAINT fk_fact_match  FOREIGN KEY (match_id)  REFERENCES dim_matches(match_id),
    CONSTRAINT fk_fact_player FOREIGN KEY (player_id) REFERENCES dim_players(player_id),
    CONSTRAINT fk_fact_team   FOREIGN KEY (team_id)   REFERENCES dim_teams(team_id)
);

CREATE INDEX idx_ora_fact_match  ON fact_player_match_stats(match_id);
CREATE INDEX idx_ora_fact_player ON fact_player_match_stats(player_id);
CREATE INDEX idx_ora_fact_team   ON fact_player_match_stats(team_id);
CREATE INDEX idx_ora_matches_ssn ON dim_matches(season_id);
