# Upstream and downstream review: 2026-11-14

Upstream main moves from `3cc8131f84d0450a4534d1e57d657c8dbe0c26f5` to
`1508c247c8c833e7f742e58b4a870450309fd954` (eight commits, including two
merge commits). The merge into san-flavored has no conflicts. Linux remains
the same locked v7.3 commit. There are now 199 upstream patches and 28 custom
patches. The source lock records the new patch bytes. The last numbered
upstream release remains kernel-t61; its artifacts no longer match current
upstream kernel inputs, and the baseline flag is explicitly false.

The functional change is DisplayPort audio: patch 0207 adds a dedicated
AudioReach link, with matching DT include, topology binary and UCM route.
The DSP startup script also moves out of the unit's inline shell and uses
POSIX read without relying on the service PATH. Upstream documents successful
DP and HDMI audio. Normal unplug falls back to the speakers; playback pinned
to the display output can stop until the application is restarted. MST audio
is untested. A PRC ZUXOS 2.0.10.026 / 24 GB firmware boot report is also added.

san-flavored becomes 0.4.0, keeps the t61 helper suffix and retains libcamera
component version 0.2.0. It includes committed TUN/policy-routing and RTC work
since the previous release. The audio companion archive contains an explicit
installer; no running device is changed as part of this synchronization.

## Downstream

The downstream repository advances from `4240ea7` to
`39ac88f` (one large snapshot commit). Review covers its source files and notes;
device results below are reports by its author, not measurements on this device.

- y18 adds seven upstream fixes for panel dimensions, USB-C suspend and microSD,
  plus a pen-tilt fix. These upstream fixes already exist in our newer t61
  baseline. y18 also disables hung-task panic, already done upstream.
- y19 drops the pen-tilt fix because its owner had no pen to validate it. This
  is an owner-specific rollback; retain our upstream input behavior. Its zram
  changes are userspace configuration, not another kernel patch stack.
- y20 keeps y19 source and enables CONFIG_HID_MAGICMOUSE=m. This is useful if
  Magic Mouse scrolling is needed but is not imported into this audio release.
- Queued patch 1059 adds the AOSS QMP phandle for DDR statistics. Downstream
  marks it unshipped and requiring device validation; defer it. Probe failure
  could remove all qcom_stats files, and reading ddr_stats adds a QMP request.
- New Stage Manager, split screen and dock features depend on KDE/KWin/QML.
  They do not directly fit this checkout's GNOME customization. Also present:
  owner-specific Apple HID rules, DP power-source policy, video-shim and
  background-service refinements. These need separate integration decisions.
- Existing kernel-y16 patches and camera files are unchanged in the new
  snapshot, so no existing custom-patch or autofocus bytes need replacement.

The original working directory contains unrelated staged and unstaged changes.
Synchronization and release preparation use an isolated checkout to preserve
them. Full kernel compilation and helper tests run in GitHub Actions; local
checks cover the 28-patch ordered applicability, release unit tests, actual
initramfs packaging and audio installer staging.
