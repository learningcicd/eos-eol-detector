# from the repo you want to scan (not the scanner repo)
mkdir -p "$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc  # persist for next shells

# install syft into your home (no sudo)
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh \
| sh -s -- -b "$HOME/.local/bin"

# verify
which syft
syft version

# create reports directory if it doesn't exist
mkdir -p reports

# generate an SPDX JSON SBOM in the reports folder
syft dir:. -o spdx-json > reports/sbom.spdx.json

# confirm the file exists
ls -lh reports/sbom.spdx.json