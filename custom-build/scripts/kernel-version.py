#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Independent custom identity with the upstream helper's trailing tNN ABI."""
import argparse
import json
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[2]


def localversion(version, upstream, build):
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        raise ValueError('Custom version must be MAJOR.MINOR.PATCH')
    if not re.fullmatch(r't[1-9][0-9]*', upstream):
        raise ValueError('Upstream identity must be tNN')
    if not re.fullmatch(r'[0-9]+\.[0-9]+', build):
        raise ValueError('Build identity must be RUN.ATTEMPT')
    result = f'-san-v{version}-b{build}-tb323fu-{upstream}'
    if len('7.3.0' + result) > 64:
        raise ValueError('Kernel release exceeds the 64-byte UTS limit')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('build')
    args = parser.parse_args()
    version = json.loads((REPO / 'custom/version.json').read_text())
    lock = json.loads((REPO / 'custom/manifests/sources.json').read_text())
    if 'kernel-' + version['upstream_kernel'] != lock['baseline_reference']['release']:
        raise SystemExit('Custom version and upstream baseline reference disagree')
    print(localversion(version['version'], version['upstream_kernel'], args.build))


if __name__ == '__main__':
    main()
