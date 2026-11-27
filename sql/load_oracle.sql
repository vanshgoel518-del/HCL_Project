-- ============================================================================
-- Project #21: Oracle Data Load Script & SQL*Loader Reference
-- Load order respects Foreign Key hierarchy:
--   1. dim_teams -> 2. dim_seasons -> 3. dim_players -> 4. dim_matches -> 5. fact_player_match_stats
-- ============================================================================

-- Sample INSERT statements for dim_teams & dim_seasons
INSERT INTO dim_teams VALUES ('T01', 'RCB', 'Royal Challengers Bengaluru', 'Bengaluru', 'M. Chinnaswamy Stadium');
INSERT INTO dim_teams VALUES ('T02', 'MI',  'Mumbai Indians',              'Mumbai',    'Wankhede Stadium');
INSERT INTO dim_teams VALUES ('T03', 'CSK', 'Chennai Super Kings',         'Chennai',   'MA Chidambaram Stadium');
INSERT INTO dim_teams VALUES ('T04', 'KKR', 'Kolkata Knight Riders',       'Kolkata',   'Eden Gardens');
INSERT INTO dim_teams VALUES ('T05', 'RR',  'Rajasthan Royals',            'Jaipur',    'Sawai Mansingh Stadium');
INSERT INTO dim_teams VALUES ('T06', 'SRH', 'Sunrisers Hyderabad',         'Hyderabad', 'Rajiv Gandhi Intl Stadium');
INSERT INTO dim_teams VALUES ('T07', 'GT',  'Gujarat Titans',              'Ahmedabad', 'Narendra Modi Stadium');
INSERT INTO dim_teams VALUES ('T08', 'DC',  'Delhi Capitals',              'Delhi',     'Arun Jaitley Stadium');

INSERT INTO dim_seasons VALUES ('S2021', 2021, 'India/UAE', 8, 'T03');
INSERT INTO dim_seasons VALUES ('S2022', 2022, 'India',     8, 'T07');
INSERT INTO dim_seasons VALUES ('S2023', 2023, 'India',     8, 'T03');
INSERT INTO dim_seasons VALUES ('S2024', 2024, 'India',     8, 'T04');

-- Sample INSERT for dim_matches showing Oracle TO_DATE conversion:
INSERT INTO dim_matches (
    match_id, season_id, match_date, venue, city,
    team1_id, team2_id, toss_winner_id, toss_decision, winner_team_id,
    win_margin_runs, win_margin_wickets
) VALUES (
    'M2021_001', 'S2021', TO_DATE('2021-04-01', 'YYYY-MM-DD'),
    'M. Chinnaswamy Stadium', 'Bengaluru',
    'T01', 'T02', 'T02', 'field', 'T02', NULL, 3
);

COMMIT;

-- ============================================================================
-- SQL*Loader Control File Example (load_fact_player_stats.ctl)
-- Run via: sqlldr userid=username/password@orcl control=load_fact_player_stats.ctl
-- ============================================================================
/*
OPTIONS (SKIP=1, DIRECT=TRUE)
LOAD DATA
INFILE 'data/clean/fact_player_match_stats.csv'
INTO TABLE fact_player_match_stats
APPEND
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
TRAILING NULLCOLS
(
    stat_id,
    match_id,
    player_id,
    team_id,
    innings_batted,
    runs_scored,
    balls_faced,
    fours,
    sixes,
    not_out,
    overs_bowled,
    balls_bowled,
    runs_conceded,
    wickets_taken,
    maidens,
    catches,
    stumpings,
    player_of_match,
    balls_faced_imputed
)
*/

-- For dim_matches.csv via SQL*Loader, convert ISO date strings using:
--   match_date DATE "YYYY-MM-DD"
