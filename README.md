# SiriusXM Artist Plays Tracker 🎙️📊

Track comedy artist spins from SiriusXM, estimate royalties, and view detailed reports — all in a secure, private dashboard.

---

## 🚀 Features

- 🔁 Scrapes track play data 
- 💾 Stores unique plays in MongoDB
- 🧠 Filters by tracked artists from a Google Sheet
- 📊 Displays artist and track breakdown in a React + Tailwind dashboard
- 🔐 Google Sign-In (restricted to allowed emails)
- 💵 Estimates royalties 

---

## 🛠 Tech Stack

- **Backend**: Python, FastAPI
- **Frontend**: React, TypeScript, TailwindCSS
- **Database**: MongoDB Atlas
- **Auth**: Google OAuth (ID token verification)
- **Infra**: EC2 + Nginx reverse proxy

---

## 🗂 Project Structure

```
.
├── api/                            # FastAPI backend
│   ├── main.py                     # API endpoints
│   ├── fetch_and_store.py          # Scrapes and stores SiriusXM data
│   ├── static/                     # Compiled React app
│   └── tracked_artists.json        # Synced from Google Sheet
├── frontend/                       # (optional) React app source
├── sync_sheet_to_json.py           # Pulls artist list from Google Sheet
├── creds.json                      # Google service account credentials
```

---

## 🔧 Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/YOUR_USERNAME/sirius-artist-tracker.git
cd sirius-artist-tracker
```

### 2. Backend Setup

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` or update `main.py` with your Mongo URI:

```env
MONGO_URI=mongodb+srv://...
```

### 3. Frontend Build

If you have the raw React app:

```bash
cd frontend
npm install
npm run build
```

Then copy the build output to `/api/static/`.

### 4. Google Sheet Sync

- Create a Google Sheet called `The Setup ISRC codes`
- Share it with your service account email (from `creds.json`)
- Run:

```bash
python sync_sheet_to_json.py
```

---

## ▶️ Run the App

From `/api/` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit [http://localhost:8000](http://localhost:8000)

---

## 🔁 Scrape Data

```bash
python fetch_and_store.py
```

This pulls latest spins from each comedy channel and upserts into MongoDB.

---

## 👤 Authentication

Only users with approved emails can log in using Google Sign-In. This is verified in `/api/main.py`.

---

## 📊 Dashboard

- View top artists by spin count
- Expand to see individual track breakdowns
- Select date range: today, week, month, year, etc.
- Auto-calculates estimated royalties

---

## 📄 License

MIT License. Use responsibly.
