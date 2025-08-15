import requests, datetime as dt

def pypi_last_release(pkg):
    try:
        r = requests.get(f"https://pypi.org/pypi/{pkg}/json", timeout=20)
        if r.status_code!=200: return None
        data = r.json(); releases = data.get("releases", {})
        latest=None
        for ver, files in releases.items():
            for f in files or []:
                ts = f.get("upload_time_iso_8601") or f.get("upload_time")
                if ts:
                    t = dt.datetime.fromisoformat(ts.replace("Z","+00:00"))
                    if (not latest) or t>latest: latest=t
        return latest.date().isoformat() if latest else None
    except Exception:
        return None

def npm_last_release(pkg):
    try:
        r = requests.get(f"https://registry.npmjs.org/{pkg}", timeout=20)
        if r.status_code!=200: return None
        data = r.json(); time = data.get("time", {})
        modified = time.get("modified") or time.get("created")
        return modified.split("T")[0] if modified else None
    except Exception:
        return None

def stale_status(last_release_date, months_stale=24):
    if not last_release_date: return None
    try: d = dt.date.fromisoformat(last_release_date)
    except Exception: return None
    delta = (dt.date.today() - d).days
    return ("Potentially unmaintained", -delta) if delta >= months_stale*30 else ("Maintained", -delta)
