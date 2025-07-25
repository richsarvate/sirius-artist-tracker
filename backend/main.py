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
            return datetime.fromisoformat(date_str.rstrip("Z"))
        return None

    try:
        start_dt = clean_iso(start) or datetime(2020, 1, 1)
        end_dt = clean_iso(end) or datetime.utcnow()
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
                            "channel": "$channel"
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

from pydantic import BaseModel
import requests

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