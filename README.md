# EOL / EOS Scanner (CLI)

A Python CLI that scans a **GitHub repository** or a **local folder** and flags
**End-of-Life (EOL)** / **End-of-Support (EOS)** risks across runtimes (Python, Node.js, etc.)
and OS base images (Ubuntu, Debian, Alpine). It also provides a lightweight package **staleness** signal.

> Uses [endoflife.date](https://endoflife.date/) for authoritative EOL schedules.
> Works with **SBOM** (GitHub Dependency Graph) or **zipball/local fallback**.

## Quick start
```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Scan a GitHub repo (SBOM if available; requires PAT with Contents: Read + Dependency graph: Read)
python -m eolscan.cli repo --repo owner/name --near-months 6 --token $GITHUB_TOKEN --out report.json

# Or scan a local path (Dockerfile / .python-version / .nvmrc / requirements.txt / package.json)
python -m eolscan.cli path --dir /path/to/repo --near-months 6 --table
```

## Output example
```json
[
  {"type":"runtime","name":"Python","version":"3.9","status":"Near EOL","eol_date":"2025-10-01","days_to_eol":80,"latest":"3.12"},
  {"type":"runtime","name":"Ubuntu","version":"18.04","status":"EOL","eol_date":"2023-04-30","days_to_eol":-820}
]
```

## CLI reference
```
python -m eolscan.cli repo --repo owner/name [--ref main] [--token GITHUB_TOKEN] [--near-months 6] [--out file.json] [--table]
python -m eolscan.cli path --dir <folder> [--near-months 6] [--out file.json] [--table]
```

## Troubleshooting
- **“SBOM unavailable …”** → Enable **Dependency graph** in repo settings or use fallback/local scan.  
- **401/403** → Use a PAT with **Contents: Read** + **Dependency graph: Read**.  
- **Empty/Unknown results** → No detectable hints; scan local clone.

## Automation
Use the included GitHub Actions workflow to run nightly and upload `eol-report.json`.
