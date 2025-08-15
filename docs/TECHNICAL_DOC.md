# EOL / EOS Scanner — Technical Documentation

## Purpose
Identify **EOL/EOS risk** across technologies used in a repo (runtimes & base OS), and optionally surface package **staleness**.

## Data sources
- **endoflife.date** JSON families (python, nodejs, ubuntu, debian, alpine, rocky-linux, rhel, …)
- **GitHub SBOM**: `GET /repos/{owner}/{repo}/dependency-graph/sbom` (optional, recommended)
- **Fallback parsing**: `.python-version`, `.nvmrc`, `.node-version`, `Dockerfile`, `package.json > engines.node`,
  plus room to parse `requirements.txt`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`.

## Detection logic
1. **Discover** versions via SBOM or fallback parsers.  
2. **Map** to endoflife.date slugs (e.g., `python→python`, `node→nodejs`, `rockylinux→rocky-linux`).  
3. **Lookup** the cycle in the family JSON and read `eol`.  
4. **Classify** status: `EOL`, `Near EOL` (within `near_months`), `Supported`, or `Unknown`.  
5. **Staleness** (optional): last release age for PyPI/npm packages; mark “Potentially unmaintained” if ≥ 24 months.

## Modes
- **repo**: Try SBOM; if not available, **zipball fallback** downloads and scans files.  
- **path**: Scan a local folder directly.

## Permissions
- Enable repo **Dependency graph** (Settings → Code security and analysis).  
- Fine-grained PAT with **Contents: Read** and **Dependency graph: Read**. Pass as `--token` or env `GITHUB_TOKEN`.

## Output schema (runtimes/OS)
- `type` = "runtime"
- `name`, `version`, `status`, `eol_date`, `days_to_eol`, `latest`

Packages (staleness):
- `type` = "package", `ecosystem`, `name`, `status`, `last_release`, `days_since_release`

## Extensibility
- Add new runtimes by extending slug map and parsers.  
- Parse lockfiles for complete dependency inventory.  
- Emit markdown/HTML report; fail CI when EOL found; PR comments with upgrade tips.

## Security
- Least-privilege PAT, short expiry.  
- No tokens written to logs or repo.  
- Network calls only to GitHub, endoflife.date, PyPI/npm.

## QA ideas
- Golden-file tests on sample repos.
- SBOM vs fallback parity tests.
- Threshold sensitivity tests (`near_months`).
