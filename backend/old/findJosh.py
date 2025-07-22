from pymongo import MongoClient
from datetime import datetime

# MongoDB connection
MONGO_URI = "mongodb+srv://setup:u2eIkhlwU0k5rya8@cluster0.jsdumcm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["sirius"]
collection = db["comedy_tracks"]

# Define time range for All Time (2020-01-01 to 2025-07-16 06:04 PM PDT)
start_date = datetime(2020, 1, 1)  # Start of All Time
end_date = datetime(2025, 7, 16, 18, 4)  # 06:04 PM PDT = 01:04 UTC (PDT is UTC-7)

# Tracked tracks for Joshua Turek
tracked_tracks = ["Scooters & Cybertrucks", "Medium Height Guys & Marriage", "Role Playing"]

# Query for Joshua Turek with tracked tracks
query = {
    "artist": "Joshua Turek",
    "title": {"$in": tracked_tracks},
    "timestamp": {
        "$gte": start_date.isoformat() + "Z",
        "$lte": end_date.isoformat() + "Z"
    }
}
records = collection.find(query)

# Print results
record_list = list(records)  # Convert cursor to list to count
print(f"Found {len(record_list)} records for Joshua Turek with tracked tracks (All Time):")
for record in record_list:
    print(record)

# Get total count using count_documents
count = collection.count_documents(query)
print(f"Total records for Joshua Turek with tracked tracks (All Time): {count}")
