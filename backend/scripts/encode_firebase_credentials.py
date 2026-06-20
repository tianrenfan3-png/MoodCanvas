#!/usr/bin/env python3
"""Encode a Firebase service-account JSON file for Railway env vars."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path, help="Path to firebase service account JSON")
    args = parser.parse_args()

    data = args.json_path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    print("Set this in Railway as FIREBASE_CREDENTIALS_JSON_B64:")
    print(encoded)


if __name__ == "__main__":
    main()
