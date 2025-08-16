import json, base64, re
from pathlib import Path
import requests

# ------------------- GitHub SBOM (kept as-is) -------------------
def fetch_github_sbom(owner_repo: str, token: str = None):
    owner, name = owner_repo.split("/", 1)
    url = f"https://api.github.com/repos/{owner}/{name}/dependency-graph/sbom"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "eol-eos-scanner"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:120]}"
    data = r.json()
    spdx_b64 = (data.get("sbom", {}) or {}).get("spdx")
    if not spdx_b64:
        return None, "No SBOM content"
    try:
        content = base64.b64decode(spdx_b64).decode("utf-8", "ignore")
        return content, None
    except Exception as e:
        return None, f"Decode error: {e}"

# ------------------- Local SBOM parsing (NEW) -------------------
def parse_local_sbom(path: str | Path):
    """
    Returns a list of {'name': str, 'version': str} components
    from an SPDX JSON or CycloneDX JSON file.
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    # SPDX JSON?
    if isinstance(data, dict) and ("spdxVersion" in data or data.get("$schema","").find("spdx") != -1):
        comps = []
        for pkg in data.get("packages", []) or []:
            name = pkg.get("name")
            ver = pkg.get("versionInfo") or pkg.get("version") or ""
            if name:
                comps.append({"name": name, "version": ver})
        return comps

    # CycloneDX JSON?
    if str(data.get("bomFormat", "")).lower() == "cyclonedx":
        comps = []
        for c in data.get("components", []) or []:
            name = c.get("name")
            ver = c.get("version") or ""
            if name:
                comps.append({"name": name, "version": ver})
        return comps

    raise ValueError("Unknown SBOM format: expected SPDX JSON or CycloneDX JSON")

# Heuristics to detect runtimes/OS among components
_RUNTIME_PATTERNS = [
    ("python", re.compile(r"(^python$|^cpython$|python\b)", re.I)),
    ("nodejs", re.compile(r"(^node$|^node\.?js$|nodejs)", re.I)),
    ("ubuntu", re.compile(r"\bubuntu\b", re.I)),
    ("debian", re.compile(r"\bdebian\b", re.I)),
    ("alpine", re.compile(r"\balpine\b", re.I)),
    ("rocky-linux", re.compile(r"\brockylinux|rocky\b", re.I)),
    ("rhel", re.compile(r"\brhel\b|\bred hat\b", re.I)),
]

def runtime_hits(components):
    """
    From [{'name','version'}] → [{'slug','name','version'}] for runtimes/OS.
    """
    hits = []
    for comp in components:
        n = (comp.get("name") or "").strip()
        v = (comp.get("version") or "").strip()
        for slug, pat in _RUNTIME_PATTERNS:
            if pat.search(n):
                norm_name = {"python":"Python", "nodejs":"Node.js"}.get(slug, n.title())
                hits.append({"slug": slug, "name": norm_name, "version": v})
                break
    return hits
