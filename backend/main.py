from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import subprocess
import json
import os

from app.backend.database import Database
from app.backend.matcher import match_fingerprint

app = FastAPI()

# Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats():
    """Get database statistics."""
    return {
        "songs": db.get_song_count(),
        "fingerprints": db.get_fingerprint_count()
    }

@app.post("/identify")
async def identify(file: UploadFile = File(...)):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_in:
        tmp_in.write(await file.read())
        tmp_in.flush()
        wav_path = tmp_in.name.replace(".webm", ".wav")

    # Convert to mono 16k WAV
    subprocess.run(["ffmpeg", "-y", "-i", tmp_in.name, "-ar", "16000", "-ac", "1", wav_path])

    # Run fpcalc
    try:
        out = subprocess.check_output(["fpcalc", "-json", wav_path])
        data = json.loads(out)
        query_fp = data["fingerprint"]
    except Exception as e:
        return {"error": str(e)}

    # Match fingerprint against DB
    tracks = db.fetch_tracks()
    fps = db.fetch_fingerprints()
    result = match_fingerprint(query_fp, tracks, fps)

    os.remove(tmp_in.name)
    os.remove(wav_path)

    if result:
        return JSONResponse(content={
            "status": "match_found",
            "song": {
                "title": result['title'],
                "artist": result['artist'],
                "confidence": round(result['confidence'], 3),
                "match_count": result['match_count']
            },
            "debug": {
                "db_songs": db.get_song_count(),
                "db_fingerprints": db.get_fingerprint_count()
            }
        })
    else:
        return JSONResponse(content={
            "status": "no_match",
            "message": "No matching song found in database",
            "debug": {
                "db_songs": db.get_song_count(),
                "db_fingerprints": db.get_fingerprint_count()
            }
        })

if __name__ == "__main__":
    uvicorn.run("app.backend.main:app", host="127.0.0.1", port=8000, reload=True)
