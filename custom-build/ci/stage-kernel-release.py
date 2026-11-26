#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Publish verified san-flavored outputs from a successful build."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from string import Template
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import quote


def read_json(path):
    return json.loads(path.read_text())


def release_notes(repo, version):
    notes = read_json(repo / 'custom/release-notes.json')
    for key in ('version', 'upstream_kernel'):
        if notes.get(key) != version[key]:
            raise SystemExit(f'Update custom/release-notes.json for {version["version"]}-{version["upstream_kernel"]}')
    for key in ('changes', 'known_issues'):
        items = notes.get(key)
        if not isinstance(items, list) or not items or not all(isinstance(item, str) and item.strip() for item in items):
            raise SystemExit(f'Release notes require a nonempty {key} list')
    if not isinstance(notes.get('device_validation'), str) or not notes['device_validation'].strip():
        raise SystemExit('Release notes require the device validation status')
    return notes


def render_notes(repo, version, notes, assets, repository, source, run_id, previous_tag):
    lock = read_json(repo / 'custom/manifests/sources.json')
    upstream = lock['upstream']
    upstream_url = f'https://github.com/{upstream["repository"]}'
    repo_url = f'https://github.com/{repository}'
    compare_link = ''
    if previous_tag:
        compare_link = f' · [与上次发布的提交差异]({repo_url}/compare/{quote(previous_tag, safe="")}...{source})'
    template = Template((repo / 'custom-build/ci/kernel-release-notes.md').read_text())
    return template.substitute(
        version=version['version'], upstream_kernel=version['upstream_kernel'],
        libcamera_version=version['libcamera_version'],
        changes='\n'.join(f'- {item}' for item in notes['changes']),
        known_issues='\n'.join(f'- {item}' for item in notes['known_issues']),
        device_validation=notes['device_validation'],
        upstream_release=lock['baseline_reference']['url'], upstream_commit_short=upstream['commit'][:7],
        upstream_commit_url=f'{upstream_url}/commit/{upstream["commit"]}',
        linux_version=lock['linux']['tag'], upstream_patch_count=len(lock['upstream_patch_sha256']),
        custom_patch_count=len((assets / 'selected-patches.txt').read_text().splitlines()),
        kernel_release=(assets / 'kernelrelease.txt').read_text().strip(),
        ci_url=f'{repo_url}/actions/runs/{run_id}', source_short=source[:7], source_url=f'{repo_url}/commit/{source}',
        compare_link=compare_link,
    )


def gh_json(*args):
    return json.loads(subprocess.check_output(['gh', *args], text=True))


