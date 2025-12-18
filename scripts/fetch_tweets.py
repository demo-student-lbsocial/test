#!/usr/bin/env python3
"""Fetch tweets matching a query and store them in MongoDB demo.tweet_collection.

Usage:
  pip install -r requirements.txt
  cp .env.example .env  # fill in values
  python scripts/fetch_tweets.py --query "GenAI" --max 100
"""

import os
import sys
import time
import argparse
import logging
from typing import Dict, List

import requests
import pymongo
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Accept both the new and older env var names for compatibility
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN") or os.getenv("TWITTER_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGODB_CONNECT")

if not TWITTER_BEARER:
    logger.error("Twitter bearer token not set. Set TWITTER_API_KEY (preferred) or TWITTER_BEARER_TOKEN in env or .env file.")
    sys.exit(1)

if not MONGODB_URI:
    logger.error("MongoDB connection string not set. Set MONGODB_CONNECT (preferred) or MONGODB_URI in env or .env file.")
    sys.exit(1)

TWITTER_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
HEADERS = {"Authorization": f"Bearer {TWITTER_BEARER}"}


def fetch_tweets(query: str, max_results: int = 100) -> List[Dict]:
    """Fetch up to max_results tweets for query (uses a single request with max_results up to 100).
    Returns list of tweets with merged author username and requested fields.
    """
    params = {
        "query": f"{query} -is:retweet lang:en",
        "max_results": str(min(100, max_results)),
        "tweet.fields": "id,text,created_at,public_metrics,author_id",
        "expansions": "author_id",
        "user.fields": "id,username,name",
    }

    backoff = 1
    while True:
        resp = requests.get(TWITTER_SEARCH_URL, headers=HEADERS, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            results = []
            for t in tweets:
                author = users.get(t.get("author_id"), {})
                results.append({
                    "id": t.get("id"),
                    "text": t.get("text"),
                    "author": author.get("username"),
                    "created_at": t.get("created_at"),
                    "metrics": t.get("public_metrics", {}),
                })
            return results

        elif resp.status_code == 429:
            logger.warning("Rate limited by Twitter API. Backing off for %s seconds", backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue
        else:
            logger.error("Twitter API error %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()


def store_tweets(mongo_uri: str, docs: List[Dict]) -> Dict[str, int]:
    client = pymongo.MongoClient(mongo_uri)
    db = client["demo"]
    coll = db["tweet_collection"]

    inserted = 0
    updated = 0
    for d in docs:
        # Use tweet id as _id to deduplicate
        doc = {
            "_id": d["id"],
            "text": d["text"],
            "author": d.get("author"),
            "created_at": d.get("created_at"),
            "metrics": d.get("metrics", {}),
        }
        res = coll.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        if res.matched_count == 0 and res.upserted_id:
            inserted += 1
        else:
            updated += 1

    return {"inserted": inserted, "updated": updated}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="GenAI", help="Search query (default: GenAI)")
    parser.add_argument("--max", type=int, default=100, help="Max tweets to fetch (max 100 per request)")
    args = parser.parse_args()

    logger.info("Fetching tweets for query: %s", args.query)
    tweets = fetch_tweets(args.query, args.max)
    logger.info("Fetched %d tweets", len(tweets))

    if not tweets:
        logger.info("No tweets to store. Exiting.")
        return

    stats = store_tweets(MONGODB_URI, tweets)
    logger.info("Store complete: %s", stats)


if __name__ == "__main__":
    main()
