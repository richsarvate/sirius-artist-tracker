#!/usr/bin/env python3
"""
Export all data from MongoDB tracked_artists collection to CSV and JSON files.
This script downloads all records from Cluster0 -> sirius -> tracked_artists
and saves them in both formats for different use cases.
"""

import os
import sys
import csv
import json
import logging
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('export_tracked_artists.log')
    ]
)
logger = logging.getLogger(__name__)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    logger.error("MONGO_URI not set in environment variables")
    sys.exit(1)

# Output file configuration
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
JSON_OUTPUT_FILE = f"tracked_artists_export_{timestamp}.json"
CSV_OUTPUT_FILE = f"tracked_artists_export_{timestamp}.csv"

def export_to_json(collection):
    """Export tracked_artists data to JSON file (preserves array structure)."""
    logger.info(f"Writing JSON data to {JSON_OUTPUT_FILE}...")
    
    # Fetch all documents
    documents = list(collection.find({}, {"_id": 0}))  # Exclude MongoDB's _id field
    
    # Write to JSON file
    with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as jsonfile:
        json.dump(documents, jsonfile, indent=2, ensure_ascii=False)
    
    return len(documents)

def export_to_csv(collection):
    """Export tracked_artists data to CSV file (flattened - one row per artist-track)."""
    logger.info(f"Writing CSV data to {CSV_OUTPUT_FILE}...")
    
    # Define CSV headers
    headers = ["artist", "track"]
    
    # Open CSV file for writing
    with open(CSV_OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        rows_written = 0
        
        # Fetch and flatten the data
        for doc in collection.find({}, {"_id": 0}):
            artist = doc.get("artist", "")
            tracks = doc.get("tracks", [])
            
            # Write one row for each track
            for track in tracks:
                writer.writerow([artist, track])
                rows_written += 1
        
        return rows_written

def export_tracked_artists():
    """Export all tracked_artists data to both JSON and CSV files."""
    
    logger.info("Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        client.server_info()  # Test connection
        db = client["sirius"]
        collection = db["tracked_artists"]
        logger.info("✅ Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    try:
        # Count total artist records
        total_artists = collection.count_documents({})
        logger.info(f"Total artist records to export: {total_artists:,}")
        
        if total_artists == 0:
            logger.warning("No records found in tracked_artists collection")
            client.close()
            return
        
        # Export to JSON (preserves structure)
        json_records = export_to_json(collection)
        
        # Export to CSV (flattened)
        csv_rows = export_to_csv(collection)
        
        logger.info("✅ Export completed successfully!")
        logger.info("=" * 50)
        logger.info(f"📁 JSON Output: {JSON_OUTPUT_FILE}")
        logger.info(f"📊 Artists exported: {json_records:,}")
        
        # Display JSON file size
        json_size_bytes = os.path.getsize(JSON_OUTPUT_FILE)
        json_size_kb = json_size_bytes / 1024
        logger.info(f"💾 JSON File size: {json_size_kb:.2f} KB")
        
        logger.info("=" * 50)
        logger.info(f"📁 CSV Output: {CSV_OUTPUT_FILE}")
        logger.info(f"📊 Artist-track combinations: {csv_rows:,}")
        
        # Display CSV file size
        csv_size_bytes = os.path.getsize(CSV_OUTPUT_FILE)
        csv_size_kb = csv_size_bytes / 1024
        logger.info(f"💾 CSV File size: {csv_size_kb:.2f} KB")
        
    except Exception as e:
        logger.error(f"❌ Error during export: {e}")
        sys.exit(1)
    finally:
        client.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting MongoDB tracked_artists export")
    logger.info("=" * 60)
    
    try:
        export_tracked_artists()
        logger.info("=" * 60)
        logger.info("Export script completed successfully")
        logger.info("=" * 60)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Export interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        sys.exit(1)