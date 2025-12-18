#!/usr/bin/env python3
"""Simple check to print the number of documents in demo.tweet_collection"""
import os
import sys
from dotenv import load_dotenv
import pymongo

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGODB_CONNECT")
if not MONGODB_URI:
    print("MongoDB connection not set. Set MONGODB_CONNECT (preferred) or MONGODB_URI in env or .env file.")
    sys.exit(1)

client = pymongo.MongoClient(MONGODB_URI)
db = client["demo"]
count = db["tweet_collection"].count_documents({})
print(f"demo.tweet_collection count: {count}")
