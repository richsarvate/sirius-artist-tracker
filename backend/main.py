from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import List, Optional
import json
from fastapi.middleware.cors import CORSMiddleware
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
from pydantic import BaseModel
import smtplib
from email.message import EmailMessage

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

app = FastAPI()

class CustomStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return response

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
import certifi
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False, tlsCAFile=certifi.where())
try:
    client.admin.command("ping")
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

db = client["sirius"]
collection = db["comedy_tracks"]
tracked_artists_collection = db["tracked_artists"]
first_plays_collection = db["first_plays"]

# Replace loading from JSON with loading from MongoDB
TRACKED_ARTISTS_DATA = list(tracked_artists_collection.find({}, {"_id": 0, "artist": 1, "tracks": 1}))
ARTISTS = [item["artist"] for item in TRACKED_ARTISTS_DATA]
TRACKS = []
for item in TRACKED_ARTISTS_DATA:
    TRACKS.extend(item["tracks"])

@app.get("/")
async def read_root():
    return FileResponse("/home/ec2-user/sirius-artist-tracker/backend/static/index.html")

@app.get("/api/artist-plays")
async def artist_plays(start: Optional[str] = Query(None), end: Optional[str] = Query(None)):
    def clean_iso(date_str: Optional[str]) -> Optional[datetime]:
        if date_str:
            # Parse and convert to Eastern Time (EDT/EST)
            dt = datetime.fromisoformat(date_str.rstrip("Z"))
            return dt.astimezone(ZoneInfo("America/New_York"))
        return None

    try:
        # Use Eastern Time for start and end
        start_dt = clean_iso(start) or datetime(2020, 1, 1, tzinfo=ZoneInfo("America/New_York"))
        end_dt = clean_iso(end) or datetime.now(ZoneInfo("America/New_York"))
        print(f"Querying for artists: {ARTISTS}, tracks: {TRACKS}, start: {start_dt}, end: {end_dt}")
        pipeline = [
            {
                "$match": {
                    "artist": {"$in": ARTISTS},
                    "title": {"$in": TRACKS},
                    "timestamp": {"$gte": start_dt.isoformat() + "Z", "$lte": end_dt.isoformat() + "Z"}
                }
            },
            {
                "$group": {
                    "_id": "$artist",
                    "tracks": {
                        "$push": {
                            "title": "$title",
                            "channel": "$channel",
                            "timestamp": "$timestamp"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$project": {
                    "artist": "$_id",
                    "tracks": {
                        "$sortArray": {
                            "input": "$tracks",
                            "sortBy": {"title": 1}
                        }
                    },
                    "count": 1,
                    "_id": 0
                }
            }
        ]
        results = list(collection.aggregate(pipeline, collation={"locale": "en", "strength": 2}))
        print(f"Query results: {results}")
        return {"data": results}
    except ValueError as e:
        print(f"ValueError: {str(e)}")
        return {"error": f"Invalid date format: {str(e)}"}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}

@app.get("/date-range/{period}")
async def get_date_range(period: str):
    now = datetime.now(ZoneInfo("America/Toronto"))
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=now.weekday())
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = datetime(2020, 1, 1, tzinfo=ZoneInfo("America/Toronto"))
    start = start - timedelta(hours=4)
    return {"start": start.isoformat(), "end": now.isoformat()}

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

class TokenRequest(BaseModel):
    credential: str

@app.post("/verify-google-token")
async def verify_token(data: TokenRequest):
    try:
        resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={data.credential}")
        if resp.status_code != 200:
            return JSONResponse(content={"allowed": False, "error": "Invalid token"}, status_code=401)
        payload = resp.json()
        email = payload.get("email")
        aud = payload.get("aud")
        allowed_emails = set(e.strip() for e in os.getenv("ALLOWED_EMAILS", "").split(",") if e.strip())
        if aud == GOOGLE_CLIENT_ID and email in allowed_emails:
            return {"allowed": True}
        else:
            return {"allowed": False}
    except Exception as e:
        return JSONResponse(content={"allowed": False, "error": str(e)}, status_code=500)

