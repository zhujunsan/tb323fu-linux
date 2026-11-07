# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import re
import unittest

path = Path(__file__).resolve().parents[1] / 'scripts/kernel-version.py'
spec = importlib.util.spec_from_file_location('kernel_version', path)
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)


class KernelVersionTest(unittest.TestCase):
    def test_upstream_helper_and_release_tool_compatibility(self):
        release = '7.3.0' + version.localversion('0.2.0', 't59', '42163956147.1')
        # Existing helper::serial_of_release and kernel-release.py contracts.
        self.assertEqual(int(release.rsplit('-tb323fu-t', 1)[1]), 59)
        self.assertEqual(re.search(r'-tb323fu-(t\d+)$', release)[1], 't59')
        self.assertIn('san-v0.2.0', release)
        self.assertLessEqual(len(release), 64)

    def test_rebuilds_and_custom_versions_are_distinct(self):
        first = version.localversion('0.2.0', 't59', '123.1')
        self.assertNotEqual(first, version.localversion('0.2.0', 't59', '123.2'))
        self.assertNotEqual(first, version.localversion('0.2.1', 't59', '123.1'))

    def test_reject_invalid_or_overlong_identity(self):
        for args in [('dev', 't59', '123.1'), ('0.2.0', '59', '123.1'),
                     ('0.2.0', 't59', 'x/y'), ('0.2.0', 't59', '1' * 60 + '.1')]:
            with self.assertRaises(ValueError):
                version.localversion(*args)
