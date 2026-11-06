"""Portable explicit download entry point; run after installing the package."""
import argparse
from pathlib import Path
from pension_risk.acquisition import FILENAME, download

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/raw") / FILENAME)
    parser.add_argument("--manifest", type=Path, default=Path("data/provenance.json"))
    args = parser.parse_args()
    print(download(args.output, args.manifest))
