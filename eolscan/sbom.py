import requests, base64

def fetch_github_sbom(owner_repo: str, token: str=None):
    owner, name = owner_repo.split("/",1)
    url = f"https://api.github.com/repos/{owner}/{name}/dependency-graph/sbom"
    headers={"Accept":"application/vnd.github+json","User-Agent":"eol-eos-scanner"}
    if token: headers["Authorization"]=f"Bearer {token}"
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code!=200: return None, f"HTTP {r.status_code}: {r.text[:120]}"
    data = r.json(); spdx_b64 = (data.get("sbom",{}) or {}).get("spdx")
    if not spdx_b64: return None, "No SBOM content"
    try:
        return base64.b64decode(spdx_b64).decode("utf-8","ignore"), None
    except Exception as e:
        return None, f"Decode error: {e}"
