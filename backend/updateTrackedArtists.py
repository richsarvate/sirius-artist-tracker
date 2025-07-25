import os
import base64
import json
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from pymongo import MongoClient

load_dotenv(dotenv_path="../.env", override=True)

isrc_sheet = os.getenv("GOOGLE_SHEETS_ISRC_NAME")
mongo_url = os.getenv("MONGO_URI")
creds_base64 = os.getenv("GOOGLE_SHEETS_JSON_BASE64")

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    if not creds_base64:
        raise Exception("GOOGLE_SHEETS_JSON_BASE64 not found in environment.")
    creds_json = base64.b64decode(creds_base64).decode("utf-8")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
except Exception as e:
    print(f"Error loading Google Sheets credentials: {e}")
    exit(1)

# Open the Google Sheet
try:
    sheet = client.open(isrc_sheet).sheet1
except gspread.exceptions.SpreadsheetNotFound:
    print(f"Error: Google Sheet '{isrc_sheet}' not found. Check the sheet name or sharing settings.")
    exit(1)

# Read all data from the sheet
try:
    data = sheet.get_all_records()
except gspread.exceptions.APIError as e:
    print(f"Error accessing Google Sheet: {e}")
    exit(1)

# Convert to pandas DataFrame
df = pd.DataFrame(data)

# Group by artist and collect tracks in title case
result = []
for artist, group in df.groupby("Artist"):
    tracks = [title.title() for title in group["Title"].tolist()]
    result.append({"artist": artist, "tracks": tracks})

# Sort artists alphabetically for consistency
result = sorted(result, key=lambda x: x["artist"])

# Save to MongoDB
try:
    mongo_client = MongoClient(mongo_url)
    db = mongo_client["sirius"]
    collection = db["tracked_artists"]
    collection.delete_many({})  # Clear existing data
    collection.insert_many(result)
    print("Data saved to MongoDB collection 'tracked_artists' in 'sirius' database.")
except Exception as e:
    print(f"Error saving data to MongoDB: {e}")
    exit(1)

