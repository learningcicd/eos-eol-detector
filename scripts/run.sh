python -m venv .venv && source .venv/bin/activate

# 1) Generate the SBOM (SPDX JSON)
chmod +x scripts/gen_sbom.sh
./scripts/gen_sbom.sh   # creates reports/sbom.spdx.json

# 2) Scan using the SBOM
# python -m eolscan.cli path --dir . --sbom reports/sbom.spdx.json --near-months 6 --table
# # or dump JSON
python -m eolscan.cli path --dir . --sbom reports/sbom.spdx.json --out reports/eol-report.json
