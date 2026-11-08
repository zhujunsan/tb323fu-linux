#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stage checked outputs in an existing draft; never publish the release."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

def stage(repo, environment, check_only=False):
    version = json.loads((repo / 'custom/version.json').read_text())
    expected = 'san-v' + version['version'] + '-' + version['upstream_kernel']
    tag = environment['RELEASE_TAG']
    assert tag == expected and re.fullmatch(r'san-v\d+\.\d+\.\d+-t\d+', tag), 'Unexpected tag'
    repository = environment['GITHUB_REPOSITORY']
    release = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repository}/releases/tags/{tag}']))
    assert release['draft'], 'Only an existing draft may receive build outputs'
    assert release['target_commitish'] == environment['GITHUB_SHA'], 'Draft/CI source mismatch'
    if check_only:
        print('Draft source identity checked')
        return
    assets = repo / 'out/build-san-flavored/artifacts'
    for line in (assets / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split(None, 1)
        path = assets / name.strip()
        assert path.parent == assets and hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    stage = repo / 'out/release-stage'
    stage.mkdir(exist_ok=False)
    kernel = stage / ('Image-tb323fu-' + version['upstream_kernel'] + '.gz')
    shutil.copyfile(assets / 'Image.gz', kernel)
    archive = stage / 'kernel-artifacts.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for path in sorted(assets.iterdir()):
            tar.add(path, arcname=path.name)
    sums = stage / 'kernel-SHA256SUMS'
    sums.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n'
                            for p in [kernel, archive]))
    subprocess.run(['gh', 'release', 'upload', tag, str(kernel), str(archive), str(sums),
                    '--repo', repository], check=True)
    print('Verified kernel staged in draft; publication remains a separate step')


if __name__ == '__main__':
    stage(Path(__file__).resolve().parents[2], os.environ, '--check' in sys.argv[1:])
