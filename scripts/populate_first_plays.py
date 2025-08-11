import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["sirius"]
collection = db["comedy_tracks"]
tracked_artists_collection = db["tracked_artists"]
first_plays_collection = db["first_plays"]

def populate_existing_first_plays():
    """Mark all existing tracked songs as already played"""
    
    # Get all tracked artists and their tracks
    tracked_artists_data = list(tracked_artists_collection.find({}, {"_id": 0, "artist": 1, "tracks": 1}))
    
    # Create a set of all tracked artist/title combinations
    tracked_combinations = set()
    for item in tracked_artists_data:
        artist = item["artist"]
        for track in item.get("tracks", []):
            tracked_combinations.add((artist, track))
    
    print(f"Found {len(tracked_combinations)} tracked artist/song combinations")
    
    # Find all plays in comedy_tracks that match tracked combinations
    existing_plays = {}
    
    for artist, title in tracked_combinations:
        # Find the earliest play of this song
        earliest_play = collection.find_one(
            {"artist": artist, "title": title},
            sort=[("timestamp", 1)]
        )
        
        if earliest_play:
            existing_plays[(artist, title)] = {
                "artist": artist,
                "title": title,
                "firstPlayDate": earliest_play["timestamp"],
                "channel": earliest_play["channel"],
                "timestamp": earliest_play["timestamp"]
            }
    
    print(f"Found {len(existing_plays)} existing plays of tracked songs")
    
    # Insert into first_plays collection
    if existing_plays:
        documents = list(existing_plays.values())
        try:
            # Use insert_many with ordered=False to continue on duplicates
            result = first_plays_collection.insert_many(documents, ordered=False)
            print(f"Successfully inserted {len(result.inserted_ids)} first plays")
        except Exception as e:
            print(f"Some duplicates encountered (expected): {e}")
            # Count what actually got inserted
            count = first_plays_collection.count_documents({})
            print(f"Total documents in first_plays collection: {count}")
    
    print("Populate first plays completed!")

if __name__ == "__main__":
    populate_existing_first_plays()
    client.close()