import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import os

# Configuration
CONFIG = {
    "output_path": "tracked_artists.json",
    "sheet_name": "The Setup ISRC codes",
    "credentials_file": "creds.json"
}

# Google Sheets setup
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
try:
    creds = Credentials.from_service_account_file(CONFIG["credentials_file"], scopes=scopes)
    client = gspread.authorize(creds)
except FileNotFoundError:
    print(f"Error: Credentials file '{CONFIG['credentials_file']}' not found.")
    exit(1)

# Open the Google Sheet
try:
    sheet = client.open(CONFIG["sheet_name"]).sheet1
except gspread.exceptions.SpreadsheetNotFound:
    print(f"Error: Google Sheet '{CONFIG['sheet_name']}' not found. Check the sheet name or sharing settings.")
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
    tracks = [title.title() for title in group["Title"].tolist()]  # Convert each track title to title case
    result.append({"artist": artist, "tracks": tracks})

# Sort artists alphabetically for consistency
result = sorted(result, key=lambda x: x["artist"])

# Ensure the output directory exists
output_dir = os.path.dirname(CONFIG["output_path"])
if output_dir:
    os.makedirs(output_dir, exist_ok=True)

# Save to JSON file
try:
    with open(CONFIG["output_path"], "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
    print(f"JSON file '{CONFIG['output_path']}' created successfully.")
except Exception as e:
    print(f"Error writing to '{CONFIG['output_path']}': {e}")
    exit(1)
