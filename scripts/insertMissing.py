import csv
import uuid
from datetime import datetime, timezone
from dateutil import parser, tz
from pymongo import MongoClient
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('insert_missing.log')
    ]
)

# MongoDB connection
MONGO_URI = "mongodb+srv://setup:u2eIkhlwU0k5rya8@cluster0.jsdumcm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["sirius"]
collection = db["comedy_tracks"]
logging.info("Connected to MongoDB")

# Input file
INPUT_CSV = "missed_records.csv"

# Timezones
ET = tz.gettz("America/New_York")
UTC = tz.UTC



def convert_to_utc(timestamp_str):
    """Convert ET timestamp string to naive UTC datetime with .000 microseconds."""
    dt_local = parser.parse(timestamp_str)
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=ET)
    dt_utc = dt_local.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)
    return dt_utc

def insert_records():
    with open(INPUT_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        inserted = 0

        for row in reader:
            try:
                artist = row["artist"].strip()
                title = row["title"].strip()
                channel = row["channel"].strip().split(":")[-1].strip()
                timestamp = convert_to_utc(row["timestamp"])

                doc = {
                    "id": str(uuid.uuid4()),
                    "artist": artist,
                    "channel": channel,
                    "timestamp": timestamp.isoformat() + "Z",
                    "title": title
                }

                collection.insert_one(doc)
                logging.info(f"✅ Inserted: {artist} - {title} - {timestamp.isoformat()}Z")
                inserted += 1

            except Exception as e:
                logging.error(f"❌ Error inserting row: {row} — {e}")

        logging.info(f"✅ Done. Inserted {inserted} records.")

if __name__ == "__main__":
    insert_records()
    client.close()
    logging.info("MongoDB connection closed.")
