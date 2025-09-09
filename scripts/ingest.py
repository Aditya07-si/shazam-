#!/usr/bin/env python3
import os
import sys
import subprocess
import sqlite3
from pathlib import Path

from app.backend.database import Database

# --- Helpers ---

def run_ffmpeg_to_wav(src_path, tmp_wav):
    """Convert input audio file to mono 16kHz WAV for fpcalc."""
    cmd = [
        "ffmpeg", "-y", "-i", src_path,
        "-ar", "16000", "-ac", "1",
        tmp_wav
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

def run_fpcalc(path):
    """Run fpcalc and return duration + fingerprint string."""
    cmd = ["fpcalc", "-json", path]
    out = subprocess.check_output(cmd)
    import json
    data = json.loads(out)
    return data["duration"], data["fingerprint"]

# --- Main ingestion ---

def ingest_songs(reference_dir="data/reference"):
    db = Database()
    ref_path = Path(reference_dir)
    audio_files = [f for f in ref_path.iterdir() if f.suffix.lower() in (".mp3", ".wav", ".flac", ".m4a")]

    print(f"Found {len(audio_files)} audio files to process...")

    processed, errors = 0, 0

    for audio_file in audio_files:
        print(f"Processing: {audio_file.name}")
        try:
            tmp_wav = "data/tmp_conv.wav"
            run_ffmpeg_to_wav(str(audio_file), tmp_wav)

            duration, fingerprint = run_fpcalc(tmp_wav)

            # Use filename as title, unknown artist for now
            title = audio_file.stem
            artist = "Unknown"

            track_id = db.insert_track(title, artist, duration)
            db.insert_fingerprint(track_id, fingerprint)

            processed += 1
        except Exception as e:
            print(f"  Error processing {audio_file.name}: {e}")
            errors += 1

    # Count tracks in DB
    with sqlite3.connect(db.db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]

    print("\nIngestion complete:")
    print(f"  Processed: {processed}")
    print(f"  Errors: {errors}")
    print(f"  Total songs in DB: {count}")

if __name__ == "__main__":
    ingest_songs()
