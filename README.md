# EOL / EOS Scanner (CLI)

A Python CLI that scans a **GitHub repository** or a **local folder** and flags
**End-of-Life (EOL)** / **End-of-Support (EOS)** risks across runtimes (Python, Node.js, etc.)
and OS base images (Ubuntu, Debian, Alpine). It also provides a lightweight package **staleness** signal.

It works three ways:
1) **GitHub SBOM** (if Dependency graph is enabled).  
2) **Self‑generated SBOM** (SPDX/CycloneDX) — recommended if GitHub SBOM isn’t enabled.  
3) **File parsing** fallback (Dockerfile, `.python-version`, `.nvmrc`, `requirements.txt`, `package.json`).

## Install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```


## A) Use GitHub SBOM (if enabled)
Requirements: repo **Settings → Code security and analysis → Dependency graph = Enabled**, PAT with **Contents: Read** + **Dependency graph: Read**.
```bash
export GITHUB_TOKEN=ghp_xxx
python -m eolscan.cli repo --repo owner/name --near-months 6 --token "$GITHUB_TOKEN" --out report.json
```

---

## B) Generate your own SBOM (no GitHub feature needed)

### Linux/macOS (no sudo)
```bash
mkdir -p "$HOME/.local/bin"; export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b "$HOME/.local/bin"

cd /path/to/repo
syft dir:. -o spdx-json > sbom.spdx.json
```


---

## Scan with a local SBOM (`--sbom`)
```bash
python -m eolscan.cli path --dir . --sbom ./sbom.spdx.json --near-months 6 --table
# or
python -m eolscan.cli path --dir . --sbom ./sbom.cdx.json --out eol-report.json
```
> When `--sbom` is provided, no GitHub API is called.

---



## C) Parse files directly (no SBOM)
```bash
python -m eolscan.cli path --dir /path/to/repo --near-months 6 --table
```

---

## Output example
```json
[
  {"type":"runtime","name":"Python","version":"3.9","status":"Near EOL","eol_date":"2025-10-01","days_to_eol":80,"latest":"3.12"},
  {"type":"runtime","name":"Ubuntu","version":"18.04","status":"EOL","eol_date":"2023-04-30","days_to_eol":-820}
]
```

---

## Troubleshooting
- **Permission denied installing syft** → install to user bin (`$HOME/.local/bin`) and ensure PATH.  
- **`FileNotFoundError: sbom.spdx.json`** → generate the SBOM first and pass the correct path.  
- **`SBOM unavailable …` (repo mode)** → Dependency graph disabled or PAT lacks permission; use `--sbom` or path mode.  
- **401/403** → fine‑grained PAT with **Contents: Read** + **Dependency graph: Read**.

---

## CLI Reference
```
python -m eolscan.cli repo --repo owner/name [--ref main] [--token GITHUB_TOKEN] [--near-months 6] [--out file.json] [--table] [--sbom sbom.json]
python -m eolscan.cli path --dir <folder>   [--near-months 6] [--out file.json] [--table] [--sbom sbom.json]
```
