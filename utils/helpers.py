import re

def extract_movie_code(text: str) -> str:
    """Extract movie code from text using regex pattern"""
    patterns = [
        r'(?:kod[: ]?)(\d+)',
        r'#(\d+)',
        r'kod[: ]?(\d+)',
        r'(\d{3,})'  # Fallback for 3+ digit numbers
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1)
    
    return None