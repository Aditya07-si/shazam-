from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional
from .database import Database
from .hasher import generate_query_hashes

class AudioMatcher:
    def __init__(self, db: Database):
        self.db = db
    
    def find_best_match(self, fpcalc_output: str) -> Optional[Dict[str, Any]]:
        """Find the best matching song for given fpcalc output."""
        
        # Generate hashes from query
        query_hashes = generate_query_hashes(fpcalc_output)
        
        if not query_hashes:
            return None
        
        # Find all matches in database
        matches = self.db.find_matches(query_hashes)
        
        if not matches:
            return None
        
        # Group matches by song
        song_matches = defaultdict(list)
        for match in matches:
            song_matches[match['song_id']].append(match)
        
        # Score each song
        best_match = None
        best_score = 0
        
        for song_id, song_match_list in song_matches.items():
            score = self._calculate_score(song_match_list, len(query_hashes))
            
            if score > best_score:
                best_score = score
                # Get song info from first match
                first_match = song_match_list[0]
                best_match = {
                    'song_id': song_id,
                    'title': first_match['title'],
                    'artist': first_match['artist'],
                    'confidence': score,
                    'match_count': len(song_match_list)
                }
        
        # Only return matches with reasonable confidence
        if best_match and best_match['confidence'] > 0.1:
            return best_match
        
        return None
    
    def _calculate_score(self, matches: List[Dict[str, Any]], total_query_hashes: int) -> float:
        """Calculate confidence score for a song based on its matches."""
        if not matches:
            return 0.0
        
        # Basic scoring: ratio of matches to total query hashes
        match_ratio = len(matches) / total_query_hashes
        
        # Bonus for time alignment consistency
        time_deltas = []
        for i, match in enumerate(matches):
            query_time = i * 0.1  # Approximate query time
            db_time = match['time_offset']
            time_deltas.append(abs(query_time - db_time))
        
        # Reward consistent time alignment
        if time_deltas:
            avg_delta = sum(time_deltas) / len(time_deltas)
            time_consistency = max(0, 1 - avg_delta / 10)  # Normalize
        else:
            time_consistency = 0
        
        # Combined score
        score = (match_ratio * 0.7) + (time_consistency * 0.3)
        
        return min(1.0, score)  # Cap at 1.0

def match_fingerprint(query_fp, tracks, fps):
    """
    Very naive matching: looks for exact fingerprint string equality.
    Replace with smarter similarity later.
    """
    for (track_id, fp) in fps:
        if query_fp == fp:
            for (tid, title, artist, duration) in tracks:
                if tid == track_id:
                    return {
                        "title": title,
                        "artist": artist,
                        "duration": duration,
                        "match_type": "exact"
                    }
    return
