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

# generate an SPDX JSON SBOM in the current repo
syft dir:. -o spdx-json > sbom.spdx.json

# confirm the file exists
ls -lh sbom.spdx.json