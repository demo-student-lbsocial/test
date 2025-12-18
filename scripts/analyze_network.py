#!/usr/bin/env python3
"""Analyze user network from tweets stored in demo.tweet_collection.

Builds a directed mention graph (author -> mentioned_user) using @mentions in tweet text.
Outputs summary stats, top users, and optionally saves GraphML and a PNG image.

Usage:
  pip install -r requirements.txt
  python scripts/analyze_network.py --top 10 --save outputs/network.graphml --image outputs/network.png
"""

import os
import re
import argparse
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
import pymongo
import networkx as nx
import matplotlib.pyplot as plt

MENTION_RE = re.compile(r"@([A-Za-z0-9_]{1,15})")


def load_tweets(mongo_uri: str):
    client = pymongo.MongoClient(mongo_uri)
    db = client["demo"]
    coll = db["tweet_collection"]
    for doc in coll.find({}, {"_id": 1, "author": 1, "text": 1, "created_at": 1}):
        yield doc


def build_mention_graph(tweets):
    G = nx.DiGraph()
    mention_counter = Counter()
    for t in tweets:
        author = (t.get("author") or "").lower()
        text = t.get("text") or ""
        mentions = [m.lower() for m in MENTION_RE.findall(text)]
        for m in mentions:
            if m == author or m == "":
                continue
            mention_counter[(author, m)] += 1
            if not G.has_node(author):
                G.add_node(author)
            if not G.has_node(m):
                G.add_node(m)
            if G.has_edge(author, m):
                G[author][m]["weight"] += 1
            else:
                G.add_edge(author, m, weight=1)
    return G, mention_counter


def save_graph(G, path: str, draw_image: str = None):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, path)
    if draw_image:
        plt.figure(figsize=(12, 8))
        # Draw a small layout of the largest connected component for readability
        if len(G) == 0:
            plt.text(0.5, 0.5, "Empty graph", horizontalalignment="center")
        else:
            try:
                comp = max(nx.weakly_connected_components(G), key=len)
                sub = G.subgraph(comp)
            except Exception:
                sub = G
            pos = nx.spring_layout(sub, k=0.5)
            weights = [d.get("weight", 1) for (_, _, d) in sub.edges(data=True)]
            nx.draw_networkx_nodes(sub, pos, node_size=100, node_color="#1f78b4")
            nx.draw_networkx_edges(sub, pos, width=[max(0.5, w * 0.2) for w in weights], alpha=0.7)
            nx.draw_networkx_labels(sub, pos, font_size=8)
        plt.axis("off")
        Path(draw_image).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(draw_image, bbox_inches="tight", dpi=150)
        plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=10, help="How many top users to show")
    parser.add_argument("--save", type=str, help="Path to save GraphML (optional)")
    parser.add_argument("--image", type=str, help="Path to save PNG image of the graph (optional)")
    args = parser.parse_args()

    load_dotenv()
    MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGODB_CONNECT")
    if not MONGODB_URI:
        print("MongoDB connection not set. Set MONGODB_CONNECT or MONGODB_URI in env or .env")
        return

    tweets = list(load_tweets(MONGODB_URI))
    print(f"Loaded {len(tweets)} tweets from demo.tweet_collection")

    G, mention_counter = build_mention_graph(tweets)
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    print(f"Graph nodes: {n_nodes}, edges: {n_edges}")

    if n_nodes == 0:
        print("No mention edges found in tweets. Consider using co-occurrence or adding referenced tweets data.")
        return

    indeg = sorted(G.in_degree(weight="weight"), key=lambda x: x[1], reverse=True)
    outdeg = sorted(G.out_degree(weight="weight"), key=lambda x: x[1], reverse=True)

    print(f"\nTop {args.top} most-mentioned users (in-degree):")
    for user, d in indeg[: args.top]:
        print(f"  {user}: {d}")

    print(f"\nTop {args.top} most-active mentioners (out-degree):")
    for user, d in outdeg[: args.top]:
        print(f"  {user}: {d}")

    try:
        centrality = nx.degree_centrality(G)
        top_cent = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[: args.top]
        print(f"\nTop {args.top} by degree centrality:")
        for user, score in top_cent:
            print(f"  {user}: {score:.4f}")
    except Exception:
        pass

    if args.save:
        save_graph(G, args.save, args.image)
        print(f"Saved graph to {args.save}")
        if args.image:
            print(f"Saved graph image to {args.image}")


if __name__ == "__main__":
    main()
