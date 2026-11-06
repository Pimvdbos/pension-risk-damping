"""Explicit acquisition only: importing or loading never downloads data."""

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

SOURCE_URL = "https://www.dnb.nl/voor-de-sector/open-boek-toezicht/sectoren/pensioenfondsen/dnb-publiceert-definitieve-scenariosets-bij-wet-toekomst-pensioenen/"
DOWNLOAD_URL = "https://www.dnb.nl/media/4xzlqaij/cp2022-p-scenarioset-20k-2026q2.xlsx"
RELEASE = "CP2022 P scenarioset 20K 2026Q2 (unshocked)"
FILENAME = "cp2022-p-scenarioset-20k-2026q2.xlsx"
KNOWN_SHA256 = "275a336f4bc121fcd2948f3c40e3bc4fd154e5279fcdee472e491720565c658b"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(destination=Path("data/raw") / FILENAME,
             manifest=Path("data/provenance.json")):
    """Download the specified vintage once; record facts from the actual response.

    Existing files are never silently overwritten or asserted to be new downloads.
    A changed upstream URL requires inspection of DNB's official page/archive.
    """
    destination, manifest = Path(destination), Path(manifest)
    if destination.exists():
        raise FileExistsError(f"Already present: {destination}. Use --workbook to load it.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".xlsx.part")
    request = Request(DOWNLOAD_URL, headers={"User-Agent": "pension-risk-damping/0.1 research"})
    try:
        # curl uses the host's TLS/network configuration; urllib is the portable fallback.
        curl = shutil.which("curl")
        if curl:
            response = subprocess.run(
                [curl, "--fail", "--location", "--silent", "--show-error",
                 "--max-time", "600", "--output", str(temporary),
                 "--write-out", "%{json}", DOWNLOAD_URL],
                check=True, capture_output=True, text=True,
            )
            details = json.loads(response.stdout)
            status, content_type = details["http_code"], details["content_type"]
            resolved_url = details["url_effective"]
        else:
            with urlopen(request, timeout=120) as response, temporary.open("wb") as output:
                status = response.status
                content_type = response.headers.get("Content-Type", "")
                resolved_url = response.url
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    output.write(block)
        if status != 200 or "spreadsheetml" not in content_type:
            raise ValueError(f"Unexpected download: HTTP {status}, {content_type}")
        with ZipFile(temporary) as archive:
            if "xl/workbook.xml" not in archive.namelist():
                raise ValueError("Response is not an XLSX workbook")
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    info = {
        "dataset": RELEASE, "release_date": "2026-04-14",
        "source_url": SOURCE_URL, "download_url": DOWNLOAD_URL,
        "resolved_download_url": resolved_url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": status, "content_type": content_type,
        "filename": destination.name, "file_size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "note": "Downloaded for this reconstruction; not the lost original local workbook.",
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info