@app.post("/api/verify-google-token")
async def verify_token(data: TokenRequest):
    try:
        resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={data.credential}")
        if resp.status_code != 200:
            return JSONResponse(content={"allowed": False, "error": "Invalid token"}, status_code=401)
        payload = resp.json()
        email = payload.get("email")
        aud = payload.get("aud")
        allowed_emails = set(e.strip() for e in os.getenv("ALLOWED_EMAILS", "").split(",") if e.strip())
        if aud == GOOGLE_CLIENT_ID and email in allowed_emails:
            return {"allowed": True}
        else:
            return {"allowed": False}
    except Exception as e:
        return JSONResponse(content={"allowed": False, "error": str(e)}, status_code=500)

# Email configuration
FIRST_PLAY_EMAIL_RECIPIENT = os.getenv("FIRST_PLAY_EMAIL_RECIPIENT", "richard@setupcomedy.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_first_play_email_sync(artist: str, title: str, channel: str):
    """Send email notification for first-time track play (synchronous)"""
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            print("SMTP credentials not configured, skipping email")
            return

        # Create message
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = FIRST_PLAY_EMAIL_RECIPIENT
        msg["Subject"] = "New Track Played on Sirius!"
        
        # Email body
        body = f"""{title} by {artist} just played for the first time on {channel}.

See report here: https://xm.setupcomedy.com"""
        
        msg.set_content(body)

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"First play email sent for: {title} by {artist}")

    except Exception as e:
        print(f"Failed to send first play email: {str(e)}")

async def check_and_record_first_plays(plays_data):
    """Check for first-time plays and send notifications"""
    try:
        current_time = datetime.now(ZoneInfo("America/New_York"))
        
        for play in plays_data:
            artist = play.get("artist")
            title = play.get("title") 
            channel = play.get("channel")
            timestamp = play.get("timestamp")

            if not all([artist, title, channel]):
                continue

            # Check if this artist/title combo is tracked
            tracked_artist = tracked_artists_collection.find_one({"artist": artist})
            if not tracked_artist or title not in tracked_artist.get("tracks", []):
                continue

            # Check if we've already recorded this as a first play
            existing_first_play = first_plays_collection.find_one({
                "artist": artist,
                "title": title
            })

            if not existing_first_play:
                # This is a first play! Record it and send email
                first_plays_collection.insert_one({
                    "artist": artist,
                    "title": title,
                    "firstPlayDate": current_time.isoformat(),
                    "channel": channel,
                    "timestamp": timestamp
                })

                # Send email notification (now synchronous)
                send_first_play_email_sync(artist, title, channel)

    except Exception as e:
        print(f"Error checking first plays: {str(e)}")

# Add this function to process new plays (call this when you receive new SiriusXM data)
async def process_new_plays(plays_data):
    """Process new plays and check for first-time plays"""
    # Check for first plays
    await check_and_record_first_plays(plays_data)
    
    # Continue with your existing play processing logic
    # ... (your existing code to save plays to main collection)

@app.post("/api/ingest-plays")
async def ingest_plays(plays: list):
    """Endpoint to receive new play data"""
    try:
        await process_new_plays(plays)
        return {"status": "success", "processed": len(plays)}
    except Exception as e:
        print(f"Error ingesting plays: {str(e)}")
        return {"error": str(e)}

@app.post("/api/test-first-play-email")
async def test_first_play_email():
    """Test endpoint for first play email"""
    send_first_play_email_sync("Test Artist", "Test Song", "Test Channel")
    return {"status": "Test email sent"}

# Add this after your existing database setup
try:
    first_plays_collection.create_index([("artist", 1), ("title", 1)], unique=True)
    print("First plays collection index created")
except Exception as e:
    print(f"Index creation error (probably already exists): {e}")