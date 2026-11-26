# SPDX-License-Identifier: MIT
import importlib.util
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest.mock import patch

CI = Path(__file__).parents[1] / 'ci'
spec = importlib.util.spec_from_file_location('release_stage', CI / 'stage-kernel-release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class KernelReleaseTest(unittest.TestCase):
    version = {'version': '0.6.1', 'upstream_kernel': 't66', 'libcamera_version': '0.2.0'}
    source = 'a' * 40
    previous = 'b' * 40
    canonical = 'san-v0.6.1-t66'
    revision = f'{canonical}-g{source[:12]}'

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name)
        (self.repo / 'custom/manifests').mkdir(parents=True)
        (self.repo / 'custom/version.json').write_text(json.dumps(self.version))
        self.notes = self.repo / 'custom/release-notes.json'
        self.notes.write_text(json.dumps({
            **self.version, 'changes': ['Kernel changes'], 'known_issues': ['Known issue'],
            'device_validation': 'Device validation pending',
        }))
        lock = self.repo / 'custom/manifests/sources.json'
        lock.write_text(json.dumps({
            'upstream': {'repository': 'upstream/kernel', 'commit': self.previous},
            'linux': {'tag': 'v7.3'}, 'upstream_patch_sha256': {'foo.patch': 'hash'},
            'baseline_reference': {'url': 'https://github.com/upstream/kernel/releases/tag/kernel-t66'},
        }))
        (self.repo / 'custom-build/ci').mkdir(parents=True)
        shutil.copyfile(CI / 'kernel-release-notes.md', self.repo / 'custom-build/ci/kernel-release-notes.md')
        self.assets = self.repo / 'out/build-san-flavored/artifacts'
        self.assets.mkdir(parents=True)
        shutil.copyfile(lock, self.assets / 'sources.json')
        shutil.copyfile(self.repo / 'custom/version.json', self.assets / 'custom-version.json')
        (self.assets / 'Image.gz').write_bytes(b'synthetic kernel fixture')
        (self.assets / 'project-commit.txt').write_text(self.source + '\n')
        (self.assets / 'kernelrelease.txt').write_text('7.3.0-san-v0.6.1-b1.1-tb323fu-t66\n')
        (self.assets / 'selected-patches.txt').write_text('custom.patch\n')
        (self.assets / 'SHA256SUMS').write_text(''.join(
            f'{release.checksum(path)}  {path.name}\n' for path in sorted(self.assets.iterdir())
        ))
        self.environment = {'GITHUB_REPOSITORY': 'owner/repo', 'GITHUB_SHA': self.source, 'GITHUB_RUN_ID': '1'}

        self.commands = []
        self.releases = {}
        self.tags = {}
        self.branch_checks = 0
        self.stale_after_upload = False
        self.corrupt_upload = False
        for name, replacement in (
            ('gh_json', self.github),
            ('tag_sources', lambda repo, tags: {tag: self.tags.get(tag) for tag in tags}),
        ):
            mock = patch.object(release, name, side_effect=replacement)
            mock.start()
            self.addCleanup(mock.stop)
        mock = patch.object(release.subprocess, 'run', side_effect=self.command)
        mock.start()
        self.addCleanup(mock.stop)

    def github(self, *args):
        if '/git/ref/' in args[1]:
            self.branch_checks += 1
            source = self.previous if self.stale_after_upload and self.branch_checks > 1 else self.source
            return {'object': {'sha': source}}
        return [list(self.releases.values())]

    def command(self, args, check):
        self.commands.append(args)
        _, _, action, tag, *options = args
        if action == 'create':
            self.releases[tag] = self.draft(tag)
        if '--notes-file' in options:
            body = Path(options[options.index('--notes-file') + 1]).read_text()
            for expected in ('版本要点', '验证与已知限制', 'Device validation pending', 'Known issue', '构建与源码'):
                self.assertIn(expected, body)
            self.assertNotIn('下载、安装与回退', body)
        if action == 'upload':
            files = [Path(arg) for arg in options[:options.index('--repo')]]
            archive = next(path for path in files if path.suffix == '.gz' and path.name.startswith('kernel-'))
            with tarfile.open(archive) as tar:
                self.assertEqual(tar.extractfile('Image.gz').read(), b'synthetic kernel fixture')
            self.releases[tag]['assets'] = [
                {'name': path.name, 'state': 'uploaded',
                 'digest': 'bad' if self.corrupt_upload else f'sha256:{release.checksum(path)}'}
                for path in files
            ]

    def draft(self, tag):
        return {'tag_name': tag, 'draft': True, 'target_commitish': self.source, 'assets': []}

    def published(self, tag, source):
        self.releases[tag] = {**self.draft(tag), 'draft': False, 'published_at': '2026-11-25T00:00:00Z'}
        self.tags[tag] = source

    def test_publishes_verified_build_as_latest(self):
        release.publish(self.repo, self.environment)
        self.assertEqual([args[2] for args in self.commands], ['create', 'upload', 'edit'])
        self.assertEqual(self.commands[-1][3], self.canonical)
        self.assertEqual(self.commands[-1][-3:], ['--draft=false', '--prerelease=false', '--latest'])

    def test_resumes_verified_draft_for_same_commit(self):
        self.releases[self.canonical] = self.draft(self.canonical)
        release.publish(self.repo, self.environment)
        self.assertEqual([args[2] for args in self.commands], ['edit', 'upload', 'edit'])

    def test_rerun_keeps_published_assets(self):
        self.published(self.canonical, self.source)
        release.publish(self.repo, self.environment)
        self.assertFalse(self.commands)

    def test_same_version_new_commit_uses_revision_tag(self):
        self.published(self.canonical, self.previous)
        release.publish(self.repo, self.environment)
        self.assertTrue(all(args[3] == self.revision for args in self.commands))

    def test_corrupt_local_asset_prevents_draft_creation(self):
        (self.assets / 'Image.gz').write_bytes(b'corrupt')
        with self.assertRaisesRegex(SystemExit, 'Build output checksum mismatch for Image.gz'):
            release.publish(self.repo, self.environment)
        self.assertFalse(self.commands)

    def test_mismatched_remote_checksum_prevents_publication(self):
        self.corrupt_upload = True
        with self.assertRaisesRegex(SystemExit, 'Release asset verification failed'):
            release.publish(self.repo, self.environment)
        self.assertEqual([args[2] for args in self.commands], ['create', 'upload'])

    def test_new_branch_tip_prevents_publication(self):
        self.stale_after_upload = True
        with self.assertRaisesRegex(SystemExit, 'branch advanced'):
            release.publish(self.repo, self.environment)
        self.assertEqual([args[2] for args in self.commands], ['create', 'upload'])

    def test_outdated_notes_prevent_publication(self):
        self.notes.write_text(json.dumps({**self.version, 'upstream_kernel': 't65'}))
        with self.assertRaisesRegex(SystemExit, 'Update custom/release-notes.json'):
            release.publish(self.repo, self.environment)
        self.assertFalse(self.commands)
