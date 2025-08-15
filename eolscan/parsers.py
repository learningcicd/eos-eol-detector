import json, re
from pathlib import Path

def read_text(p):
    try: return Path(p).read_text(errors="ignore")
    except Exception: return ""

def find_python_version(root: Path):
    p = Path(root)/".python-version"
    if p.exists(): return p.read_text().strip()
    docker = Path(root)/"Dockerfile"
    if docker.exists():
        m = re.search(r"FROM\s+python:(\d+(\.\d+)*)", read_text(docker), re.IGNORECASE)
        if m: return m.group(1)
    pyproject = Path(root)/"pyproject.toml"
    if pyproject.exists():
        m = re.search(r'python\s*=\s*"[^\d]*(\d+(\.\d+)*)', read_text(pyproject))
        if m: return m.group(1)
    return None

def find_node_version(root: Path):
    for fname in [".nvmrc",".node-version"]:
        p = Path(root)/fname
        if p.exists(): return p.read_text().strip().lstrip("v")
    docker = Path(root)/"Dockerfile"
    if docker.exists():
        m = re.search(r"FROM\s+node:(\d+(\.\d+)*)", read_text(docker), re.IGNORECASE)
        if m: return m.group(1)
    pkgjson = Path(root)/"package.json"
    if pkgjson.exists():
        try:
            data = json.loads(read_text(pkgjson) or "{}")
            node = (data.get("engines",{}) or {}).get("node")
            if node:
                m = re.search(r"(\d+(\.\d+)*)", node)
                if m: return m.group(1)
        except Exception: pass
    return None

def find_os_from_docker(root: Path):
    docker = Path(root)/"Dockerfile"
    if not docker.exists(): return None
    text = read_text(docker)
    m = re.search(r"FROM\s+(ubuntu|debian|alpine|centos|rockylinux|rhel):([\w\.\-]+)", text, re.IGNORECASE)
    if not m: return None
    name = m.group(1).lower(); ver = m.group(2)
    if name=="rockylinux": name="rocky"
    return name, ver
