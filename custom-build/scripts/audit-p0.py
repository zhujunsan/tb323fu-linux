#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Reconstruct custom-stack-touched files; never a kernel build/boot test."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request

REPO = Path(__file__).resolve().parents[2]
LOCK = json.loads((REPO / 'custom/manifests/sources.json').read_text())


def download(repo, commit, path):
    with urllib.request.urlopen(
        f'https://raw.githubusercontent.com/{repo}/{commit}/{path}', timeout=90
    ) as response:
        return response.read()


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True)


def main():
    actual = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((REPO / 'kernel/patches').glob('*.patch'))}
    if actual != LOCK['upstream_patch_sha256']:
        raise SystemExit('Upstream patch set changed: review and update source lock first')
    with tempfile.TemporaryDirectory(prefix='tb323fu-audit-') as temp:
        root = Path(temp)
        tree = root / 'tree'
        tree.mkdir()
        candidates = []
        paths = set()
        for candidate in LOCK['candidates']:
            source = LOCK['downstream']
            data = download(source['repository'], source['commit'], candidate['path'])
            if hashlib.sha256(data).hexdigest() != candidate['sha256']:
                raise SystemExit(f"Checksum mismatch: {candidate['path']}")
            patch = root / Path(candidate['path']).name
            patch.write_bytes(data)
            paths.update(re.findall(r'^--- a/(.+)$', data.decode(), re.M))
            candidates.append((candidate['id'], patch))
        # Some device files are introduced by the upstream device series.
        introduced = set()
        for patch in (REPO / 'kernel/patches').glob('*.patch'):
            introduced.update(re.findall(r'^--- /dev/null\n\+\+\+ b/(.+)$',
                                         patch.read_text(encoding='utf-8'), re.M))
        for path in sorted(paths):
            target = tree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if path not in introduced:
                target.write_bytes(download('torvalds/linux', LOCK['linux']['commit'], path))
        # Apply only hunks touching these files, including all upstream changes
        # to them. This is a scoped source audit, not a full-series apply check.
        for patch in sorted((REPO / 'kernel/patches').glob('*.patch')):
            result = run('git', 'apply', *['--include=' + p for p in sorted(paths)],
                         str(patch), cwd=tree)
            if result.returncode:
                raise SystemExit(result.stderr)
        results = []
        for ident, patch in candidates:
            forward = run('git', 'apply', '--check', str(patch), cwd=tree)
            reverse = run('git', 'apply', '--check', '--reverse', str(patch), cwd=tree)
            results.append({'id': ident, 'forward_applies': forward.returncode == 0,
                            'reverse_applies': reverse.returncode == 0,
                            'forward_diagnostics': forward.stderr})
        # Independent checks above are diagnostic: later patches can depend
        # on earlier custom patches. Require the complete selected sequence.
        # patch-plan validates
        # local files against their original downstream checksums.
        import os
        env = dict(os.environ)
        env.pop('PATCH_IDS', None)
        plan = subprocess.run(['python3', str(REPO / 'custom-build/scripts/patch-plan.py')],
                              check=True, text=True, capture_output=True, env=env)
        selected = plan.stdout.splitlines()
        for patch in selected:
            applied = run('git', 'apply', patch, cwd=tree)
            if applied.returncode:
                raise SystemExit(applied.stderr)
        print(json.dumps({'scope': 'ordered stack on custom-touched files only; independent checks diagnostic',
                          'integrated_series_applies': [str(Path(p).relative_to(REPO)) for p in selected],
                          'results': results}, indent=2))
        if any(r['reverse_applies'] for r in results):
            raise SystemExit('Candidate may already be included: review required')


if __name__ == '__main__':
    main()
