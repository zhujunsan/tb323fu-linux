# SPDX-License-Identifier: MIT
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release_stage', Path(__file__).parents[1] / 'ci/stage-kernel-release.py')
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class ReleaseStageTest(unittest.TestCase):
    def execute(self, draft=True, source='abc123', corrupt=False):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'custom').mkdir()
            (root / 'custom/version.json').write_text(json.dumps({'version': '0.3.0', 'upstream_kernel': 't61'}))
            assets = root / 'out/build-san-flavored/artifacts'
            assets.mkdir(parents=True)
            data = b'synthetic kernel fixture'
            (assets / 'Image.gz').write_bytes(data)
            (assets / 'SHA256SUMS').write_text(hashlib.sha256(data).hexdigest() + '  Image.gz\n')
            if corrupt:
                (assets / 'Image.gz').write_bytes(b'corrupted download')
            env = {'RELEASE_TAG': 'san-v0.3.0-t61', 'GITHUB_REPOSITORY': 'test/repo', 'GITHUB_SHA': 'abc123'}
            with patch.object(stage.subprocess, 'check_output', return_value=json.dumps({'draft': draft, 'target_commitish': source}).encode()), \
                 patch.object(stage.subprocess, 'run') as upload:
                if not draft or source != 'abc123' or corrupt:
                    with self.assertRaises(AssertionError):
                        stage.stage(root, env)
                    upload.assert_not_called()
                else:
                    stage.stage(root, env)
                    upload.assert_called_once()
                    with tarfile.open(root / 'out/release-stage/kernel-artifacts.tar.gz') as tar:
                        self.assertEqual(tar.extractfile('Image.gz').read(), data)
                    self.assertEqual((root / 'out/release-stage/Image-tb323fu-t61.gz').read_bytes(), data)

    def test_validated_outputs_stage_in_draft(self):
        self.execute()

    def test_published_release_is_never_modified(self):
        self.execute(draft=False)

    def test_wrong_source_commit_is_rejected(self):
        self.execute(source='another-commit')

    def test_corrupt_build_output_is_rejected(self):
        self.execute(corrupt=True)
