import csv
import uuid
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

# Collect conditions for duplicates and prepare documents for insertion
conditions = []
new_documents = []

# Read the CSV and build query conditions and new documents
with open(csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Parse the timestamp (add 4 hours to align with MongoDB UTC)
        try:
            ts = datetime.strptime(row['datetime'], '%Y-%m-%d %H:%M:%S')
            # Adjust by adding 4 hours to match MongoDB UTC
            utc_ts = ts + timedelta(hours=4)
            base_ts = utc_ts.isoformat() + '.000Z'  # Add milliseconds for consistency
        except ValueError as e:
            print(f"Error parsing timestamp in row: {row['datetime']}, Error: {e}")
            continue

        # Extract channel name after ': '
        channel_parts = row['Channel'].split(': ', 1)
        channel = channel_parts[1] if len(channel_parts) > 1 else row['Channel']

        # Create condition for this row to check duplicates
        condition = {
            "artist": row['Artist'],
            "timestamp": {
                "$regex": f"^{re.escape(base_ts.split('.')[0])}(\\.\\d{{0,6}})?Z$"
            }
        }

        # Prepare new document in MongoDB format
        new_doc = {
            "id": str(uuid.uuid4()),
            "artist": row['Artist'],
            "channel": channel,
            "timestamp": base_ts,
            "title": row['Song']
        }

        conditions.append(condition)
        new_documents.append({"condition": condition, "document": new_doc})

# Perform a single query to find all matching documents
if conditions:
    # Use $or to check all conditions in one query
    matching_docs = collection.find({"$or": conditions})

    # Collect existing artist+timestamp combinations
    existing_keys = set()
    for doc in matching_docs:
        key = (doc["artist"], doc["timestamp"].split('.')[0])  # Ignore milliseconds for key
        existing_keys.add(key)

    # Filter and insert non-duplicate documents
    documents_to_insert = []
    for item in new_documents:
        condition = item["condition"]
        new_doc = item["document"]
        key = (new_doc["artist"], new_doc["timestamp"].split('.')[0])
        if key not in existing_keys:
            documents_to_insert.append(new_doc)

    # Insert non-duplicates into MongoDB
    if documents_to_insert:
        result = collection.insert_many(documents_to_insert)
        print(f"Inserted {len(result.inserted_ids)} new documents into the collection.")
    else:
        print("No new documents to insert (all were duplicates).")

    # Print sample inserted documents for debugging
    print("\nSample inserted documents (first 5):")
    inserted_docs = collection.find({"_id": {"$in": result.inserted_ids}}).limit(5) if documents_to_insert else []
    for doc in inserted_docs:
        print(f"  Artist: {doc['artist']}, Timestamp: {doc['timestamp']}, Title: {doc['title']}, Channel: {doc['channel']}")

    # Print sample CSV records for comparison
    print("\nSample CSV records (first 5):")
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            print(f"  Artist: {row['Artist']}, Timestamp: {row['datetime']}, Title: {row['Song']}, Channel: {row['Channel']}")

    # Print sample MongoDB records for comparison
    print("\nSample MongoDB records (first 5):")
    sample_docs = collection.find().limit(5)
    for doc in sample_docs:
        print(f"  Artist: {doc['artist']}, Timestamp: {doc['timestamp']}, Title: {doc.get('title', 'N/A')}, Channel: {doc.get('channel', 'N/A')}")

else:
    print("No records to check in the CSV.")
