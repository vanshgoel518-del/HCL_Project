-- ============================================================================
-- Project #21: 7 Analytical Business Queries (SQLite)
-- Oracle differences are annotated inside each query block.
-- ============================================================================

-- QUERY_NAME: q1_5_player_verification
-- Q1: Career verification totals for the 5 benchmark players (P001-P005)
-- Oracle note: SQLite uses `* 1.0` for float division; Oracle performs decimal division on NUMBER automatically.
SELECT
    p.player_id,
    p.player_name,
    t.team_code,
    COUNT(DISTINCT f.match_id) AS matches_played,
    SUM(f.innings_batted) AS innings_batted,
    SUM(CASE WHEN f.innings_batted = 1 THEN f.not_out ELSE 0 END) AS not_outs,
    SUM(f.runs_scored) AS total_runs,
    SUM(f.balls_faced) AS total_balls_faced,
    ROUND(
        CASE
            WHEN (SUM(f.innings_batted) - SUM(CASE WHEN f.innings_batted = 1 THEN f.not_out ELSE 0 END)) > 0
            THEN SUM(f.runs_scored) * 1.0 / (SUM(f.innings_batted) - SUM(CASE WHEN f.innings_batted = 1 THEN f.not_out ELSE 0 END))
            ELSE SUM(f.runs_scored)
        END, 2
    ) AS batting_average,
    ROUND(SUM(f.runs_scored) * 100.0 / NULLIF(SUM(f.balls_faced), 0), 2) AS strike_rate,
    SUM(f.wickets_taken) AS total_wickets,
    SUM(f.balls_bowled) AS total_balls_bowled,
    SUM(f.runs_conceded) AS total_runs_conceded,
    ROUND(COALESCE(SUM(f.runs_conceded) * 1.0 / NULLIF(SUM(f.balls_bowled) / 6.0, 0), 0), 2) AS economy_rate
FROM fact_player_match_stats f
JOIN dim_players p ON f.player_id = p.player_id
JOIN dim_teams t ON p.team_id = t.team_id
WHERE p.player_id IN ('P001', 'P002', 'P003', 'P004', 'P005')
GROUP BY p.player_id, p.player_name, t.team_code
ORDER BY p.player_id;

-- QUERY_NAME: q2_season_batting_ranks
-- Q2: Top 10 batsmen per season with RANK() and DENSE_RANK() preserving ties (e.g., S2023 tie at 739 runs)
-- Oracle note: Identical CTE + RANK()/DENSE_RANK() syntax; Oracle uses NVL instead of COALESCE if preferred.
WITH season_batting AS (
    SELECT
        s.season_year,
        p.player_id,
        p.player_name,
        t.team_code,
        SUM(f.innings_batted) AS innings,
        SUM(CASE WHEN f.innings_batted = 1 THEN f.not_out ELSE 0 END) AS not_outs,
        SUM(f.runs_scored) AS total_runs,
        SUM(f.balls_faced) AS total_balls_faced,
        ROUND(SUM(f.runs_scored) * 100.0 / NULLIF(SUM(f.balls_faced), 0), 2) AS strike_rate
    FROM fact_player_match_stats f
    JOIN dim_matches m ON f.match_id = m.match_id
    JOIN dim_seasons s ON m.season_id = s.season_id
    JOIN dim_players p ON f.player_id = p.player_id
    JOIN dim_teams t ON f.team_id = t.team_id
    GROUP BY s.season_year, p.player_id, p.player_name, t.team_code
),
ranked_batting AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY season_year ORDER BY total_runs DESC) AS rank_skip,
        DENSE_RANK() OVER (PARTITION BY season_year ORDER BY total_runs DESC) AS rank_dense
    FROM season_batting
)
SELECT *
FROM ranked_batting
WHERE rank_skip <= 10
ORDER BY season_year DESC, rank_skip ASC, strike_rate DESC;

-- QUERY_NAME: q3_season_bowling_ranks
-- Q3: Top 10 bowlers per season with RANK() and DENSE_RANK() preserving ties (e.g., S2024 tie at 21 wickets)
WITH season_bowling AS (
    SELECT
        s.season_year,
        p.player_id,
        p.player_name,
        t.team_code,
        SUM(f.wickets_taken) AS total_wickets,
        SUM(f.balls_bowled) AS total_balls_bowled,
        SUM(f.runs_conceded) AS total_runs_conceded,
        ROUND(SUM(f.runs_conceded) * 1.0 / NULLIF(SUM(f.balls_bowled) / 6.0, 0), 2) AS economy_rate
    FROM fact_player_match_stats f
    JOIN dim_matches m ON f.match_id = m.match_id
    JOIN dim_seasons s ON m.season_id = s.season_id
    JOIN dim_players p ON f.player_id = p.player_id
    JOIN dim_teams t ON f.team_id = t.team_id
    WHERE f.balls_bowled > 0
    GROUP BY s.season_year, p.player_id, p.player_name, t.team_code
),
ranked_bowling AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY season_year ORDER BY total_wickets DESC) AS rank_skip,
        DENSE_RANK() OVER (PARTITION BY season_year ORDER BY total_wickets DESC) AS rank_dense
    FROM season_bowling
)
SELECT *
FROM ranked_bowling
WHERE rank_skip <= 10
ORDER BY season_year DESC, rank_skip ASC, economy_rate ASC;

