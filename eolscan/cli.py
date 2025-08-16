import argparse, json, os, sys, io, zipfile, tempfile, requests
from pathlib import Path
from tabulate import tabulate

from .parsers import find_python_version, find_node_version, find_os_from_docker
from .eol_data import EOL_SLUGS, assess
from .pypi_npm import pypi_last_release, npm_last_release, stale_status
from .sbom import fetch_github_sbom, parse_local_sbom, runtime_hits
from .eol_data import EOL_SLUGS, assess

def assess_from_components(components, near_months):
    out = []
    for hit in runtime_hits(components):
        out.append(assess(hit["slug"], hit["name"], hit["version"], near_months))
    return out

def scan_path(path: Path, near_months=6, sbom_path: str | None = None):
    results = []
    if sbom_path:
        comps = parse_local_sbom(sbom_path)
        results.extend(assess_from_components(comps, near_months))
        return results

    py_ver = find_python_version(path)
    if py_ver:
        results.append(assess(EOL_SLUGS["python"], "Python", py_ver, near_months))

    node_ver = find_node_version(path)
    if node_ver:
        results.append(assess(EOL_SLUGS["node"], "Node.js", node_ver, near_months))

    os_info = find_os_from_docker(path)
    if os_info:
        os_name, os_version = os_info
        slug = EOL_SLUGS.get(os_name, os_name)
        results.append(assess(slug, os_name.title(), os_version, near_months))

    # Optional lightweight “stale lib” signals
    req = path / "requirements.txt"
    if req.exists():
        for line in req.read_text(errors="ignore").splitlines():
            if "==" in line and not line.strip().startswith("#"):
                pkg = line.split("==")[0].strip()
                last = pypi_last_release(pkg)
                status = stale_status(last, months_stale=24)
                if status:
                    results.append({
                        "type":"package","ecosystem":"PyPI","name":pkg,"version":None,
                        "status":status[0],"last_release":last,"days_since_release":-status[1]
                    })

    pkgjson = path / "package.json"
    if pkgjson.exists():
        last = npm_last_release("express")  # placeholder; expand to parse all deps if desired
        if last:
            status = stale_status(last, months_stale=24)
            if status:
                results.append({
                    "type":"package","ecosystem":"npm","name":"(example) express","version":None,
                    "status":status[0],"last_release":last,"days_since_release":-status[1]
                })
    return results

def _headers(token: str | None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "eol-eos-scanner"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def _download_repo_to_temp(owner_repo: str, ref: str | None, token: str | None) -> Path:
    owner, name = owner_repo.split("/", 1)
    if not ref:
        r = requests.get(f"https://api.github.com/repos/{owner}/{name}", headers=_headers(token), timeout=30)
        r.raise_for_status()
        ref = r.json().get("default_branch", "main")
    url = f"https://api.github.com/repos/{owner}/{name}/zipball/{ref}"
    r = requests.get(url, headers=_headers(token), timeout=180)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    tmpdir = Path(tempfile.mkdtemp(prefix="repo_"))
    z.extractall(tmpdir)
    roots = list(tmpdir.glob("*"))
    return roots[0] if roots else tmpdir

def scan_repo(owner_repo: str, ref: str | None = None, token: str | None = None, near_months: int = 6):
    # 1) Try SBOM first
    spdx, err = fetch_github_sbom(owner_repo, token)
    if spdx:
        out = []
        name = None; version = None
        for line in spdx.splitlines():
            if line.strip().startswith("PackageName:"):
                name = line.split(":",1)[1].strip()
            if line.strip().startswith("PackageVersion:"):
                version = line.split(":",1)[1].strip()
                low = (name or "").lower()
                if "python" in low:
                    out.append(assess(EOL_SLUGS["python"], "Python", version, near_months))
                if low in ("node","nodejs") or "node.js" in low:
                    out.append(assess(EOL_SLUGS["node"], "Node.js", version, near_months))
                name = None; version = None
        if out:
            return out
        # fall through if SBOM had no useful entries

    # 2) Fallback: download zipball and run path scanners
    try:
        root = _download_repo_to_temp(owner_repo, ref, token)
        out = scan_path(root, near_months=near_months)
        # out.insert(0, {"type":"note","message":"SBOM unavailable; used zipball fallback."})
        return out
    except requests.HTTPError as e:
        msg = ""
        try:
            msg = e.response.json().get("message","")
        except Exception:
            msg = e.response.text
        return [{"type":"note","message": f"Zipball fallback failed (HTTP {e.response.status_code}): {msg}"}]
    except Exception as e:
        return [{"type":"note","message": f"Zipball fallback failed: {e}"}]

def main():
    ap = argparse.ArgumentParser(prog="eol-scan", description="EOL/EOS scanner for repos or local paths")
    sub = ap.add_subparsers(dest="cmd")

    p1 = sub.add_parser("path", help="Scan a local directory")
    p1.add_argument("--dir", required=True)
    p1.add_argument("--sbom", default=None, help="Path to a local SBOM (SPDX/CycloneDX JSON)")
    p1.add_argument("--near-months", type=int, default=6)
    p1.add_argument("--out")
    p1.add_argument("--table", action="store_true")

    p2 = sub.add_parser("repo", help="Scan a GitHub repo (SBOM, then zip fallback)")
    p2.add_argument("--repo", required=True)
    p2.add_argument("--sbom", default=None, help="Path to a local SBOM (SPDX/CycloneDX JSON)")
    p2.add_argument("--ref", default=None)
    p2.add_argument("--token", default=os.getenv("GITHUB_TOKEN"))
    p2.add_argument("--near-months", type=int, default=6)
    p2.add_argument("--out")
    p2.add_argument("--table", action="store_true")

    args = ap.parse_args()
    if args.cmd == "path":
        res = scan_path(Path(args.dir), near_months=args.near_months, sbom_path=args.sbom)
    elif args.cmd == "repo":
        if args.sbom:
            comps = parse_local_sbom(args.sbom)
            res = assess_from_components(comps, args.near_months)
        else:
            res = scan_repo(args.repo, args.ref, args.token, near_months=args.near_months)
    else:
        ap.print_help(); sys.exit(1)

    if args.table:
        headers = sorted({k for r in res for k in r.keys()})
        rows = [[r.get(h,"") for h in headers] for r in res]
        print(tabulate(rows, headers=headers, tablefmt="github"))
    else:
        print(json.dumps(res, indent=2))

    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
