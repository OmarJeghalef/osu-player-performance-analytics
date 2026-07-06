/*
osu! Player Performance Analytics
SQL analysis queries

These queries analyze the loaded PostgreSQL tables:
- player_profile_snapshots
- player_best_scores

Current scope:
The score table contains the player's current top 100 best scores from the osu! API.
Date-based analysis shows when the current top 100 plays were achieved, not the player's full historical score timeline.
*/


/*
1. Preview the current top 10 plays.

Purpose:
Confirm that score-level data loaded correctly and that key fields are readable.
*/
SELECT
    top_play_rank,
    username,
    pp,
    ROUND(accuracy * 100, 2) AS accuracy_percent,
    rank,
    COALESCE(NULLIF(mods, ''), 'NM') AS mods,
    beatmap_star_rating,
    beatmapset_artist,
    beatmapset_title,
    beatmap_difficulty_name,
    created_at
FROM player_best_scores
ORDER BY top_play_rank
LIMIT 10;


/*
2. Accuracy, difficulty, and pp relationship.

Purpose:
Compare how accuracy and star rating relate to pp.
This helps answer whether higher star rating plays can earn more pp even with lower accuracy.
*/
SELECT
    top_play_rank,
    pp,
    ROUND(accuracy * 100, 2) AS accuracy_percent,
    beatmap_star_rating,
    ROUND((pp / NULLIF(beatmap_star_rating, 0)), 2) AS pp_per_star,
    rank,
    COALESCE(NULLIF(mods, ''), 'NM') AS mods,
    beatmapset_artist,
    beatmapset_title,
    beatmap_difficulty_name
FROM player_best_scores
WHERE
    pp IS NOT NULL
    AND accuracy IS NOT NULL
    AND beatmap_star_rating IS NOT NULL
ORDER BY pp DESC;


/*
3. Correlation between pp, accuracy, and star rating.

Purpose:
Quantify relationships:
- pp vs accuracy
- pp vs star rating
- accuracy vs star rating

Interpretation:
Positive correlation means the two values tend to increase together.
Negative correlation means one tends to decrease as the other increases.
Values closer to 1 or -1 indicate a stronger relationship.
Values near 0 indicate a weaker linear relationship.
*/
SELECT
    ROUND(CORR(pp, accuracy)::numeric, 4) AS corr_pp_accuracy,
    ROUND(CORR(pp, beatmap_star_rating)::numeric, 4) AS corr_pp_star_rating,
    ROUND(CORR(accuracy, beatmap_star_rating)::numeric, 4) AS corr_accuracy_star_rating
FROM player_best_scores
WHERE
    pp IS NOT NULL
    AND accuracy IS NOT NULL
    AND beatmap_star_rating IS NOT NULL;


/*
4. Average pp by accuracy bucket.

Purpose:
Group top plays by accuracy range and compare average pp and star rating.
This helps show whether lower-accuracy plays are still high-value because of map difficulty.
*/
WITH accuracy_buckets AS (
    SELECT
        CASE
            WHEN accuracy >= 0.995 THEN '99.5%+'
            WHEN accuracy >= 0.990 THEN '99.0% - 99.49%'
            WHEN accuracy >= 0.980 THEN '98.0% - 98.99%'
            WHEN accuracy >= 0.970 THEN '97.0% - 97.99%'
            WHEN accuracy >= 0.960 THEN '96.0% - 96.99%'
            ELSE 'Below 96.0%'
        END AS accuracy_bucket,
        pp,
        accuracy,
        beatmap_star_rating
    FROM player_best_scores
    WHERE
        pp IS NOT NULL
        AND accuracy IS NOT NULL
        AND beatmap_star_rating IS NOT NULL
)
SELECT
    accuracy_bucket,
    COUNT(*) AS score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(MIN(pp), 2) AS min_pp,
    ROUND(MAX(pp), 2) AS max_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating
FROM accuracy_buckets
GROUP BY accuracy_bucket
ORDER BY
    CASE accuracy_bucket
        WHEN '99.5%+' THEN 1
        WHEN '99.0% - 99.49%' THEN 2
        WHEN '98.0% - 98.99%' THEN 3
        WHEN '97.0% - 97.99%' THEN 4
        WHEN '96.0% - 96.99%' THEN 5
        ELSE 6
    END;


/*
5. Average pp by star rating bucket.

Purpose:
Group top plays by beatmap difficulty and compare pp and accuracy.
This directly supports analysis of whether harder maps produce higher pp despite lower accuracy.
*/
WITH star_buckets AS (
    SELECT
        CASE
            WHEN beatmap_star_rating >= 8.0 THEN '8.0+ stars'
            WHEN beatmap_star_rating >= 7.5 THEN '7.5 - 7.99 stars'
            WHEN beatmap_star_rating >= 7.0 THEN '7.0 - 7.49 stars'
            WHEN beatmap_star_rating >= 6.5 THEN '6.5 - 6.99 stars'
            ELSE 'Below 6.5 stars'
        END AS star_rating_bucket,
        pp,
        accuracy,
        beatmap_star_rating
    FROM player_best_scores
    WHERE
        pp IS NOT NULL
        AND accuracy IS NOT NULL
        AND beatmap_star_rating IS NOT NULL
)
SELECT
    star_rating_bucket,
    COUNT(*) AS score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(MIN(pp), 2) AS min_pp,
    ROUND(MAX(pp), 2) AS max_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating
