DROP TABLE IF EXISTS player_best_scores;
DROP TABLE IF EXISTS player_profile_snapshots;

-- Create the player_profile_snapshots table to store snapshots of player profiles.
CREATE TABLE player_profile_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,

    extracted_at_utc TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    mode TEXT NOT NULL,

    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    country_code TEXT,
    country_name TEXT,

    global_rank INTEGER,
    country_rank INTEGER,
    pp NUMERIC(10, 3),
    hit_accuracy NUMERIC(8, 5),
    play_count INTEGER,
    play_time INTEGER,
    total_score BIGINT,
    ranked_score BIGINT,
    maximum_combo INTEGER,
    replays_watched INTEGER,

    level_current INTEGER,
    level_progress INTEGER,

    loaded_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_profile_pp_nonnegative CHECK (pp IS NULL OR pp >= 0),
    CONSTRAINT chk_profile_hit_accuracy_range CHECK (
        hit_accuracy IS NULL OR hit_accuracy BETWEEN 0 AND 100
    ),
    CONSTRAINT chk_profile_play_count_nonnegative CHECK (
        play_count IS NULL OR play_count >= 0
    )
);

-- Create the player_best_scores table to store the best scores of players.
CREATE TABLE player_best_scores (
    score_id BIGINT PRIMARY KEY,

    extracted_at_utc TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    mode TEXT NOT NULL,
    username TEXT NOT NULL,

    top_play_rank INTEGER NOT NULL,
    user_id BIGINT NOT NULL,
    beatmap_id BIGINT NOT NULL,
    beatmapset_id BIGINT,

    score BIGINT,
    pp NUMERIC(10, 3),
    accuracy NUMERIC(8, 7),
    rank TEXT,
    max_combo INTEGER,
    passed BOOLEAN,
    perfect BOOLEAN,
    created_at TIMESTAMPTZ,

    mods TEXT,
    ruleset_id INTEGER,

    count_300 INTEGER,
    count_100 INTEGER,
    count_50 INTEGER,
    count_miss INTEGER,

    weight_percentage NUMERIC(8, 4),
    weight_pp NUMERIC(10, 3),

    beatmap_difficulty_name TEXT,
    beatmap_total_length INTEGER,
    beatmap_hit_length INTEGER,
    beatmap_bpm NUMERIC(8, 3),
    beatmap_cs NUMERIC(5, 2),
    beatmap_ar NUMERIC(5, 2),
    beatmap_od NUMERIC(5, 2),
    beatmap_hp NUMERIC(5, 2),
    beatmap_star_rating NUMERIC(8, 4),
    beatmap_status TEXT,

    beatmapset_artist TEXT,
    beatmapset_title TEXT,
    beatmapset_creator TEXT,
    beatmapset_ranked_date TIMESTAMPTZ,

    loaded_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_best_scores_top_play_rank_range CHECK (
        top_play_rank BETWEEN 1 AND 100
    ),
    CONSTRAINT chk_best_scores_pp_nonnegative CHECK (
        pp IS NULL OR pp >= 0
    ),
    CONSTRAINT chk_best_scores_accuracy_range CHECK (
        accuracy IS NULL OR accuracy BETWEEN 0 AND 1
    ),
    CONSTRAINT chk_best_scores_score_nonnegative CHECK (
        score IS NULL OR score >= 0
    ),
    CONSTRAINT chk_best_scores_combo_nonnegative CHECK (
        max_combo IS NULL OR max_combo >= 0
    ),
    CONSTRAINT chk_best_scores_star_rating_nonnegative CHECK (
        beatmap_star_rating IS NULL OR beatmap_star_rating >= 0
    )
);

-- Create indexes to optimize queries on the player_profile_snapshots and player_best_scores tables.
CREATE INDEX idx_profile_snapshots_user_time
    ON player_profile_snapshots (user_id, extracted_at_utc DESC);

CREATE INDEX idx_best_scores_user_rank
    ON player_best_scores (user_id, top_play_rank);

CREATE INDEX idx_best_scores_created_at
    ON player_best_scores (created_at DESC);

CREATE INDEX idx_best_scores_pp
    ON player_best_scores (pp DESC);

CREATE INDEX idx_best_scores_beatmap
    ON player_best_scores (beatmap_id);
