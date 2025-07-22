import json
from pymongo import MongoClient

# MongoDB connection
MONGO_URI = "mongodb+srv://setup:u2eIkhlwU0k5rya8@cluster0.jsdumcm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["sirius"]
collection = db["comedy_tracks"]

# Load tracked artists and tracks
with open("tracked_artists.json") as f:
    tracked_data = json.load(f)

# Extract artists and tracks
artists = [item["artist"] for item in tracked_data]
tracks = []
for item in tracked_data:
    tracks.extend(item["tracks"])

# Query MongoDB for records matching tracked artists and tracks
pipeline = [
    {
        "$match": {
            "artist": {"$in": artists},
            "title": {"$in": tracks}
        }
    },
    {
        "$group": {
            "_id": {
                "artist": "$artist",
                "title": "$title"
            },
            "count": {"$sum": 1}
        }
    },
    {
        "$group": {
            "_id": "$_id.artist",
            "total_records": {"$sum": "$count"},
            "tracks": {
                "$push": {
                    "title": "$_id.title",
                    "count": "$count"
                }
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "artist": "$_id",
            "total_records": 1,
            "tracks": 1
        }
    }
]

# Execute the aggregation and print results
results = list(collection.aggregate(pipeline))

for result in results:
    print(f"Artist: {result['artist']}")
    print(f"Total Records: {result['total_records']}")
    for track in result['tracks']:
        print(f"  Track: {track['title']}, Count: {track['count']}")
    print()

# Calculate and print overall total
overall_total = sum(result['total_records'] for result in results)
print(f"Overall Total Records for Tracked Artists and Tracks: {overall_total}")
