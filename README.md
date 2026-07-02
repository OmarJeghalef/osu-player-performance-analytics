# osu! Player Performance Analytics

An end-to-end data analytics project that collects and analyzes osu! player performance data using Python, PostgreSQL, SQL, and Power BI.

## Project Goal

The goal of this project is to build a repeatable analytics pipeline that:

1. Extracts player, score, and beatmap data from the osu! API.
2. Cleans and transforms the data with Python and pandas.
3. Loads normalized data into PostgreSQL.
4. Analyzes performance using SQL.
5. Presents findings through an interactive Power BI dashboard.

## Questions

- How has player performance changed over time?
- Which star-rating range produces the highest performance?
- Which mods produce the highest accuracy?
- How does BPM affect accuracy and miss count?
- What is the player's strongest difficulty range?
- Which maps appear to offer the best improvement opportunities?

## Planned Technology Stack

- Python
- pandas
- PostgreSQL
- SQL
- Power BI
- Power Query
- DAX
- Git and GitHub

## Planned Project Structure

```text
data/
├── raw/
└── processed/

src/
├── config.py
├── extract.py
├── transform.py
└── load.py

sql/
├── create_tables.sql
└── analysis_queries.sql

dashboard/
screenshots/