import re, datetime as dt
from dateutil import parser as dtp
import logging
import os
from typing import Optional

def setup_logging(level: Optional[str] = None):
    """Setup logging configuration"""
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    # Create reports directory if it doesn't exist
    os.makedirs('reports', exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('reports/eol_scanner.log')
        ]
    )

def parse_semver(text):
    m = re.search(r"(\d+\.\d+(\.\d+)?)", text or "");
    return m.group(1) if m else None

def parse_date(s):
    if not s: return None
    try: return dtp.parse(s).date()
    except Exception: return None

def days_until(date_str):
    d = parse_date(date_str)
    if not d: return None
    return (d - dt.date.today()).days

def status_from_eol(eol_date, near_months=6):
    days = days_until(eol_date)
    if days is None: return "Unknown", None
    if days < 0: return "EOL", days
    if days <= near_months*30: return "Near EOL", days
    return "Supported", days

def validate_github_repo(repo: str) -> bool:
    """Validate GitHub repository format"""
    return bool(re.match(r'^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$', repo))

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"
