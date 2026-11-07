#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify the camera source lock, adaptations and release identities."""
import hashlib
import json
from pathlib import Path
import urllib.request

repo = Path(__file__).resolve().parents[2]
root = repo / 'custom/libcamera'
lock = json.loads((root / 'source-lock.json').read_text())
version = json.loads((repo / 'custom/version.json').read_text())['version']
for entry in lock['files']:
    path = entry['path']
    url = f"https://raw.githubusercontent.com/{lock['repository']}/{lock['commit']}/{lock['source_directory']}/{path}"
    with urllib.request.urlopen(url, timeout=60) as response:
        original = response.read()
    assert hashlib.sha256(original).hexdigest() == entry['sha256'], path + ': source drift'
    local = (root / path).read_bytes()
    assert hashlib.sha256(local).hexdigest() == entry.get('local_sha256', entry['sha256']), path + ': local drift'
for script in ['libcamera-af-build.sh', 'libcamera-af-install.sh']:
    assert 'NEW=$VER+san' + version in (root / script).read_text(), script + ': version drift'
print('PASS: five autofocus/lens-power patches and three adapted scripts match the lock')
