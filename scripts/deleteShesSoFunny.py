from pymongo import MongoClient

# MongoDB connection
MONGO_URI = "mongodb+srv://setup:u2eIkhlwU0k5rya8@cluster0.jsdumcm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["sirius"]
collection = db["comedy_tracks"]

# Define the query to match records with channel "She's So Funny"
query = {"channel": "She's So Funny"}

# Count records to be deleted (optional verification)
count_before = collection.count_documents(query)
print(f"Number of records to delete: {count_before}")

# Perform the deletion
result = collection.delete_many(query)
print(f"Deleted {result.deleted_count} records with channel 'She's So Funny'")

# Verify remaining records (optional)
count_after = collection.count_documents(query)
print(f"Number of remaining records with channel 'She's So Funny': {count_after}")
