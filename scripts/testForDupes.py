import csv
from pymongo import MongoClient
from datetime import datetime, timedelta
import re

# MongoDB connection string
MONGO_URI = "mongodb+srv://setup:u2eIkhlwU0k5rya8@cluster0.jsdumcm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Database and collection names
db_name = "sirius"
collection_name = "comedy_tracks"

# CSV file path
csv_file = '/home/ec2-user/SiriusMonitoring/dataPopulator/report.csv'

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[db_name]
collection = db[collection_name]

# Collect conditions for duplicates and debug info
conditions = []
csv_records = []

# Read the CSV and build the query conditions with 4-hour adjustment
with open(csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Parse the timestamp (add 4 hours to align with MongoDB UTC)
        try:
            ts = datetime.strptime(row['datetime'], '%Y-%m-%d %H:%M:%S')
            # Adjust by adding 4 hours to match MongoDB UTC
            utc_ts = ts + timedelta(hours=4)
            base_ts = utc_ts.isoformat()
        except ValueError as e:
            print(f"Error parsing timestamp in row: {row['datetime']}, Error: {e}")
            continue

        # Create condition for this row
        condition = {
            "artist": row['Artist'],
            "timestamp": {
                "$regex": f"^{re.escape(base_ts)}(\\.\\d{{0,6}})?Z$"
            }
        }
        conditions.append(condition)
        csv_records.append({"artist": row['Artist'], "timestamp": base_ts})

# Perform a single query to find all matching documents
duplicate_count = 0
if conditions:
    # Use $or to check all conditions in one query
    matching_docs = collection.find({"$or": conditions})

    # Collect and count matching documents
    duplicates = []
    for doc in matching_docs:
        duplicates.append({
            "artist": doc["artist"],
            "timestamp": doc["timestamp"],
            "title": doc.get("title", "N/A"),
            "channel": doc.get("channel", "N/A")
        })
        duplicate_count += 1

    # Print duplicates for debugging
    if duplicates:
        print("Found duplicates:")
        for dup in duplicates:
            print(f"  Artist: {dup['artist']}, Timestamp: {dup['timestamp']}, Title: {dup['title']}, Channel: {dup['channel']}")
    else:
        print("No duplicates found in the collection.")

    # Print sample CSV records for comparison
    print("\nSample CSV records (first 5):")
    for record in csv_records[:5]:
        print(f"  Artist: {record['artist']}, Timestamp: {record['timestamp']}")

    # Print sample MongoDB records for comparison
    print("\nSample MongoDB records (first 5):")
    sample_docs = collection.find().limit(5)
    for doc in sample_docs:
        print(f"  Artist: {doc['artist']}, Timestamp: {doc['timestamp']}, Title: {doc.get('title', 'N/A')}, Channel: {doc.get('channel', 'N/A')}")

else:
    print("No records to check in the CSV.")

print(f"\nFound {duplicate_count} duplicate records in the collection.")