FROM star_buckets
GROUP BY star_rating_bucket
ORDER BY
    CASE star_rating_bucket
        WHEN '8.0+ stars' THEN 1
        WHEN '7.5 - 7.99 stars' THEN 2
        WHEN '7.0 - 7.49 stars' THEN 3
        WHEN '6.5 - 6.99 stars' THEN 4
        ELSE 5
    END;


/*
6. High difficulty versus high accuracy comparison.

Purpose:
Compare different score profiles:
- high star rating with lower accuracy
- lower star rating with very high accuracy

This helps investigate whether difficulty can outweigh accuracy for pp.
*/
WITH score_categories AS (
    SELECT
        CASE
            WHEN beatmap_star_rating >= 7.5 AND accuracy < 0.985
                THEN 'High difficulty, lower accuracy'
            WHEN beatmap_star_rating < 7.5 AND accuracy >= 0.990
                THEN 'Lower difficulty, high accuracy'
            WHEN beatmap_star_rating >= 7.5 AND accuracy >= 0.985
                THEN 'High difficulty, high accuracy'
            ELSE 'Other'
        END AS score_profile,
        pp,
        accuracy,
        beatmap_star_rating
    FROM player_best_scores
    WHERE
        pp IS NOT NULL
        AND accuracy IS NOT NULL
        AND beatmap_star_rating IS NOT NULL
)
SELECT
    score_profile,
    COUNT(*) AS score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(MAX(pp), 2) AS max_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating
FROM score_categories
GROUP BY score_profile
ORDER BY avg_pp DESC;


/*
7. Current top 100 plays by year achieved.

Purpose:
Show when the player's current top plays were set.
This gives a high-level view of improvement timing.
*/
SELECT
    EXTRACT(YEAR FROM created_at)::int AS score_year,
    COUNT(*) AS top_score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(MAX(pp), 2) AS max_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating
FROM player_best_scores
WHERE created_at IS NOT NULL
GROUP BY EXTRACT(YEAR FROM created_at)
ORDER BY score_year;


/*
8. Current top 100 plays by month achieved.

Purpose:
Show which months produced the most current top 100 plays.
This is useful for analyzing bursts of improvement.
*/
SELECT
    DATE_TRUNC('month', created_at)::date AS score_month,
    COUNT(*) AS top_score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(MAX(pp), 2) AS max_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating
FROM player_best_scores
WHERE created_at IS NOT NULL
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY score_month;


