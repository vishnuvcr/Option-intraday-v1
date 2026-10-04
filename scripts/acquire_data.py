from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
HF_ROOT = CACHE / "hf_options"
SPOT_ROOT = CACHE / "spot"
MANIFEST = CACHE / "acquisition_manifest.json"

HF_REPO = "rissin/nse-options-intraday"
HF_REVISION = "78b1c5468255d18cf492984bfe6fe4e3ac874d7c"
HF_FILES = {
    "upstox_2024": "upstox_intraday/NIFTY/NIFTY_2024.parquet",
    "upstox_2025": "upstox_intraday/NIFTY/NIFTY_2025.parquet",
}
SPOT_RELEASE_URL = "https://github.com/voletiramu/nse-fno-1min-data/releases/download/indices-v1.0.0/nifty_indices_5yr.zip"
EXPECTED_SPOT_SHA256 = "0c1f3de848a4e8c05e233c195685e7ae560d56d08df8baba8b2ffcfac699d3f8"

def sha256(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()

def download_spot() -> Path:
    SPOT_ROOT.mkdir(parents=True, exist_ok=True)
    zip_path = SPOT_ROOT / "nifty_indices_5yr.zip"
    if not zip_path.exists():
        req = Request(SPOT_RELEASE_URL, headers={"User-Agent": "Option-intraday-v1/1.0"})
        with urlopen(req, timeout=120) as r, zip_path.open("wb") as out:
            shutil.copyfileobj(r, out)
    digest = sha256(zip_path)
    if digest != EXPECTED_SPOT_SHA256:
        raise RuntimeError(f"Spot release SHA-256 mismatch: {digest}")
    extracted = SPOT_ROOT / "extracted"
    extracted.mkdir(exist_ok=True)
    target = extracted / "NIFTY_5min_5yr_2021_2026.csv"
    if not target.exists():
        with zipfile.ZipFile(zip_path) as zf:
            members = [n for n in zf.namelist() if n.endswith("NIFTY_5min_5yr_2021_2026.csv")]
            if not members:
                raise FileNotFoundError("NIFTY 5-minute spot CSV not found in release archive")
            zf.extract(members[0], extracted)
            extracted_member = extracted / members[0]
            if extracted_member != target:
                extracted_member.rename(target)
    return target

def download_options() -> list[Path]:
    HF_ROOT.mkdir(parents=True, exist_ok=True)
    token = os.getenv("HF_TOKEN") or None
    downloaded = snapshot_download(
        repo_id=HF_REPO,
        repo_type="dataset",
        allow_patterns=list(HF_FILES.values()),
        revision=HF_REVISION,
        local_dir=str(HF_ROOT),
        token=token,
    )
    base = Path(downloaded)
    paths = [base / rel for rel in HF_FILES.values()]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing option files: " + ", ".join(missing))
    return paths

def main() -> None:
    option_paths = download_options()
    spot_path = download_spot()
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "options": {
            "repo_id": HF_REPO,
            "revision": HF_REVISION,
            "files": [{"track": track, "source_path": source_path, "path": str((Path(HF_ROOT) / source_path).relative_to(ROOT)), "sha256": sha256(Path(HF_ROOT) / source_path), "bytes": (Path(HF_ROOT) / source_path).stat().st_size} for track, source_path in HF_FILES.items()],
        },
        "spot": {
            "release_url": SPOT_RELEASE_URL,
            "tag": "indices-v1.0.0",
            "asset_sha256": EXPECTED_SPOT_SHA256,
            "file": str(spot_path.relative_to(ROOT)),
            "bytes": spot_path.stat().st_size,
        },
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
