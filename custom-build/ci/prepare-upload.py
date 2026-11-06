#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Keep this repository's CI artifacts bounded without deleting prior builds.

Only san-flavored ships a full archive. Baseline keeps diagnostics. If storage
cannot be checked or the soft budget is exhausted, build logs remain on Actions.
This repository cap is not an account-wide billing/budget setting.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

REPO = Path(__file__).resolve().parents[2]
BUDGET = 400 * 1024**2
MAX_ARCHIVE = 100 * 1024**2
RESERVE = 2 * 1024**2  # Other profile's small diagnostic upload.


def main():
    profile, result = sys.argv[1:]
    if profile not in {'baseline', 'san-flavored'}:
        raise SystemExit('Unknown profile')
    work = REPO / 'out' / f'build-{profile}'
    output = REPO / 'out' / f'upload-{profile}'
    # Each CI checkout is fresh; never silently package stale files.
    output.mkdir(parents=True, exist_ok=False)
    upload = False
    note = ''
    try:
        response = subprocess.check_output([
            'gh', 'api', '--paginate', '--slurp',
            f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/artifacts?per_page=100",
        ], text=True, stderr=subprocess.PIPE)
        used = sum(a['size_in_bytes'] for page in json.loads(response)
                   for a in page['artifacts'] if not a['expired'])
        for source in ['build.log', 'kout/.config', 'selected-patches.txt',
                       'artifacts/ccache-stats.txt', 'artifacts/kernelrelease.txt']:
            path = work / source
            if path.is_file():
                shutil.copyfile(path, output / ('config' if path.name == '.config' else path.name))
        if profile == 'san-flavored' and result == 'success':
            archive = output / 'kernel-artifacts.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                for path in sorted((work / 'artifacts').iterdir()):
                    tar.add(path, arcname=path.name)
            if archive.stat().st_size > MAX_ARCHIVE or used + archive.stat().st_size + RESERVE > BUDGET:
                archive.unlink()  # Only this job's newly generated archive.
                note = 'Full archive omitted: 100 MiB archive / 400 MiB repository storage guard.'
        size = sum(p.stat().st_size for p in output.iterdir())
        upload = size > 0 and used + size + RESERVE <= BUDGET
        note = note or f'Artifact storage before this job: {used / 1024**2:.1f} MiB; prepared {size / 1024**2:.1f} MiB.'
    except (subprocess.CalledProcessError, KeyError, ValueError) as exc:
        note = f'Artifact upload skipped: storage usage could not be verified ({type(exc).__name__}).'
    with open(os.environ['GITHUB_OUTPUT'], 'a') as handle:
        handle.write(f'upload={str(upload).lower()}\n')
    if not upload:
        note += ' Diagnostics remain in the job log.'
    print(note)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as handle:
            handle.write(f'### {profile} artifact policy\n\n{note}\n')


if __name__ == '__main__':
    main()