/*
9. Running count of current top plays over time.

Purpose:
Use a window function to show the accumulation of the player's current top 100 plays by score date.
This helps visualize consistency and improvement periods.
*/
WITH monthly_counts AS (
    SELECT
        DATE_TRUNC('month', created_at)::date AS score_month,
        COUNT(*) AS monthly_top_scores
    FROM player_best_scores
    WHERE created_at IS NOT NULL
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT
    score_month,
    monthly_top_scores,
    SUM(monthly_top_scores) OVER (
        ORDER BY score_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_current_top_scores
FROM monthly_counts
ORDER BY score_month;


/*
10. Month-over-month change in average pp.

Purpose:
Use LAG() to compare each month against the previous month.
This demonstrates a window function and helps identify improvement periods.
*/
WITH monthly_pp AS (
    SELECT
        DATE_TRUNC('month', created_at)::date AS score_month,
        COUNT(*) AS score_count,
        AVG(pp) AS avg_pp,
        MAX(pp) AS max_pp
    FROM player_best_scores
    WHERE created_at IS NOT NULL
    GROUP BY DATE_TRUNC('month', created_at)
),
monthly_changes AS (
    SELECT
        score_month,
        score_count,
        avg_pp,
        max_pp,
        LAG(avg_pp) OVER (ORDER BY score_month) AS previous_month_avg_pp,
        LAG(max_pp) OVER (ORDER BY score_month) AS previous_month_max_pp
    FROM monthly_pp
)
SELECT
    score_month,
    score_count,
    ROUND(avg_pp, 2) AS avg_pp,
    ROUND(previous_month_avg_pp, 2) AS previous_month_avg_pp,
    ROUND((avg_pp - previous_month_avg_pp), 2) AS avg_pp_change,
    ROUND(max_pp, 2) AS max_pp,
    ROUND(previous_month_max_pp, 2) AS previous_month_max_pp,
    ROUND((max_pp - previous_month_max_pp), 2) AS max_pp_change
FROM monthly_changes
ORDER BY score_month;


/*
11. Mod combination performance summary.

Purpose:
Analyze which mod combinations appear most often and how they compare by pp, accuracy, and star rating.
*/
WITH mod_summary AS (
    SELECT
        COALESCE(NULLIF(mods, ''), 'NM') AS mod_combination,
        COUNT(*) AS score_count,
        AVG(pp) AS avg_pp,
        MAX(pp) AS max_pp,
        AVG(accuracy) * 100 AS avg_accuracy_percent,
        AVG(beatmap_star_rating) AS avg_star_rating
    FROM player_best_scores
    GROUP BY COALESCE(NULLIF(mods, ''), 'NM')
)
SELECT
    mod_combination,
    score_count,
    ROUND(avg_pp, 2) AS avg_pp,
    ROUND(max_pp, 2) AS max_pp,
    ROUND(avg_accuracy_percent, 2) AS avg_accuracy_percent,
    ROUND(avg_star_rating, 3) AS avg_star_rating
FROM mod_summary
ORDER BY score_count DESC, avg_pp DESC;


/*
12. Best score per mod combination.

Purpose:
Use ROW_NUMBER() to find the highest-pp score for each mod combination.
*/
WITH ranked_mod_scores AS (
    SELECT
        COALESCE(NULLIF(mods, ''), 'NM') AS mod_combination,
        top_play_rank,
        pp,
        accuracy,
        rank,
        beatmap_star_rating,
        beatmapset_artist,
        beatmapset_title,
        beatmap_difficulty_name,
        ROW_NUMBER() OVER (
            PARTITION BY COALESCE(NULLIF(mods, ''), 'NM')
            ORDER BY pp DESC
        ) AS mod_pp_rank
    FROM player_best_scores
)
SELECT
    mod_combination,
    top_play_rank,
    pp,
    ROUND(accuracy * 100, 2) AS accuracy_percent,
    rank,
    beatmap_star_rating,
    beatmapset_artist,
    beatmapset_title,
    beatmap_difficulty_name
FROM ranked_mod_scores
WHERE mod_pp_rank = 1
ORDER BY pp DESC;


/*
13. Rank grade distribution.

Purpose:
Summarize how many current top 100 plays have each score grade.
*/
SELECT
    rank,
    COUNT(*) AS score_count,
    ROUND(AVG(pp), 2) AS avg_pp,
    ROUND(AVG(accuracy) * 100, 2) AS avg_accuracy_percent,
    ROUND(AVG(beatmap_star_rating), 3) AS avg_star_rating
FROM player_best_scores
GROUP BY rank
ORDER BY score_count DESC, avg_pp DESC;


/*
14. Join player profile snapshot to best scores.

Purpose:
Demonstrate joining player-level and score-level data.
This query connects profile rank/pp to individual top plays.
*/
SELECT
    p.username,
    p.global_rank,
    p.country_rank,
    p.pp AS profile_pp,
    p.hit_accuracy AS profile_accuracy_percent,
    p.play_count,
    s.top_play_rank,
    s.pp AS score_pp,
    ROUND(s.accuracy * 100, 2) AS score_accuracy_percent,
    s.rank,
    COALESCE(NULLIF(s.mods, ''), 'NM') AS mods,
    s.beatmap_star_rating,
    s.beatmapset_artist,
    s.beatmapset_title,
    s.beatmap_difficulty_name,
    s.created_at
FROM player_profile_snapshots p
JOIN player_best_scores s
    ON p.user_id = s.user_id
ORDER BY s.top_play_rank
LIMIT 20;


/*
15. Top plays with the largest pp per star rating.

Purpose:
Identify unusually efficient plays where pp is high relative to star rating.
*/
SELECT
    top_play_rank,
    pp,
    beatmap_star_rating,
    ROUND((pp / NULLIF(beatmap_star_rating, 0)), 2) AS pp_per_star,
    ROUND(accuracy * 100, 2) AS accuracy_percent,
    rank,
    COALESCE(NULLIF(mods, ''), 'NM') AS mods,
    beatmapset_artist,
    beatmapset_title,
    beatmap_difficulty_name
FROM player_best_scores
WHERE
    pp IS NOT NULL
    AND beatmap_star_rating IS NOT NULL
ORDER BY pp_per_star DESC
LIMIT 15;


/*
16. Dashboard-friendly score view query.

Purpose:
This SELECT can later be converted into a SQL view for Power BI.
*/
SELECT
    score_id,
    username,
    top_play_rank,
    pp,
    accuracy,
    ROUND(accuracy * 100, 2) AS accuracy_percent,
    rank,
    COALESCE(NULLIF(mods, ''), 'NM') AS mods,
    beatmap_star_rating,
    beatmap_bpm,
    beatmap_cs,
    beatmap_ar,
    beatmap_od,
    beatmap_hp,
    beatmap_total_length,
    beatmap_hit_length,
    beatmapset_artist,
    beatmapset_title,
    beatmapset_creator,
    beatmap_difficulty_name,
    created_at,
    DATE_TRUNC('month', created_at)::date AS score_month,
    EXTRACT(YEAR FROM created_at)::int AS score_year
FROM player_best_scores
ORDER BY top_play_rank;
