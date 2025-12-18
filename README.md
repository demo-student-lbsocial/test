# test

A small project that fetches tweets, builds a mention network, computes network metrics, and provides visualizations.

## Overview

This repository contains scripts to fetch social data, store it (MongoDB), analyze it as a network, and visualize results using a Jupyter notebook. For a concise human-friendly overview, open `index.html` in the repository root.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables (recommended via `.env`):

- `TWITTER_BEARER_TOKEN` (Twitter API v2)
- `MONGODB_CONNECT` (MongoDB connection string)

Older environment variable names are also supported: `TWITTER_BEARER_TOKEN` and `MONGODB_URI`.

## Usage

- Fetch tweets (example):

```bash
python scripts/fetch_tweets.py --query "GenAI" --max 100
```

- Verify inserted documents:

```bash
python scripts/verify_count.py
```

- Build and analyze the mention network (example):

```bash
python scripts/analyze_network.py --top 10 --save outputs/network.graphml --image outputs/network.png
```

## Files of interest

- `scripts/fetch_tweets.py` — data collection
- `scripts/analyze_network.py` — network building and metrics
- `scripts/verify_count.py` — verification utilities
- `notebooks/network_visualization.ipynb` — notebook for visualization
- `outputs/network.graphml` — exported graph file
- `index.html` — concise project summary and links

## Reproducing the workflow

1. Install dependencies
2. Set environment variables
3. Run the fetch script
4. Run the analysis script
5. Open the notebook to reproduce the visualizations

---

_Last updated: 2025-12-18_