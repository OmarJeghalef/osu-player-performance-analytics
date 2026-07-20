# osu! Player Performance Analytics

An end-to-end data analytics portfolio project that collects, processes, validates, stores, analyzes, and visualizes osu! player performance data using Python, pandas, PostgreSQL, SQL, and Power BI.

The current version analyzes the osu! standard player `mrekk` using public data from the osu! API v2.

## Project Goal

The goal of this project is to build a repeatable analytics pipeline that:

1. Extracts player profile and best-score data from the osu! API.
2. Saves raw API responses as timestamped JSON files.
3. Cleans and transforms nested API data with Python and pandas.
4. Validates processed datasets before database loading.
5. Loads validated data into PostgreSQL.
6. Analyzes player performance using SQL.
7. Prepares dashboard-ready SQL views for Power BI.
8. Builds an interactive Power BI dashboard.

## Analysis Questions

This project is focused on answering questions such as:

- How does accuracy relate to pp in a player's top scores?
- How does beatmap star rating relate to pp?
- Do higher-star plays still produce more pp when accuracy is lower?
- Which mod combinations appear most often in the player's top scores?
- Which mod combinations are associated with higher average pp or accuracy?
- When were the player's current top scores achieved?
- What difficulty ranges appear most represented in the player's best scores?

Note: Date-based score analysis currently reflects when the player's current top 100 best scores were achieved, not the player's complete historical score timeline.

## Technology Stack

Implemented:

- Python
- pandas
- requests
- python-dotenv
- osu! API v2
- PostgreSQL
- SQL
- SQLAlchemy
- psycopg
- Power BI Desktop
- DAX measures
- Git and GitHub

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
├── analysis_queries.sql
└── views.sql

dashboard/
├── osu_performance_dashboard.pbix
└── screenshots/
    ├── dashboard_overview.png
    └── dashboard_overview.pdf

README.md
requirements.txt
.env.example
.gitignore
```

## Dashboard Preview

![Dashboard Overview](dashboard/screenshots/dashboard_overview.png)

[View dashboard PDF](dashboard/screenshots/dashboard_overview.pdf)

## Key Findings

Based on the current top 100 best scores for `mrekk`:

- Higher star-rating plays generally produce higher average pp, with the 8.0+ star bucket showing the highest average pp.
- Accuracy is still high across most top plays, but the scatter plot shows more lower-accuracy outliers at higher star ratings.
- `HD,DT` is the most common mod combination in the current top 100 sample.
- Several current top plays were achieved in a concentrated recent period, especially around the largest monthly spike shown in the dashboard.
- Date-based analysis reflects when the current top 100 plays were achieved, not the player's full score history.

## Current Pipeline Status

The project implements a completed local analytics pipeline:

```text
osu! API
→ raw JSON
→ processed CSV
→ validation
→ PostgreSQL tables
→ SQL analysis queries
→ SQL reporting views
→ Power BI dashboard
```

Pipeline stages:

1. Extracts public osu! player data from the osu! API v2.
2. Saves raw API responses as timestamped JSON files with metadata.
3. Transforms nested JSON into clean player profile and best-score CSV datasets using pandas.
4. Validates processed datasets before database loading.
5. Loads validated datasets into PostgreSQL tables.
6. Provides SQL analysis queries for player performance trends.
7. Creates dashboard-ready PostgreSQL views for Power BI reporting.
8. Connects Power BI Desktop to PostgreSQL and loads reporting views.
9. Builds a Power BI overview dashboard with KPI cards and visuals for accuracy, difficulty, pp, mod combinations, and score timing.

## ETL Pipeline

### Extract

The extraction script authenticates with the osu! API v2 using OAuth credentials stored in a local `.env` file.

`src/extract.py` extracts:

- Player profile data
- Player best-score data

Raw responses are saved as timestamped JSON files in:

```text
data/raw/
```

Generated raw JSON files are ignored by Git.

### Transform

`src/transform.py` reads the latest raw JSON files, flattens nested API responses, and creates processed CSV datasets.

Processed outputs include:

```text
data/processed/player_profile_snapshot.csv
data/processed/player_best_scores.csv
```

The best-score dataset includes score, player, beatmap, beatmapset, mod, difficulty, hit-count, pp, accuracy, and score timing fields.

Generated processed CSV files are ignored by Git.

### Validate

`src/validate.py` checks processed datasets before database loading.

Validation checks include:

- Required file existence
- Required column presence
- Non-null checks for critical fields
- Unique score IDs
- Numeric range checks
- Datetime parsing checks

Validation helped identify and fix field-mapping issues in the nested osu! API response.

### Load

`src/load.py` loads validated processed CSV files into PostgreSQL using SQLAlchemy and psycopg.

The load step converts CSV timestamp fields back into datetime values before insertion so they match PostgreSQL `TIMESTAMPTZ` columns.

## PostgreSQL Database

The database is named:

```text
osu_analytics
```

The schema is defined in:

```text
sql/schema.sql
```

Current tables:

- `player_profile_snapshots`
- `player_best_scores`

The schema includes:

- Primary keys
- SQL data types
- Check constraints
- Indexes

The current design keeps the first database version scoped and explainable. It uses structured relational tables while keeping beatmap and beatmapset fields inside the best-scores table for dashboard simplicity.

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

The SQL analysis file demonstrates:

- Joins
- CTEs
- Aggregations
- Date functions
- Window functions
- Correlation calculations

## SQL Reporting Views

The `sql/views.sql` file creates dashboard-ready PostgreSQL views for Power BI.

Current views include:

- `vw_best_scores_dashboard`: score-level view with cleaned fields such as accuracy percentage, cleaned mods, pp per star, beatmap name, score month, and score year.
- `vw_profile_snapshot_latest`: latest player profile snapshot for dashboard card visuals.
- `vw_monthly_score_summary`: monthly summary of the player's current top 100 plays.
- `vw_mod_summary`: performance summary by mod combination.
- `vw_star_rating_summary`: performance summary by beatmap star rating bucket.

These views provide a reporting layer between the PostgreSQL tables and Power BI so dashboard logic can stay consistent and reusable.

## Power BI Dashboard

The Power BI dashboard is connected to PostgreSQL reporting views and provides an overview of `mrekk`'s current top 100 osu! standard best scores.

Current dashboard visuals include:

- KPI cards for global rank, country rank, profile pp, profile accuracy, and play count.
- Scatter plot showing accuracy by beatmap star rating and mod combination.
- Bar chart showing average pp by difficulty range.
- Column chart showing when the current top plays were achieved by month.
- Bar chart showing the most common mod combinations in the current top 100 plays.

The dashboard uses PostgreSQL views as the reporting layer so Power BI can load cleaned fields such as accuracy percentage, score month, mod combination, pp per star, and star rating buckets.

## Environment Variables

The project uses a local `.env` file for private configuration.

Required variables are documented in:

```text
.env.example
```

Expected variables:

```text
OSU_CLIENT_ID=
OSU_CLIENT_SECRET=
OSU_USERNAME=
OSU_MODE=osu
DATABASE_URL=
```

The actual `.env` file is ignored by Git and should not be committed.

## Running the Pipeline

After setting up the virtual environment, installing dependencies, configuring `.env`, and creating the PostgreSQL database, run:

```bash
python src/extract.py
python src/transform.py
python src/validate.py
psql osu_analytics -f sql/schema.sql
python src/load.py
psql osu_analytics -f sql/views.sql
```

On Windows, if using the `postgres` user, the PostgreSQL commands may look like:

```powershell
psql -U postgres -d osu_analytics -f sql\schema.sql
psql -U postgres -d osu_analytics -f sql\views.sql
```
