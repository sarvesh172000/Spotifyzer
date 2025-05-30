# Spotifyzer: Data Warehouse Project

![Spotifyzer Banner](https://img.shields.io/badge/Spotifyzer-Data%20Warehouse-green)

A comprehensive data‑warehousing and analytics solution that transforms raw Spotify streaming data into actionable insights for artists, labels and marketers.

---

## Table of Contents

* [Introduction](#introduction)
* [Problem Statement](#problem-statement)
* [Features](#features)
* [Architecture](#architecture)
* [ETL Process](#etl-process)

  * [Extraction (E)](#extraction-e)
  * [Transformation (T)](#transformation-t)
  * [Loading (L)](#loading-l)
* [Data Model](#data-model)
* [Dashboard Overview](#dashboard-overview)
* [Key Insights](#key-insights)
* [Technical Stack](#technical-stack)
* [Setup and Installation](#setup-and-installation)

  * [Prerequisites](#prerequisites)
  * [Spotify API Credentials](#spotify-api-credentials)
  * [Environment Variables](#environment-variables)
  * [Running the ETL Script](#running-the-etl-script)
* [Future Enhancements](#future-enhancements)
* [Contributing](#contributing)
* [Team](#team)
* [License](#license)
* [Acknowledgements](#acknowledgements)

---

## Introduction

Spotifyzer is a data‑warehousing project designed to analyze Spotify data, uncover patterns in music trends, listener behavior, and the impact of audio features. It empowers data‑driven decisions for artists, labels, and marketers by surfacing insights on user engagement with albums and tracks.

## Problem Statement

Despite the vast user‑interaction data generated on platforms like Spotify, the music industry lacks an integrated, data‑driven tool to explore how audio features, user behavior, and track popularity intersect. **Spotifyzer** bridges this gap by converting raw streaming data into actionable insights through a comprehensive data‑warehousing and analytics stack.

## Features

* **Comprehensive Data Extraction** – Fetches track metadata, user‑interaction data (popularity, play count, device type), and audio features.
* **Robust ETL Pipeline** – Python, AWS Glue, and Snowflake power scalable data processing.
* **Data Cleaning & Transformation** – Handles nulls, standardizes formats, filters duplicates, converts data types, and ensures consistency.
* **Feature Engineering** – Adds mood‑based categories and enriches data with external sources.
* **Cloud Data Warehousing** – Leverages Snowflake for lightning‑fast querying and aggregation.
* **Interactive Dashboards** – Power BI visualizes key metrics such as most‑played tracks, listening patterns, and artist popularity.
* **Detailed Analytics** – Surfaces insights into album, artist, and track performance, listening patterns, and engagement metrics.

## Architecture

```text
+--------------+       +-------------+       +--------------------+       +-------------+
|  Spotify Web |  -->  |   Amazon    |  -->  |  AWS Glue (Python) |  -->  |  Snowflake  |
|     API      |       |     S3      |       |  Transformations   |       |  Warehouse  |
+--------------+       +-------------+       +--------------------+       +-------------+
                                                          |
                                                          v
                                               +--------------------+
                                               |    Power BI        |
                                               |  Dashboards &      |
                                               |  Analytics         |
                                               +--------------------+
```

* **Extraction** – Data fetched from the Spotify Web API.
* **Storage (Staging)** – Raw JSON files stored temporarily in Amazon S3.
* **Transformation** – AWS Glue jobs (Python/Pandas) perform cleaning, enrichment, and normalization.
* **Loading** – Curated data loaded into Snowflake with partitioning for optimized querying.
* **Visualization** – Power BI connects to Snowflake for interactive dashboards.

## ETL Process

### Extraction (E)

* **Source**: Spotify Web API using the `spotipy` Python library.
* **Data Retrieved**:

  * Track metadata: `name`, `artist`, `album`, `release_date`
  * User interaction: `popularity`, `play_count`, `device_type`
  * Saved tracks, playlists, recently‑played tracks.
* **Frequency**: Daily/weekly ingestion.

```powershell
# Install Spotipy
pip install spotipy

# Set credentials (PowerShell)
$env:SPOTIPY_CLIENT_ID     = 'YOUR_CLIENT_ID'
$env:SPOTIPY_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
$env:SPOTIPY_REDIRECT_URI  = 'http://127.0.0.1:8000/callback'

# Run the extraction script
python spotify_etl_extract.py
```

Sample output:

```text
Authentication successful.
Fetching saved tracks... ✅ 295 tracks
Fetching user playlists... ✅ 9 playlists
Fetching audio features... ✅
Fetching recently played... ✅ 50 tracks
--- Extraction Complete ---
Data saved to ./spotify_data/
```

### Transformation (T)

* **Environment**: AWS Glue + Python (Pandas).
* **Steps**:

  1. **Data Cleaning** – Remove null/blank records, standardize column names, drop duplicates, convert dates, cast numeric types, audit consistency.
  2. **Feature Engineering** – Categorize tracks by mood (sentiment & audio features).
  3. **Data Enrichment** – Join with external sources (genre, mood tags).
  4. **Normalization** – Scale/standardize numerical features.

### Loading (L)

* **Destination**: **Snowflake** data warehouse.
* **Partitioning**: By year, genre, sentiment score.
* **Schema**:

  * **Fact**: `fact_streaming_events` (plays, timestamps, `track_id`).
  * **Dimensions**: `dim_track`, `dim_artist`, `dim_audio_features`, `dim_user`, `dim_date`.
* **Automation & Logging**: AWS Glue Jobs & Crawlers orchestrate and log via CloudWatch.

```sql
CREATE OR REPLACE TABLE dim_track (
    track_id     STRING PRIMARY KEY,
    track_name   STRING,
    artist_name  STRING,
    album_name   STRING,
    genre        STRING,
    release_date DATE
);

CREATE OR REPLACE TABLE dim_user (
    user_id  STRING PRIMARY KEY,
    platform STRING
);
```

## Data Model

The warehouse follows a **star schema**:

```
              +----------------+
              |  dim_artist    |
              +----------------+
                      ^
                      |
+------------+   +------------+   +------------------+
| dim_track  |<--| fact_stream |-->| dim_audio_feat   |
+------------+   +------------+   +------------------+
                      |
                      v
                +-------------+
                |  dim_user   |
                +-------------+
```

This layout enables lightning‑fast analytical queries and seamless dashboard integrations.

## Dashboard Overview

Power BI dashboards provide a holistic view of engagement and trends via three panels—**Albums, Artists, Tracks**—and advanced slicers.

* **Platform Slicer** – Filter behavior by device (Android, Mac, Windows).
* **Visuals** – Listening trends, top items, weekday/weekend engagement.
* **YoY Comparison** – Examine year‑over‑year deltas.
* **Heatmap** – Peak listening hours (6 PM – 2 AM, esp. weekends).
* **Scatterplot** – Track frequency vs. average listening time (most tracks: 10–25 plays, 2–4 min listen).
* **Behavior Filters** – Shuffle & Skip flags for segmentation.
* **Details Grid** – Album | Artist | Track | Listening Time with drill‑through & CSV export.

## Key Insights

| Metric                | Insight                                                 |
| --------------------- | ------------------------------------------------------- |
| **Weekend Share**     | \~59 % of listening occurs on weekends                  |
| **Peak Hours**        | 18:00–02:00 (highest engagement)                        |
| **Top Artist**        | The Beatles remain most‑played                          |
| **Track Duration**    | Avg. 2–4 min; 10–25 repeats                             |
| **YoY Change (2024)** | Albums ↓ 21.82 % · Artists ↓ 26.39 % · Tracks ↓ 11.49 % |

## Technical Stack

| Layer               | Technology                   |
| ------------------- | ---------------------------- |
| **Language**        | Python                       |
| **Libraries**       | Spotipy · Pandas · requests  |
| **Cloud**           | AWS – S3 · Glue · CloudWatch |
| **Warehouse**       | Snowflake                    |
| **Visualization**   | Power BI                     |
| **Version Control** | Git                          |

## Setup and Installation

### Prerequisites

* Python **3.x** & `pip`
* AWS account with S3, Glue, CloudWatch permissions
* Snowflake account (roles & warehouses)
* Power BI Desktop

### Spotify API Credentials

1. Sign in at **[Spotify for Developers](https://developer.spotify.com/dashboard)**.
2. Create an *App* → copy the **Client ID** & **Client Secret**.
3. Add redirect URI: `http://127.0.0.1:8000/callback`.

### Environment Variables

```powershell
$env:SPOTIPY_CLIENT_ID     = 'your_client_id_here'
$env:SPOTIPY_CLIENT_SECRET = 'your_client_secret_here'
$env:SPOTIPY_REDIRECT_URI  = 'http://127.0.0.1:8000/callback'
```

### Running the ETL Script

```bash
# 1. Install dependencies
pip install spotipy pandas

# 2. Clone repository
git clone https://github.com/sarvesh172000/Spotifyzer.git
cd Spotifyzer

# 3. Start extraction
python spotify_etl_extract.py
```

**Next Steps**

* Configure **AWS Glue** Jobs and Crawlers to pick up data from S3, transform, and load into Snowflake.
* Connect **Power BI** to Snowflake to explore dashboards.

## Future Enhancements

* Real‑time streaming ingestion using **Kafka** or **Kinesis**.
* Machine‑learning models for hit‑song prediction.
* Multi‑platform analytics (Apple Music, YouTube Music, etc.).
* Web interface for interactive exploration.

## Contributing

We welcome contributions! Fork this repo, create a branch, commit your changes, and open a **PR**.

## Team

* **Jenil Sanjaybhai Savalia** (018224960)
* **Sarvesh Waghmare** (018319262)
* **Shibin Biji Thomas** (018318261)
* **Vrushabh Pravinbhai Bodarya** (018284162)

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

## Acknowledgements

* **Spotify for Developers**
* **AWS Documentation**
* **Snowflake Documentation**
