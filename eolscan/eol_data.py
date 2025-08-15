import requests
from .util import status_from_eol, parse_semver
BASE = "https://endoflife.date/api"
EOL_SLUGS={"python":"python","node":"nodejs","nodejs":"nodejs","java":"java","go":"go","golang":"go","dotnet":"dotnet","ruby":"ruby","php":"php","rust":"rust","ubuntu":"ubuntu","debian":"debian","alpine":"alpine","centos":"centos","rocky":"rocky-linux","rhel":"rhel"}

def fetch_family(slug):
    r = requests.get(f"{BASE}/{slug}.json", timeout=30); r.raise_for_status(); return r.json()

def find_version_entry(entries, version):
    if not version: return None
    target = parse_semver(version)
    if not target: return None
    for e in entries:
        if str(e.get("cycle"))==target or str(e.get("releaseCycle"))==target: return e
    major = target.split(".")[0]
    for e in entries:
        if str(e.get("cycle")) in (target, major): return e
    return None

def assess(slug, name, version, near_months=6):
    try: entries = fetch_family(slug)
    except Exception as e: return {"type":"runtime","name":name,"version":version,"status":"Unknown","error":str(e)}
    entry = find_version_entry(entries, version)
    if not entry: return {"type":"runtime","name":name,"version":version,"status":"Unknown"}
    eol = entry.get("eol") or entry.get("support") or entry.get("end")
    status, days = status_from_eol(eol, near_months)
    latest = entries[0].get("latest") if entries else None
    return {"type":"runtime","name":name,"version":version,"status":status,"eol_date":eol,"days_to_eol":days,"latest":latest}