def checksum(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def release_assets(repo, assets, stage, source, version):
    if (assets / 'project-commit.txt').read_text().strip() != source:
        raise SystemExit('Build outputs do not match the CI source commit')
    if read_json(assets / 'custom-version.json') != version:
        raise SystemExit('Build outputs do not match custom/version.json')
    if (assets / 'sources.json').read_bytes() != (repo / 'custom/manifests/sources.json').read_bytes():
        raise SystemExit('Build outputs do not match the source lock')
    checksums = {}
    for line in (assets / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        checksums[name] = digest
    files = {path.name: path for path in assets.iterdir() if path.name != 'SHA256SUMS'}
    if files.keys() != checksums.keys():
        raise SystemExit('Build output checksum mismatch')
    for name, path in files.items():
        if not path.is_file() or path.is_symlink() or checksum(path) != checksums[name]:
            raise SystemExit(f'Build output checksum mismatch for {name}')

    image = stage / f'Image-tb323fu-{version["upstream_kernel"]}.gz'
    shutil.copyfile(assets / 'Image.gz', image)
    archive = stage / 'kernel-artifacts.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for path in sorted(assets.iterdir()):
            tar.add(path, arcname=path.name)
    sums = stage / 'kernel-SHA256SUMS'
    sums.write_text(''.join(f'{checksum(path)}  {path.name}\n' for path in (image, archive)))
    return {path.name: path for path in (image, archive, sums)}


def tag_sources(repo, tags):
    refs = [ref for tag in tags for ref in (f'refs/tags/{tag}', f'refs/tags/{tag}^{{}}')]
    output = subprocess.check_output(['git', 'ls-remote', '--tags', 'origin', *refs], cwd=repo, text=True)
    found = {ref: commit for commit, ref in (line.split() for line in output.splitlines())}
    return {tag: found.get(f'refs/tags/{tag}^{{}}', found.get(f'refs/tags/{tag}')) for tag in tags}


def release_source(repository, tag, releases, tags):
    if tags[tag]:
        return tags[tag]
    release = releases.get(tag)
    if release is None:
        return None
    if not release['draft']:
        raise SystemExit(f'Published release {tag} has no remote tag')
    target = release['target_commitish']
    if re.fullmatch(r'[0-9a-f]{40}', target):
        return target
    return gh_json('api', f'repos/{repository}/commits/{quote(target, safe="")}')['sha']


def verify_branch(repository, source):
    branch = gh_json('api', f'repos/{repository}/git/ref/heads/san-flavored')
    if branch['object']['sha'] != source:
        raise SystemExit('The san-flavored branch advanced while this build was running')


def publish(repo, environment):
    repository = environment['GITHUB_REPOSITORY']
    source = environment['GITHUB_SHA']
    version = read_json(repo / 'custom/version.json')
    notes = release_notes(repo, version)
    canonical = f'san-v{version["version"]}-{version["upstream_kernel"]}'
    if not re.fullmatch(r'san-v\d+\.\d+\.\d+-t\d+', canonical):
        raise SystemExit('Invalid release version')
    revision_tag = f'{canonical}-g{source[:12]}'
    requested = environment.get('RELEASE_TAG')
    if requested and requested not in {canonical, revision_tag}:
        raise SystemExit(f'Release tag must be {canonical} or {revision_tag}')

    verify_branch(repository, source)
    pages = gh_json('api', f'repos/{repository}/releases?per_page=100', '--paginate', '--slurp')
    releases = {release['tag_name']: release for page in pages for release in page}
    tags = tag_sources(repo, (canonical, revision_tag))
    tag = requested or (canonical if release_source(repository, canonical, releases, tags) in {None, source}
                        else revision_tag)
    if release_source(repository, tag, releases, tags) not in {None, source}:
        raise SystemExit(f'{tag} is already bound to another source commit')
    release = releases.get(tag)
    if release and not release['draft']:
        print(f'{tag} already published for {source}')
        return

    published = [item for name, item in releases.items()
                 if name != tag and name.startswith('san-v') and not item['draft']]
    previous = max(published, key=lambda item: item['published_at'], default=None)
    assets = repo / 'out/build-san-flavored/artifacts'
    with tempfile.TemporaryDirectory(prefix='tb323fu-release-') as temporary:
        stage = Path(temporary)
        files = release_assets(repo, assets, stage, source, version)
        body = stage / 'release-notes.md'
        body.write_text(render_notes(repo, version, notes, assets, repository, source,
                                     environment['GITHUB_RUN_ID'], previous['tag_name'] if previous else None))
        title = f'san-flavored v{version["version"]} · 上游 {version["upstream_kernel"]}'
        if tag == revision_tag:
            title += f' · {source[:7]}'
        metadata = ['--repo', repository, '--target', source, '--title', title, '--notes-file', str(body)]
        if release:
            subprocess.run(['gh', 'release', 'edit', tag, *metadata], check=True)
        else:
            subprocess.run(['gh', 'release', 'create', tag, '--draft', *metadata], check=True)
        subprocess.run(['gh', 'release', 'upload', tag, *map(str, files.values()),
                        '--repo', repository, '--clobber'], check=True)

        pages = gh_json('api', f'repos/{repository}/releases?per_page=100', '--paginate', '--slurp')
        draft, = (item for page in pages for item in page if item['tag_name'] == tag)
        if not draft['draft'] or draft['target_commitish'] != source:
            raise SystemExit('Release draft does not match the CI source commit')
        uploaded = {item['name']: item for item in draft['assets']}
        for name, path in files.items():
            asset = uploaded.get(name, {})
            if asset.get('state') != 'uploaded' or asset.get('digest') != f'sha256:{checksum(path)}':
                raise SystemExit(f'Release asset verification failed for {name}')

        verify_branch(repository, source)
        if tag_sources(repo, (tag,))[tag] not in {None, source}:
            raise SystemExit('Remote release tag changed before publication')
        subprocess.run(['gh', 'release', 'edit', tag, '--repo', repository,
                        '--draft=false', '--prerelease=false', '--latest'], check=True)


if __name__ == '__main__':
    repo = Path(__file__).resolve().parents[2]
    if sys.argv[1:] == ['--check-notes']:
        release_notes(repo, read_json(repo / 'custom/version.json'))
    else:
        publish(repo, os.environ)
