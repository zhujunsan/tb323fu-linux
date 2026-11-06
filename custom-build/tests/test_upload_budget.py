# SPDX-License-Identifier: MIT
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

spec = importlib.util.spec_from_file_location(
    'prepare_upload', Path(__file__).parents[1] / 'ci/prepare-upload.py')
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)


class UploadBudgetTests(unittest.TestCase):
    def execute(self, profile, used=0, api_error=False, archive_limit=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work = root / 'out' / f'build-{profile}'
            (work / 'artifacts').mkdir(parents=True)
            (work / 'artifacts/Image').write_bytes(b'kernel fixture')
            (work / 'build.log').write_text('build passed\n')
            response = json.dumps([{'artifacts': [{'size_in_bytes': used, 'expired': False}]}])
            with patch.object(upload, 'REPO', root), \
                 patch.object(upload, 'MAX_ARCHIVE', upload.MAX_ARCHIVE if archive_limit is None else archive_limit), \
                 patch.object(sys, 'argv', ['prepare-upload.py', profile, 'success']), \
                 patch.dict(os.environ, {'GITHUB_REPOSITORY': 'test/repo', 'GITHUB_OUTPUT': str(root / 'output')}, clear=True), \
                 patch.object(upload.subprocess, 'check_output', side_effect=ValueError() if api_error else None, return_value=response), \
                 redirect_stdout(io.StringIO()):
                upload.main()
            directory = root / 'out' / f'upload-{profile}'
            files = {p.name for p in directory.iterdir()}
            output = (root / 'output').read_text()
            if 'kernel-artifacts.tar.gz' in files:
                with tarfile.open(directory / 'kernel-artifacts.tar.gz') as archive:
                    self.assertEqual(archive.extractfile('Image').read(), b'kernel fixture')
            return output, files

    def test_san_flavored_archive_contains_build_outputs(self):
        output, files = self.execute('san-flavored')
        self.assertIn('upload=true', output)
        self.assertIn('kernel-artifacts.tar.gz', files)

    def test_baseline_preserves_diagnostics_without_full_archive(self):
        output, files = self.execute('baseline')
        self.assertIn('upload=true', output)
        self.assertEqual(files, {'build.log'})

    def test_full_budget_blocks_upload(self):
        output, files = self.execute('san-flavored', used=upload.BUDGET)
        self.assertIn('upload=false', output)
        self.assertNotIn('kernel-artifacts.tar.gz', files)

    def test_unknown_usage_blocks_upload(self):
        output, _ = self.execute('san-flavored', api_error=True)
        self.assertIn('upload=false', output)

    def test_oversized_archive_keeps_diagnostics(self):
        output, files = self.execute('san-flavored', archive_limit=1)
        self.assertIn('upload=true', output)
        self.assertEqual(files, {'build.log'})


if __name__ == '__main__':
    unittest.main()
