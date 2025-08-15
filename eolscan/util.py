import re, datetime as dt
from dateutil import parser as dtp

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
