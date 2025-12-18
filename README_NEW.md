# test

## Fetch GenAI tweets and store in MongoDB ✅

This repository includes a script to fetch recent tweets matching the query `GenAI` and store them in the MongoDB collection `demo.tweet_collection`.

### Setup 🔧

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy and edit `.env.example`:

```bash
cp .env.example .env
# then fill TWITTER_BEARER_TOKEN and MONGODB_URI
```

### Run the fetch script ▶️

```bash
python scripts/fetch_tweets.py --query "GenAI" --max 100
```

### Verify inserted documents ✅

```bash
python scripts/verify_count.py
```

### Analyze user mention network 🔍

You can build a mention network from stored tweets (author -> mentioned user) and get summary stats and top users.

```bash
python scripts/analyze_network.py --top 10 --save outputs/network.graphml --image outputs/network.png
```

Notes:
- The script uses Twitter API v2 (Bearer token) and stores these fields: `id`, `text`, `author` (username), `created_at`, and `metrics`.
- Environment variables (preferred names): `TWITTER_API_KEY` (Bearer token) and `MONGODB_CONNECT` (MongoDB connection string). Older names `TWITTER_BEARER_TOKEN` and `MONGODB_URI` are also supported for backward compatibility.
- The tweet `id` is used as the document `_id` to prevent duplicates (upserts are used).
