/*
osu! Player Performance Analytics
Dashboard-ready PostgreSQL views

These views create a cleaner reporting layer for Power BI.
They are based on the loaded PostgreSQL tables:
- player_profile_snapshots
- player_best_scores
*/


DROP VIEW IF EXISTS vw_star_rating_summary;
DROP VIEW IF EXISTS vw_mod_summary;
DROP VIEW IF EXISTS vw_monthly_score_summary;
DROP VIEW IF EXISTS vw_profile_snapshot_latest;
DROP VIEW IF EXISTS vw_best_scores_dashboard;


/*
Main score-level dashboard view.

Purpose:
Provides one row per best score with cleaned reporting fields.
This should be the main Power BI table for score-level visuals.
*/
CREATE OR REPLACE VIEW vw_best_scores_dashboard AS
SELECT
    score_id,
    username,
    user_id,
    top_play_rank,

    pp,
    accuracy,
    ROUND(accuracy * 100, 2) AS accuracy_percent,
    rank,
    COALESCE(NULLIF(mods, ''), 'NM') AS mods_clean,

    score,
    max_combo,
    passed,
    perfect,

    count_300,
    count_100,
    count_50,
    count_miss,

    weight_percentage,
    weight_pp,

    beatmap_id,
    beatmapset_id,
    beatmap_star_rating,
    ROUND((pp / NULLIF(beatmap_star_rating, 0)), 2) AS pp_per_star,

    beatmap_bpm,
    beatmap_cs,
    beatmap_ar,
    beatmap_od,
    beatmap_hp,
    beatmap_total_length,
    beatmap_hit_length,
    beatmap_status,

    beatmapset_artist,
    beatmapset_title,
    beatmapset_creator,
    beatmap_difficulty_name,

    CONCAT(
        beatmapset_artist,
        ' - ',
        beatmapset_title,
        ' [',
        beatmap_difficulty_name,
        ']'
    ) AS beatmap_full_name,

    created_at,
    DATE_TRUNC('month', created_at)::date AS score_month,
    EXTRACT(YEAR FROM created_at)::int AS score_year,

    extracted_at_utc,
    loaded_at_utc
FROM player_best_scores;


/*
Latest profile snapshot view.

Purpose:
Returns the most recently loaded profile snapshot for each player.
Useful for Power BI card visuals.
*/
CREATE OR REPLACE VIEW vw_profile_snapshot_latest AS
WITH ranked_snapshots AS (
    SELECT
        snapshot_id,
        extracted_at_utc,
        source,
        mode,
        user_id,
        username,
        country_code,
        country_name,
        global_rank,
        country_rank,
        pp AS profile_pp,
        hit_accuracy AS profile_accuracy_percent,
        play_count,
        play_time,
        total_score,
        ranked_score,
        maximum_combo,
        replays_watched,
        level_current,
        level_progress,
        loaded_at_utc,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY extracted_at_utc DESC, loaded_at_utc DESC
        ) AS snapshot_rank
    FROM player_profile_snapshots
)
SELECT
    snapshot_id,
    extracted_at_utc,
    source,
    mode,
    user_id,
    username,
    country_code,
    country_name,
    global_rank,
    country_rank,
    profile_pp,
    profile_accuracy_percent,
    play_count,
    play_time,
    total_score,
    ranked_score,
    maximum_combo,
    replays_watched,
    level_current,
    level_progress,
    loaded_at_utc
FROM ranked_snapshots
WHERE snapshot_rank = 1;


/*
Monthly summary of current top 100 plays.

Purpose:
Shows when the player's current top plays were achieved.
This does not represent full player history; it summarizes only the current top 100 best scores.
*/
CREATE OR REPLACE VIEW vw_monthly_score_summary AS
SELECT
    DATE_TRUNC('month', created_at)::date AS score_month,
    EXTRACT(YEAR FROM created_at)::int AS score_year,
    COUNT(*) AS top_score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(MAX(pp), 2) AS max_pp,
    ROUND(MIN(pp), 2) AS min_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating,
    ROUND(AVG(count_miss), 2) AS avg_miss_count
FROM player_best_scores
WHERE created_at IS NOT NULL
GROUP BY
    DATE_TRUNC('month', created_at),
    EXTRACT(YEAR FROM created_at);


/*
Mod combination summary.

Purpose:
Compares score count, pp, accuracy, and difficulty by mod combination.
Useful for Power BI bar charts.
*/
CREATE OR REPLACE VIEW vw_mod_summary AS
SELECT
    COALESCE(NULLIF(mods, ''), 'NM') AS mods_clean,
    COUNT(*) AS score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(MAX(pp), 2) AS max_pp,
    ROUND(MIN(pp), 2) AS min_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating,
    ROUND(AVG(count_miss), 2) AS avg_miss_count
FROM player_best_scores
GROUP BY COALESCE(NULLIF(mods, ''), 'NM');


/*
Star rating bucket summary.

Purpose:
Groups scores by beatmap difficulty range.
This supports the main analysis question about whether harder maps produce higher pp even with lower accuracy.
*/
CREATE OR REPLACE VIEW vw_star_rating_summary AS
WITH star_buckets AS (
    SELECT
        CASE
            WHEN beatmap_star_rating >= 8.0 THEN '8.0+ stars'
            WHEN beatmap_star_rating >= 7.5 THEN '7.5 - 7.99 stars'
            WHEN beatmap_star_rating >= 7.0 THEN '7.0 - 7.49 stars'
            WHEN beatmap_star_rating >= 6.5 THEN '6.5 - 6.99 stars'
            ELSE 'Below 6.5 stars'
        END AS star_rating_bucket,
        CASE
            WHEN beatmap_star_rating >= 8.0 THEN 1
            WHEN beatmap_star_rating >= 7.5 THEN 2
            WHEN beatmap_star_rating >= 7.0 THEN 3
            WHEN beatmap_star_rating >= 6.5 THEN 4
            ELSE 5
        END AS star_rating_bucket_sort,
        pp,
        accuracy,
        beatmap_star_rating,
        count_miss
    FROM player_best_scores
    WHERE beatmap_star_rating IS NOT NULL
)
SELECT
    star_rating_bucket,
    star_rating_bucket_sort,
    COUNT(*) AS score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(MAX(pp), 2) AS max_pp,
    ROUND(MIN(pp), 2) AS min_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating,
    ROUND(AVG(count_miss), 2) AS avg_miss_count
FROM star_buckets
GROUP BY
    star_rating_bucket,
    star_rating_bucket_sort;