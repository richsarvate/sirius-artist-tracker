import pymongo
from pymongo import MongoClient
import pandas as pd
import logging
import sys
import os
from datetime import datetime, timedelta
from dateutil import parser, tz
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('check_tracks.log')
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger('pymongo').setLevel(logging.WARNING)

# MongoDB setup
MONGO_URI = "mongodb+srv://setup:u2eIkhlwU0k5rya8@cluster0.jsdumcm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
max_retries = 3
backoff_factors = [5, 10, 20]

# Attempt MongoDB connection with retries
for attempt in range(max_retries):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        client.server_info()
        db = client["sirius"]
        collection = db["comedy_tracks"]
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

def check_records(csv_file):
    """Check if CSV records exist in MongoDB comedy_tracks collection."""
    logger.info(f"Processing CSV file: {csv_file}")
    try:
        df = pd.read_csv(csv_file, header=None, names=["artist", "title", "channel", "timestamp", "unused1", "unused2"])
        logger.info(f"Loaded {len(df)} rows from CSV")

        found_count = 0
        missed_records = []

        for index, row in df.iterrows():
            try:
                artist = row["artist"].strip()
                title = row["title"].strip()
                timestamp_str = row["timestamp"].strip()

                # Parse timestamp and convert to UTC
                dt_exact = parser.parse(timestamp_str)
                if dt_exact.tzinfo is None:
                    dt_exact = dt_exact.replace(tzinfo=tz.gettz("America/New_York"))
                dt_utc = dt_exact.astimezone(tz.UTC)

                # Define ±2 hour window
                start_time = dt_utc - timedelta(hours=2)
                end_time = dt_utc + timedelta(hours=2)

                # MongoDB query
                query = {
                    "artist": {"$regex": f"^{artist}$", "$options": "i"},
                    "title": {"$regex": f"^{title}$", "$options": "i"},
                    "timestamp": {
                        "$gte": start_time.isoformat(),
                        "$lte": end_time.isoformat()
                    }
                }

                record = collection.find_one(query)

                if record is not None:
                    logger.info(f"Record found: artist={artist}, title={title}, timestamp={dt_utc.strftime('%Y-%m-%dT%H:%M')}")
                    found_count += 1
                else:
                    logger.warning(f"Record not found: artist={artist}, title={title}, timestamp={dt_utc.strftime('%Y-%m-%dT%H:%M')}")
                    missed_records.append(row.to_dict())

            except (ValueError, KeyError) as e:
                logger.error(f"Error processing row {index + 1}: {e}")
                continue
            except pymongo.errors.PyMongoError as e:
                logger.error(f"MongoDB error processing row {index + 1}: {e}")
                continue

        logger.info(f"Summary: {found_count} records found, {len(missed_records)} records missed")
        if missed_records:
            missed_df = pd.DataFrame(missed_records)
            missed_df.to_csv("missed_records.csv", index=False)
            logger.info("Missed records written to missed_records.csv")

    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logger.error(f"CSV file is empty: {csv_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading CSV file {csv_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Usage: python check_csv_records.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    logger.info("Starting CSV record check")
    try:
        check_records(csv_file)
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Closing MongoDB connection")
        client.close()
