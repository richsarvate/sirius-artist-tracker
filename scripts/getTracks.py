import pymongo
from pymongo import MongoClient
import requests
from datetime import datetime
from dateutil import parser
import logging
import sys
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv(dotenv_path="../.env", override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('comedy_tracks.log')
    ]
)

logger = logging.getLogger(__name__)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    logger.error("MONGO_URI not set in environment variables")
    sys.exit(1)

max_retries = 3
backoff_factors = [5, 10, 20]  # Seconds for each retry attempt

# Attempt MongoDB connection with retries
for attempt in range(max_retries):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        # Test connection by accessing server info
        client.server_info()
        db = client["sirius"]
        collection = db["comedy_tracks"]
        stations_collection = db["tracked_stations"]
        logger.info("Connected to MongoDB")
        break
    except (pymongo.errors.ConnectionError, pymongo.errors.ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB (attempt {attempt + 1}/{max_retries}): {e}")
        if attempt < max_retries - 1:
            sleep_time = backoff_factors[attempt]
            logger.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            logger.error("Max retries reached for MongoDB connection. Exiting.")
            sys.exit(1)

# Ensure the 'id' field from the API is unique
for attempt in range(max_retries):
    try:
        collection.create_index("id", unique=True)
        logger.info("Unique index on 'id' created")
        break
    except pymongo.errors.OperationFailure as e:
        logger.error(f"Failed to create index (attempt {attempt + 1}/{max_retries}): {e}")
        if attempt < max_retries - 1:
            sleep_time = backoff_factors[attempt]
            logger.info(f"Retrying index creation in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            logger.error("Max retries reached for index creation. Exiting.")
            sys.exit(1)

BASE_URL = os.getenv("XMPLAYLIST_BASE_URL", "https://xmplaylist.com/api/station/")

def fetch_and_store():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Authorization": f"Bearer {os.getenv('XMPLAYLIST_API_KEY', '')}"
    }
    logger.info(f"Headers: {headers}")

    # Load station names from MongoDB
    station_docs = list(stations_collection.find({}, {"_id": 0, "name": 1}))
    STATION_NAMES = [doc["name"] for doc in station_docs]
    logger.info(f"Loaded {len(STATION_NAMES)} stations from MongoDB: {STATION_NAMES}")

    for station in STATION_NAMES:
        logger.info(f"Processing station: {station}")
        url = f"{BASE_URL}{station}"
        logger.info(f"Requesting URL: {url}")
        tracks_added = 0

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            channel_name = data.get("channel", {}).get("name", "")
            results = data.get("results", [])
            logger.info(f"[{channel_name}] Tracks received: {len(results)}")

            for item in results:
                try:
                    track_info = {
                        "id": item["id"],
                        "timestamp": item["timestamp"],
                        "title": ' '.join(word.capitalize() for word in item["track"]["title"].split()),
                        "artist": item["track"]["artists"][0] if item["track"]["artists"] else None,
                        "channel": channel_name
                    }
                    result = collection.update_one(
                        {"id": track_info["id"]},
                        {"$setOnInsert": track_info},
                        upsert=True
                    )
                    if result.upserted_id:
                        tracks_added += 1

                except KeyError as e:
                    logger.error(f"[{channel_name}] KeyError processing track item: {e}")
                    continue
                except pymongo.errors.DuplicateKeyError as e:
                    logger.warning(f"[{channel_name}] Duplicate key for track ID {item['id']}")
                    continue
                except Exception as e:
                    logger.error(f"[{channel_name}] Error processing track: {e}")
                    continue

            logger.info(f"[{channel_name}] Tracks added: {tracks_added}")

            try:
                timestamps = [parser.parse(item["timestamp"]) for item in results]
                if timestamps:
                    time_span = max(timestamps) - min(timestamps)
                    total_seconds = int(time_span.total_seconds())
                    minutes, seconds = divmod(total_seconds, 60)
                    logger.info(f"[{channel_name}] Time Span: {minutes}m {seconds}s")
                else:
                    logger.warning(f"[{channel_name}] No timestamps found")
            except ValueError as e:
                logger.error(f"[{channel_name}] Error parsing timestamps: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"[{station}] Request error: {e}")
            continue
        except Exception as e:
            logger.error(f"[{station}] Unexpected error: {e}")
            continue

    logger.info("Finished processing all stations")

if __name__ == "__main__":
    logger.info("Starting fetch_and_store script")
    try:
        fetch_and_store()
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Closing MongoDB connection")
        client.close()