-- QUERY_NAME: q4_yoy_player_runs_lag
-- Q4: Season-over-season player runs comparison using LAG()
-- Oracle note: LAG(...) OVER (PARTITION BY ... ORDER BY ...) works identically in Oracle 11g+.
WITH player_season AS (
    SELECT
        p.player_id,
        p.player_name,
        t.team_code,
        s.season_year,
        SUM(f.runs_scored) AS total_runs
    FROM fact_player_match_stats f
    JOIN dim_matches m ON f.match_id = m.match_id
    JOIN dim_seasons s ON m.season_id = s.season_id
    JOIN dim_players p ON f.player_id = p.player_id
    JOIN dim_teams t ON p.team_id = t.team_id
    GROUP BY p.player_id, p.player_name, t.team_code, s.season_year
)
SELECT
    player_id,
    player_name,
    team_code,
    season_year,
    total_runs,
    LAG(total_runs) OVER (PARTITION BY player_id ORDER BY season_year) AS prev_season_runs,
    total_runs - LAG(total_runs) OVER (PARTITION BY player_id ORDER BY season_year) AS yoy_runs_diff
FROM player_season
ORDER BY player_id, season_year;

-- QUERY_NAME: q5_team_season_summary
-- Q5: Team batting and bowling summary by season (JOIN + GROUP BY)
SELECT
    s.season_year,
    t.team_code,
    t.team_name,
    COUNT(DISTINCT f.match_id) AS matches_played,
    SUM(f.runs_scored) AS total_runs,
    SUM(f.fours) AS total_fours,
    SUM(f.sixes) AS total_sixes,
    SUM(f.wickets_taken) AS total_wickets,
    ROUND(SUM(f.runs_scored) * 100.0 / NULLIF(SUM(f.balls_faced), 0), 2) AS team_batting_sr,
    ROUND(SUM(f.runs_conceded) * 1.0 / NULLIF(SUM(f.balls_bowled) / 6.0, 0), 2) AS team_bowling_econ
FROM fact_player_match_stats f
JOIN dim_matches m ON f.match_id = m.match_id
JOIN dim_seasons s ON m.season_id = s.season_id
JOIN dim_teams t ON f.team_id = t.team_id
GROUP BY s.season_year, t.team_code, t.team_name
ORDER BY s.season_year DESC, total_runs DESC;

-- QUERY_NAME: q6_player_performance_tiers
-- Q6: Player season performance tiers using CASE expression
WITH season_totals AS (
    SELECT
        s.season_year,
        p.player_id,
        p.player_name,
        p.player_role,
        SUM(f.runs_scored) AS total_runs,
        SUM(f.wickets_taken) AS total_wickets
    FROM fact_player_match_stats f
    JOIN dim_matches m ON f.match_id = m.match_id
    JOIN dim_seasons s ON m.season_id = s.season_id
    JOIN dim_players p ON f.player_id = p.player_id
    GROUP BY s.season_year, p.player_id, p.player_name, p.player_role
)
SELECT
    season_year,
    player_id,
    player_name,
    player_role,
    total_runs,
    total_wickets,
    CASE
        WHEN total_runs >= 400 THEN 'Elite'
        WHEN total_runs >= 200 THEN 'Consistent'
        ELSE 'Supporting'
    END AS batting_tier
FROM season_totals
ORDER BY season_year DESC, total_runs DESC;

-- QUERY_NAME: q7_toss_and_venue_impact
-- Q7: Toss decision and venue win-rate impact across seasons
-- Oracle note: In Oracle, extract year via EXTRACT(YEAR FROM match_date); SQLite stores ISO text so we join dim_seasons.
SELECT
    s.season_year,
    m.venue,
    m.toss_decision,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) AS toss_winner_wins,
    ROUND(
        SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS toss_win_pct
FROM dim_matches m
JOIN dim_seasons s ON m.season_id = s.season_id
GROUP BY s.season_year, m.venue, m.toss_decision
ORDER BY s.season_year DESC, total_matches DESC, m.venue;
