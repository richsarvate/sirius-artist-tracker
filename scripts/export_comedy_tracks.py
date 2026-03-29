#!/usr/bin/env python3
"""
Export all data from MongoDB comedy_tracks collection to CSV file.
This script downloads all records from Cluster0 -> sirius -> comedy_tracks
and saves them to a CSV file for ML training purposes.
"""

import os
import sys
import csv
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
        logging.FileHandler('export_comedy_tracks.log')
    ]
)
logger = logging.getLogger(__name__)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    logger.error("MONGO_URI not set in environment variables")
    sys.exit(1)

# Output file configuration
OUTPUT_FILE = f"comedy_tracks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

def export_to_csv():
    """Export all comedy_tracks data to CSV file."""
    
    logger.info("Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=30000)
        client.server_info()  # Test connection
        db = client["sirius"]
        collection = db["comedy_tracks"]
        logger.info("✅ Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    try:
        # Count total records
        total_records = collection.count_documents({})
        logger.info(f"Total records to export: {total_records:,}")
        
        if total_records == 0:
            logger.warning("No records found in collection")
            client.close()
            return
        
        # Define CSV headers based on document structure
        headers = ["id", "timestamp", "title", "artist", "channel"]
        
        # Open CSV file for writing
        logger.info(f"Writing data to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            # Fetch and write records in batches for memory efficiency
            batch_size = 10000
            records_written = 0
            
            for doc in collection.find({}, {"_id": 0}):  # Exclude MongoDB's _id field
                # Write the document directly (DictWriter handles the field mapping)
                writer.writerow(doc)
                records_written += 1
                
                # Log progress every batch_size records
                if records_written % batch_size == 0:
                    logger.info(f"Progress: {records_written:,} / {total_records:,} records written ({(records_written/total_records)*100:.1f}%)")
        
        logger.info(f"✅ Export completed successfully!")
        logger.info(f"📁 Output file: {OUTPUT_FILE}")
        logger.info(f"📊 Total records exported: {records_written:,}")
        
        # Display file size
        file_size_bytes = os.path.getsize(OUTPUT_FILE)
        file_size_mb = file_size_bytes / (1024 * 1024)
        logger.info(f"💾 File size: {file_size_mb:.2f} MB")
        
    except Exception as e:
        logger.error(f"❌ Error during export: {e}")
        sys.exit(1)
    finally:
        client.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting MongoDB comedy_tracks export to CSV")
    logger.info("=" * 60)
    
    try:
        export_to_csv()
        logger.info("=" * 60)
        logger.info("Export script completed successfully")
        logger.info("=" * 60)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Export interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        sys.exit(1)
