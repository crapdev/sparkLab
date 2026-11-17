#!/usr/bin/env python3
"""Point the lab notebooks at the published site.

The site URL lives in site.config.json. This script updates it and regenerates
every notebook, so Colab downloads the datasets from <site>/data.

Usage:
    python scripts/set-data-url.py https://pyspark-labs.vercel.app
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "site.config.json"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    site_url = sys.argv[1].rstrip("/")
    if site_url.endswith("/data"):
        site_url = site_url[: -len("/data")]
    parsed = urlparse(site_url)
    if parsed.scheme != "https" or not parsed.netloc:
        print(f"Not a valid https URL: {sys.argv[1]}", file=sys.stderr)
        return 1

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config["siteUrl"] = site_url
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"siteUrl = {site_url}")

    return subprocess.run([sys.executable, str(ROOT / "scripts" / "build-labs.py")]).returncode


if __name__ == "__main__":
    sys.exit(main())
