import csv
from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB connection
MONGO_URI = "mongodb+srv://setup:u2eIkhlwU0k5rya8@cluster0.jsdumcm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["sirius"]
collection = db["comedy_tracks"]

# CSV file path
csv_file = '/home/ec2-user/SiriusMonitoring/dataPopulator/report.csv'

# Initialize counters
found_count = 0
not_found_count = 0

# Read CSV and check records
with open(csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Parse the timestamp and adjust by adding 4 hours to match MongoDB UTC
        try:
            ts = datetime.strptime(row['datetime'], '%Y-%m-%d %H:%M:%S')
            utc_ts = ts + timedelta(hours=4)
            adjusted_ts = utc_ts.isoformat() + '.000Z'  # Add milliseconds for consistency
        except ValueError as e:
            print(f"Error parsing timestamp for {row['Artist']}, {row['Song']}: {e}")
            continue

        # Create query based on artist and adjusted timestamp
        query = {
            "artist": row['Artist'],
            "timestamp": {
                "$regex": f"^{adjusted_ts.split('.')[0]}(\\.\\d{{0,6}})?Z$"
            }
        }

        # Check if the record exists in MongoDB
        existing_record = collection.find_one(query)
        if existing_record:
            print(f"Record found in DB: Artist={row['Artist']}, Song={row['Song']}, Timestamp={row['datetime']} (Adjusted to {adjusted_ts})")
            found_count += 1
        else:
            print(f"Record NOT found in DB: Artist={row['Artist']}, Song={row['Song']}, Timestamp={row['datetime']} (Adjusted to {adjusted_ts})")
            not_found_count += 1

# Print totals
print(f"\nTotal records found: {found_count}")
print(f"Total records not found: {not_found_count}")
