#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Print selected, hash-verified local patches in the canonical series order."""
import hashlib
import json
import os
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
root = repo / 'custom/patches'
lock = json.loads((repo / 'custom/manifests/sources.json').read_text())
series = [line.strip() for line in (root / 'series').read_text().splitlines()
          if line.strip() and not line.lstrip().startswith('#')]
if len(series) != len(set(series)):
    raise SystemExit('Duplicate patch in series')
records = {c['local_patch']: c for c in lock['candidates'] if 'local_patch' in c}
if set(series) != set(records):
    raise SystemExit('Series and imported manifest records disagree')
requested = os.environ.get('PATCH_IDS')
selected = ({i.strip() for i in requested.split(',') if i.strip()}
            if requested is not None else
            {c['id'] for c in records.values() if c['enabled']})
unknown = selected - {c['id'] for c in records.values()}
if unknown:
    raise SystemExit(f'Unknown/unimported patch IDs: {sorted(unknown)}')
for path in series:
    candidate = records[path]
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise SystemExit('Patch path escapes patch directory')
    if hashlib.sha256(target.read_bytes()).hexdigest() != candidate.get('local_sha256', candidate['sha256']):
        raise SystemExit(f'Patch checksum mismatch: {path}')
    if candidate['id'] in selected:
        print(target)
