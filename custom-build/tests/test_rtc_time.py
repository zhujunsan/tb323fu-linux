# SPDX-License-Identifier: MIT
import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest import mock

PATH = Path(__file__).resolve().parents[2] / 'custom/rtc/tb323fu-rtc-time'
loader = importlib.machinery.SourceFileLoader('rtc_time', str(PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
rtc = importlib.util.module_from_spec(spec)
loader.exec_module(rtc)


class RtcTimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        block = root / 'block/mmcblk0p7'
        block.mkdir(parents=True)
        (block / 'uevent').write_text('DEVNAME=mmcblk0p7\nPARTNAME=persist\n')
        counter = root / 'since_epoch'
        counter.write_text('190000\n')
        for name, value in [('BLOCK_SYSFS', root / 'block'), ('RTC_SECONDS', counter)]:
            patch = mock.patch.object(rtc, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        self.offset_ms = 1794040276895
        self.expected = 190000 + self.offset_ms / 1000
        patch = mock.patch.object(rtc.subprocess, 'run', return_value=subprocess.CompletedProcess(
            [], 0, struct.pack('<Q', self.offset_ms), b''))
        self.read = patch.start()
        self.addCleanup(patch.stop)

    def test_android_offset_restores_real_date_without_raw_rtc_writes(self):
        raw, offset, corrected, _ = rtc.read_hardware_time()
        self.assertEqual((raw, offset, corrected), (190000, self.offset_ms, self.expected))
        command = self.read.call_args.args[0]
        self.assertEqual(command, ['/usr/sbin/debugfs', '-R', 'cat /time/ats_2', '/dev/mmcblk0p7'])
        self.assertNotIn('-w', command)

    def test_truncated_and_implausible_offsets_are_rejected(self):
        for data in [b'', b'1234567', struct.pack('<Q', 0), struct.pack('<Q', 2**64 - 1)]:
            with self.subTest(data=data):
                self.read.return_value.stdout = data
                with self.assertRaises(RuntimeError):
                    rtc.read_hardware_time()

    def test_ambiguous_persist_partition_is_rejected(self):
        duplicate = rtc.BLOCK_SYSFS / 'sda3'
        duplicate.mkdir()
        (duplicate / 'uevent').write_text('DEVNAME=sda3\nPARTNAME=persist\n')
        with self.assertRaises(RuntimeError):
            rtc.read_hardware_time()
        self.read.assert_not_called()

    def test_synchronized_system_is_never_stepped(self):
        with mock.patch.object(rtc.sys, 'argv', ['rtc', '--restore']), \
             mock.patch.object(rtc, 'system_clock_synchronized', return_value=True), \
             mock.patch.object(rtc.time, 'clock_settime') as settime, \
             contextlib.redirect_stdout(io.StringIO()):
            rtc.main()
        self.read.assert_not_called()
        settime.assert_not_called()

    def test_unsynchronized_build_date_is_restored_not_just_1970(self):
        with mock.patch.object(rtc.sys, 'argv', ['rtc', '--restore']), \
             mock.patch.object(rtc, 'system_clock_synchronized', return_value=False), \
             mock.patch.object(rtc.time, 'time', return_value=1789600000), \
             mock.patch.object(rtc.time, 'clock_settime') as settime, \
             contextlib.redirect_stdout(io.StringIO()):
            rtc.main()
        self.assertEqual(settime.call_args.args[0], rtc.time.CLOCK_REALTIME)
        self.assertAlmostEqual(settime.call_args.args[1], self.expected, delta=0.1)

    def test_read_only_mode_never_sets_system_clock(self):
        with mock.patch.object(rtc.sys, 'argv', ['rtc']), \
             mock.patch.object(rtc.time, 'clock_settime') as settime, \
             contextlib.redirect_stdout(io.StringIO()):
            rtc.main()
        settime.assert_not_called()

    def test_ntp_state_query_is_read_only_and_checks_time_error(self):
        for state, expected in [(0, True), (1, True), (4, True), (5, False), (-1, False)]:
            with self.subTest(state=state), mock.patch.object(rtc.ctypes, 'CDLL') as libc:
                libc.return_value.adjtimex.return_value = state
                self.assertEqual(rtc.system_clock_synchronized(), expected)
                pointer = libc.return_value.adjtimex.call_args.args[0]
                self.assertEqual(bytes(pointer._obj), bytes(1024))
