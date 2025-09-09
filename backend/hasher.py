import hashlib
import json
from typing import List, Dict, Any

def parse_chromaprint_fingerprint(fpcalc_output: str) -> List[int]:
    """Parse fpcalc JSON output and return raw fingerprint array."""
    try:
        data = json.loads(fpcalc_output)
        # fpcalc returns base64-encoded fingerprint, we need the raw array
        # For simplicity, we'll use a basic approach with the duration and fingerprint string
        fingerprint_str = data.get('fingerprint', '')
        
        # Simple hash-based approach: convert fingerprint string to numeric values
        # In production, you'd decode the base64 and work with the actual values
        hash_values = []
        for i in range(0, len(fingerprint_str), 8):
            chunk = fingerprint_str[i:i+8]
            hash_val = hash(chunk) % (2**31)  # Simple hash to positive int
            hash_values.append(hash_val)
        
        return hash_values
    except (json.JSONDecodeError, KeyError):
        return []

def generate_hashes(fingerprint_values: List[int], window_size: int = 5) -> List[Dict[str, Any]]:
    """Generate hashes from fingerprint values using sliding window."""
    if len(fingerprint_values) < window_size:
        return []
    
    hashes = []
    for i in range(len(fingerprint_values) - window_size + 1):
        # Take a window of values
        window = tuple(fingerprint_values[i:i + window_size])
        
        # Create hash from window
        hash_str = hashlib.md5(str(window).encode()).hexdigest()[:16]
        
        # Time offset (approximate seconds, assuming each value is ~0.1 seconds)
        time_offset = i * 0.1
        
        hashes.append({
            'hash': hash_str,
            'time_offset': time_offset
        })
    
    return hashes

def generate_query_hashes(fpcalc_output: str) -> List[str]:
    """Generate query hashes from fpcalc output - returns just the hash strings."""
    fingerprint_values = parse_chromaprint_fingerprint(fpcalc_output)
    hash_objects = generate_hashes(fingerprint_values)
    return [h['hash'] for h in hash_objects]
