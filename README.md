# osu! Player Performance Analytics

An end-to-end data analytics project that collects and analyzes osu! player performance data using Python, PostgreSQL, SQL, and Power BI.

## Project Goal

The goal of this project is to build a repeatable analytics pipeline that:

1. Extracts player, score, and beatmap data from the osu! API.
2. Cleans and transforms the data with Python and pandas.
3. Loads validated data into PostgreSQL.
4. Analyzes performance using SQL.
5. Presents findings through an interactive Power BI dashboard.

## Questions

- How does accuracy relate to pp in a player's top scores?
- How does beatmap star rating relate to pp?
- Do higher-star plays still produce more pp when accuracy is lower?
- Which mod combinations appear most often in the player's top scores?
- When were the player's current top scores achieved?
- What difficulty ranges appear most represented in the player's best scores?

## Technology Stack

Currently implemented:

- Python
- pandas
- osu! API v2
- PostgreSQL
- SQL
- Git and GitHub

Planned:

- Power BI
- Power Query
- DAX

## Project Structure

```text
data/
├── raw/
└── processed/

src/
├── config.py
├── extract.py
├── transform.py
├── validate.py
└── load.py

sql/
├── schema.sql
└── analysis_queries.sql

dashboard/
└── screenshots/
```

## Current Pipeline Status

The project currently implements an end-to-end local analytics pipeline:

1. Extracts public osu! player data from the osu! API v2.
2. Saves raw API responses as timestamped JSON files with metadata.
3. Transforms nested JSON into clean player profile and best-score CSV datasets using pandas.
4. Validates processed datasets for required files, columns, non-null fields, unique score IDs, numeric ranges, and parseable timestamps.
5. Loads validated datasets into PostgreSQL tables.
6. Provides SQL analysis queries for player performance trends, including accuracy, pp, beatmap difficulty, mod combinations, and score timing.

## SQL Analysis

The `sql/analysis_queries.sql` file contains exploratory SQL queries for analyzing the player's current top 100 best scores.

Current analysis areas include:

- Accuracy versus pp
- Beatmap star rating versus pp
- Accuracy versus beatmap difficulty
- Average pp by accuracy bucket
- Average pp by star rating bucket
- High-difficulty lower-accuracy plays versus lower-difficulty high-accuracy plays
- Current top plays by year and month achieved
- Cumulative current top plays over time
- Mod combination performance
- Rank grade distribution
- Joins between profile snapshots and best scores

Note: Date-based score analysis currently reflects when the player's current top 100 best scores were achieved, not the player's complete historical score timeline.
