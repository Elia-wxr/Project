"""Write the package version into _version.py (used by CI builds).

Every commit build passes the git commit hash (PEP 440 local version, e.g.
0.1.0+g1a2b3c4d); tag builds pass the tag name (e.g. 0.1.0).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

VERSION_FILE = Path("src/tarot_jupyterlab/_version.py")

#: A strict PEP 440 shape; the hash is a local version segment.
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*(?:\+[0-9A-Za-z.]+)?$")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set the package version in _version.py.")
    parser.add_argument("version", help="PEP 440 version to write.")
    args = parser.parse_args()
    version = args.version.strip()
    if not _VERSION_RE.fullmatch(version):
        parser.error(f"Invalid PEP 440 version: {version!r}")
    header = (
        "\"\"\"Package version.\n\n"
        "Computed by the CI build: the git tag for releases, or the git\n"
        "commit hash for development builds.\n"
        "\"\"\"\n\n"
    )
    content = header + f"__version__ = \"{version}\"\n"
    VERSION_FILE.write_text(content, encoding="utf-8")
    print(f"Wrote version {version} to {VERSION_FILE}")


if __name__ == "__main__":
    main()
