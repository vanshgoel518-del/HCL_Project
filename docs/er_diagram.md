# Star Schema ER Diagram & Draw.io Guide — Project #21

## 1. Star Schema Mermaid ER Diagram

```mermaid
erDiagram
    DIM_TEAMS ||--o{ DIM_SEASONS : "champion_team_id"
    DIM_TEAMS ||--o{ DIM_PLAYERS : "team_id"
    DIM_TEAMS ||--o{ DIM_MATCHES : "team1_team2_toss_winner"
    DIM_TEAMS ||--o{ FACT_PLAYER_MATCH_STATS : "team_id"
    DIM_SEASONS ||--o{ DIM_MATCHES : "season_id"
    DIM_PLAYERS ||--o{ FACT_PLAYER_MATCH_STATS : "player_id"
    DIM_MATCHES ||--o{ FACT_PLAYER_MATCH_STATS : "match_id"

    DIM_TEAMS {
        string team_id PK
        string team_code UK
        string team_name
        string home_city
        string home_venue
    }

    DIM_SEASONS {
        string season_id PK
        int season_year UK
        string host_country
        int total_teams
        string champion_team_id FK
    }

    DIM_PLAYERS {
        string player_id PK
        string player_name
        string team_id FK
        string player_role
        string batting_hand
        string bowling_style
        string nationality
        int is_active
    }

    DIM_MATCHES {
        string match_id PK
        string season_id FK
        date match_date
        string venue
        string city
        string team1_id FK
        string team2_id FK
        string toss_winner_id FK
        string toss_decision
        string winner_team_id FK
        int win_margin_runs
        int win_margin_wickets
    }

    FACT_PLAYER_MATCH_STATS {
        string stat_id PK
        string match_id FK
        string player_id FK
        string team_id FK
        int innings_batted
        int runs_scored
        int balls_faced
        int fours
        int sixes
        int not_out
        float overs_bowled
        int balls_bowled
        int runs_conceded
        int wickets_taken
        int maidens
        int catches
        int stumpings
        int player_of_match
        int balls_faced_imputed
    }
```

---

## 2. Step-by-Step Instructions to Draw in draw.io
1. Open [app.diagrams.net](https://app.diagrams.net) and create a blank diagram (`IPL_Star_Schema.drawio`).
2. In the left panel, enable **Entity Relation** shapes (`More Shapes -> Software -> Entity Relation`).
3. Drag **5 Table boxes** onto the canvas:
   - Place **`fact_player_match_stats`** in the **center** (highlight header in Navy `#1F4E78`).
   - Place the 4 dimensions around it in a star layout: **`dim_players`** (left), **`dim_matches`** (top), **`dim_teams`** (right), and **`dim_seasons`** (top-right).
4. Add columns inside each table box and mark **`PK`** (Primary Key) and **`FK`** (Foreign Key) on the left column slot.
5. Connect relationships using **Crow's Foot** connectors (`1` on the Dimension side, `0..N` / Many on the Fact side):
   - `dim_players.player_id` (1) ---> (*) `fact_player_match_stats.player_id`
   - `dim_matches.match_id` (1) ---> (*) `fact_player_match_stats.match_id`
   - `dim_teams.team_id` (1) ---> (*) `fact_player_match_stats.team_id`
   - `dim_seasons.season_id` (1) ---> (*) `dim_matches.season_id`
   - `dim_teams.team_id` (1) ---> (*) `dim_players.team_id`
6. Export via **File -> Export as -> PNG / PDF** to include in your report or presentation.
