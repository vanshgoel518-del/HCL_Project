-- ============================================================================
-- Project #21: Analytical Queries & Views (Oracle SQL)
-- Key Oracle Differences vs SQLite:
--   1. CREATE OR REPLACE VIEW supported directly for reusable BI views
--   2. No `* 1.0` needed for floating-point division on NUMBER columns
--   3. NVL() / COALESCE() supported; DATE columns use EXTRACT(YEAR FROM ...)
--   4. FETCH FIRST 10 ROWS ONLY (Oracle 12c+) available for inline row limits
-- ============================================================================

-- VIEW 1: Career 5-Player Verification & All-Player Summary View
CREATE OR REPLACE VIEW vw_player_career_summary AS
SELECT
    p.player_id,
    p.player_name,
    t.team_code,
    p.player_role,
    COUNT(DISTINCT f.match_id) AS matches_played,
    SUM(f.innings_batted) AS innings_batted,
    SUM(CASE WHEN f.innings_batted = 1 THEN f.not_out ELSE 0 END) AS not_outs,
    SUM(f.runs_scored) AS total_runs,
    SUM(f.balls_faced) AS total_balls_faced,
    ROUND(
        CASE
            WHEN (SUM(f.innings_batted) - SUM(CASE WHEN f.innings_batted = 1 THEN f.not_out ELSE 0 END)) > 0
            THEN SUM(f.runs_scored) / (SUM(f.innings_batted) - SUM(CASE WHEN f.innings_batted = 1 THEN f.not_out ELSE 0 END))
            ELSE SUM(f.runs_scored)
        END, 2
    ) AS batting_average,
    ROUND((SUM(f.runs_scored) * 100) / NULLIF(SUM(f.balls_faced), 0), 2) AS strike_rate,
    SUM(f.wickets_taken) AS total_wickets,
    SUM(f.balls_bowled) AS total_balls_bowled,
    SUM(f.runs_conceded) AS total_runs_conceded,
    ROUND(NVL(SUM(f.runs_conceded) / NULLIF(SUM(f.balls_bowled) / 6, 0), 0), 2) AS economy_rate
FROM fact_player_match_stats f
JOIN dim_players p ON f.player_id = p.player_id
JOIN dim_teams t ON p.team_id = t.team_id
GROUP BY p.player_id, p.player_name, t.team_code, p.player_role;

-- VIEW 2: Season Batting Leaderboard with Tie-Preserving RANK / DENSE_RANK
CREATE OR REPLACE VIEW vw_season_batting_leaderboard AS
SELECT
    season_year,
    player_id,
    player_name,
    team_code,
    innings,
    not_outs,
    total_runs,
    total_balls_faced,
    strike_rate,
    RANK() OVER (PARTITION BY season_year ORDER BY total_runs DESC) AS rank_skip,
    DENSE_RANK() OVER (PARTITION BY season_year ORDER BY total_runs DESC) AS rank_dense
FROM (
    SELECT
        s.season_year,
        p.player_id,
        p.player_name,
        t.team_code,
        SUM(f.innings_batted) AS innings,
        SUM(CASE WHEN f.innings_batted = 1 THEN f.not_out ELSE 0 END) AS not_outs,
        SUM(f.runs_scored) AS total_runs,
        SUM(f.balls_faced) AS total_balls_faced,
        ROUND((SUM(f.runs_scored) * 100) / NULLIF(SUM(f.balls_faced), 0), 2) AS strike_rate
    FROM fact_player_match_stats f
    JOIN dim_matches m ON f.match_id = m.match_id
    JOIN dim_seasons s ON m.season_id = s.season_id
    JOIN dim_players p ON f.player_id = p.player_id
    JOIN dim_teams t ON f.team_id = t.team_id
    GROUP BY s.season_year, p.player_id, p.player_name, t.team_code
);

-- VIEW 3: Season Bowling Leaderboard with Tie-Preserving RANK / DENSE_RANK
CREATE OR REPLACE VIEW vw_season_bowling_leaderboard AS
SELECT
    season_year,
    player_id,
    player_name,
    team_code,
    total_wickets,
    total_balls_bowled,
    total_runs_conceded,
    economy_rate,
    RANK() OVER (PARTITION BY season_year ORDER BY total_wickets DESC) AS rank_skip,
    DENSE_RANK() OVER (PARTITION BY season_year ORDER BY total_wickets DESC) AS rank_dense
FROM (
    SELECT
        s.season_year,
        p.player_id,
        p.player_name,
        t.team_code,
        SUM(f.wickets_taken) AS total_wickets,
        SUM(f.balls_bowled) AS total_balls_bowled,
        SUM(f.runs_conceded) AS total_runs_conceded,
        ROUND(SUM(f.runs_conceded) / NULLIF(SUM(f.balls_bowled) / 6, 0), 2) AS economy_rate
    FROM fact_player_match_stats f
    JOIN dim_matches m ON f.match_id = m.match_id
    JOIN dim_seasons s ON m.season_id = s.season_id
    JOIN dim_players p ON f.player_id = p.player_id
    JOIN dim_teams t ON f.team_id = t.team_id
    WHERE f.balls_bowled > 0
    GROUP BY s.season_year, p.player_id, p.player_name, t.team_code
);

-- Q1: Verify 5 benchmark players
SELECT * FROM vw_player_career_summary
WHERE player_id IN ('P001', 'P002', 'P003', 'P004', 'P005')
ORDER BY player_id;

-- Q2: Top 10 batsmen per season (handles S2023 tie at 739 runs)
SELECT * FROM vw_season_batting_leaderboard
WHERE rank_skip <= 10
ORDER BY season_year DESC, rank_skip ASC, strike_rate DESC;

-- Q3: Top 10 bowlers per season (handles S2024 tie at 21 wickets)
SELECT * FROM vw_season_bowling_leaderboard
WHERE rank_skip <= 10
ORDER BY season_year DESC, rank_skip ASC, economy_rate ASC;

-- Q4: Season-over-season player runs comparison using LAG()
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

-- Q5: Team batting and bowling summary by season
SELECT
    s.season_year,
    t.team_code,
    t.team_name,
    COUNT(DISTINCT f.match_id) AS matches_played,
    SUM(f.runs_scored) AS total_runs,
    SUM(f.fours) AS total_fours,
    SUM(f.sixes) AS total_sixes,
    SUM(f.wickets_taken) AS total_wickets,
    ROUND((SUM(f.runs_scored) * 100) / NULLIF(SUM(f.balls_faced), 0), 2) AS team_batting_sr,
    ROUND(SUM(f.runs_conceded) / NULLIF(SUM(f.balls_bowled) / 6, 0), 2) AS team_bowling_econ
FROM fact_player_match_stats f
JOIN dim_matches m ON f.match_id = m.match_id
JOIN dim_seasons s ON m.season_id = s.season_id
JOIN dim_teams t ON f.team_id = t.team_id
GROUP BY s.season_year, t.team_code, t.team_name
ORDER BY s.season_year DESC, total_runs DESC;

-- Q6: Player performance tiers using CASE
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

-- Q7: Toss decision & venue win-rate impact across seasons (uses Oracle EXTRACT(YEAR FROM match_date))
SELECT
    EXTRACT(YEAR FROM m.match_date) AS season_year,
    m.venue,
    m.toss_decision,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) AS toss_winner_wins,
    ROUND(
        (SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) * 100) / COUNT(*),
        2
    ) AS toss_win_pct
FROM dim_matches m
GROUP BY EXTRACT(YEAR FROM m.match_date), m.venue, m.toss_decision
ORDER BY season_year DESC, total_matches DESC, m.venue;
