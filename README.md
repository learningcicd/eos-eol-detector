# EOL / EOS Scanner (CLI)

A small Python CLI that scans a **GitHub repository** or a **local folder** and flags
**End-of-Life (EOL)** / **End-of-Support (EOS)** risks across runtimes (Python, Node.js, etc.)
and OS base images (Ubuntu, Debian, Alpine). It can also surface a lightweight signal for
**potentially unmaintained** packages.

---

## What it checks

- **Runtimes / languages**: Python, Node.js (more can be added easily)
- **Base OS from Dockerfile**: Ubuntu, Debian, Alpine, CentOS/Rocky/RHEL
- **Package “staleness” signals** (optional):
  - PyPI: last release date per package in `requirements.txt`
  - npm: example “express” release timestamp (placeholder; can be expanded to all deps)

> Determinations are made by joining detected versions to
> [endoflife.date](https://endoflife.date/), the canonical public EOL dataset.

---

## Requirements

- Python 3.9+  
- Internet access (to call endoflife.date and, optionally, GitHub/PyPI/npm)  
- Optional: GitHub **Personal Access Token (PAT)** for private repos or higher rate limits

Install dependencies:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Quick start

### Scan a GitHub repo (uses SBOM if available)

```bash
python -m eolscan.cli repo   --repo owner/name   --near-months 6   --token $GITHUB_TOKEN   --out report.json
```

### Scan a local path

```bash
python -m eolscan.cli path   --dir /path/to/repo   --near-months 6   --out report.json
```

Pretty table instead of JSON:

```bash
python -m eolscan.cli path --dir . --near-months 6 --table
```

---

## Detectors (how versions are found)

- **Python**: `.python-version`, `Dockerfile` (`FROM python:X.Y`), or `pyproject.toml` (Poetry `python = "^3.11"`).
- **Node.js**: `.nvmrc`, `.node-version`, `Dockerfile` (`FROM node:X.Y`), or `package.json > engines.node`.
- **Base OS**: `Dockerfile` (`FROM ubuntu:22.04`, `debian:11`, `alpine:3.18`, `rockylinux:8`, etc.).
- **Packages (optional)**:
  - PyPI: reads `requirements.txt` (`name==version`) and checks last release date.
  - npm: sample “express” check included as a placeholder (expandable to parse all deps/lockfiles).

---

## Output

Default is **JSON list**. Example (trimmed):

```json
[
  {
    "type": "runtime",
    "name": "Python",
    "version": "3.9",
    "status": "Near EOL",
    "eol_date": "2025-10-01",
    "days_to_eol": 80,
    "latest": "3.12"
  },
  {
    "type": "runtime",
    "name": "Ubuntu",
    "version": "18.04",
    "status": "EOL",
    "eol_date": "2023-04-30",
    "days_to_eol": -820
  },
  {
    "type": "package",
    "ecosystem": "PyPI",
    "name": "requests",
    "version": null,
    "status": "Potentially unmaintained",
    "last_release": "2021-06-15",
    "days_since_release": 1100
  }
]
```

Statuses:
- **Supported** – EOL date is beyond the `--near-months` horizon  
- **Near EOL** – within the next N months (default 6)  
- **EOL** – already past the EOL date  
- **Unknown** – could not determine version or dataset has no entry

---

## CLI reference

```
python -m eolscan.cli path --dir <folder> [--near-months 6] [--out file.json] [--table]
python -m eolscan.cli repo --repo owner/name [--ref main] [--token GITHUB_TOKEN] [--near-months 6] [--out file.json] [--table]
```

- `--near-months` : months before EOL to mark **Near EOL** (default: 6)
- `--token`       : GitHub PAT (only needed for private repos or to avoid rate limits)
- `--out`         : write the JSON result to a file
- `--table`       : print a pretty table instead of JSON

---

## GitHub PAT (what & why)

A **Personal Access Token** lets the scanner call GitHub APIs (e.g., to fetch a repo SBOM)
without hitting anonymous rate limits, and to read **private** repos.

Create (recommended fine-grained token):
1. GitHub → **Settings** → **Developer settings** → **Fine-grained tokens**  
2. Select the repo(s) and grant **Contents: Read** and **Dependency graph: Read**  
3. Set an expiration, create the token, and pass it as `--token` or set `GITHUB_TOKEN` env var.

You can revoke the token at any time.

---

## Notes & limitations

- Package-level EOL is not standardized; the **“potentially unmaintained”** signal is based on last release age (default 24 months).  
- For best accuracy on dependency inventories, enable **GitHub SBOM** on the repo.  
- Current runtime detectors cover Python & Node.js + common OS images; adding Java/Go/.NET is straightforward (map to endoflife.date slugs).

---

## Troubleshooting

- **Empty/Unknown** results: no detectable version hints (no `.python-version`, `.nvmrc`, `Dockerfile`, engines).  
- **SBOM unavailable**: GitHub dependency graph/SBOM not enabled for the repo or token lacks permission.  
- **401/403**: provide a valid PAT with read access.  
- **Windows**: use PowerShell activation: `. .venv\Scripts\Activate.ps1`.

---

## Roadmap

- Parse `poetry.lock`, `Pipfile.lock`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`  
- Detect more runtimes (Java, Go, .NET, PHP, Ruby, Rust) and frameworks  
- Export markdown/HTML report, GitHub PR comment, or failing CI check on EOL findings