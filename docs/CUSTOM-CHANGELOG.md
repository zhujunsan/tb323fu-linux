# san-flavored kernel versions

## 0.6.0 (2026-11-25, pending)

Updates to [kernel-t65](https://github.com/joonhoekim/tb323fu-linux/releases/tag/kernel-t65)
(`38f6c9a`), with 210 upstream patches and 28 custom kernel patches on Linux v7.3.
The interim [t64 release](https://github.com/joonhoekim/tb323fu-linux/releases/tag/kernel-t64)
updated DPU idle-refresh timeouts, AW86937 haptics and the second DSI link.
T65 caps microSD at 100 MHz to avoid read errors observed at 202 MHz, with lower
peak throughput. [Open Device Helper 0.4.10](https://github.com/joonhoekim/tb323fu-linux/releases/tag/helper-v0.4.10)
uses a clean shutdown path when switching to Android from a running Linux root.

The [downstream y18–y20 refresh](https://github.com/bobsixsixsix-boop/legion-y700-gen5/commit/39ac88f88dd395faebe05d7f27caf4d3b9d99f3b)
builds on t52. Its y18 backports are already represented in the newer upstream
base. The y20 change `CONFIG_HID_MAGICMOUSE=m` is enabled for the custom profile,
so Magic Mouse 2 can use the in-tree driver for scrolling and middle click.
Downstream's KDE dock and window management target a separate desktop stack.
The proposed AOSS/QMP statistics patch (1059) is still queued downstream.

Autofocus stays at 0.2.0. The TUN routing, RTC restore and DP-audio components
continue to ship in the custom build. Device boot and peripheral tests are pending.

## 0.5.0 (2026-11-20, testing)

Updates upstream to kernel-t63 / `38caae7`, with 203 upstream patches and
28 custom patches. Linux is pinned to v7.3 (`c03c1a1`).

- Disables direct PMIC RTC-to-system-clock initialization (0214), preventing
  the clock from jumping back toward 1970 after systemd restores saved time.
  The custom Android TOD-offset restore continues to provide offline time.
- Adds the fixed permanent Wi-Fi MAC patches (0209-0210). Install the platform
  files from Open Device Helper 0.4.9 for the matching ath12k module option.
- Replaces the earlier USB/DP-only patches with the reviewed v4 series
  (0211-0213) and adds the stock 6 mA microSD pad drive (0215).

The existing DP-audio and RTC companion archives are included. Kernel updates
alone do not install their userspace components. Autofocus remains 0.2.0.
Publication requires a successful audit and kernel CI build. Device boot,
suspend, network and audio behavior still need validation on this tablet.

## 0.4.0 (2026-11-14, testing)

Updates upstream to `1508c24`: DisplayPort/HDMI audio (patch 0207, audio
topology and UCM) and resilient DSP startup. Linux stays v7.3; the helper ABI
suffix stays t61 because upstream has not published a newer numbered kernel.
The t61 release is now only a baseline reference, not an identical kernel input.
All 28 custom patches and the independent libcamera 0.2.0 component are retained.

Includes the previously committed TUN/policy-routing configuration and Qualcomm
RTC restore files. Kernel updates do not install userspace automatically.
`kernel-artifacts.tar.gz` includes `dp-audio-userspace.tar.gz`; extract that
archive, then run `sudo sh custom/audio/install.sh` from its extracted root.
Install the matching kernel and reboot to load the new DSP topology. The RTC
archive remains separate; install it with `sudo sh custom/rtc/install.sh`.

Upstream reports DP and HDMI playback and normal unplug fallback; an application
stream pinned to the display can require an application restart after unplug.
Audio over MST remains untested. This release requires a successful full CI
build and artifact verification; local source checks are not hardware validation.
See [the synchronization report](UPSTREAM-SYNC-2026-11-14.md) for downstream review.

## 0.3.0 (2026-11-08, testing)

Updates the upstream base to kernel-t61 / `3cc8131`, with 198 upstream patches
and all 28 custom patches. Adds upstream DisplayPort MST, external-display boot
and suspend/resume fixes, built-in dwc3 glue, and the Iris restricted-IOVA fix.
8K HEVC Main10 still does not decode; the upstream fix prevents a tablet reset.
The kernel identity ends in `-tb323fu-t61`, preserving stock helper comparisons.

Autofocus remains package `0.7.0-1ubuntu2+san0.2.0`; its code and ABI did not
change. `custom/version.json` records its component version independently.
Existing autofocus installations need no package change for this kernel update.
See [the sync report](UPSTREAM-SYNC-2026-11-08.md) for scope and release delivery.

## 0.2.0 (2026-11-07, testing)

Based on the locked upstream kernel-t59 inputs (Linux v7.3). The complete
28-patch y16 stack from downstream commit
`4240ea715133574fd335f2e1631a450f09c8c16e` is selected in its original order.
This adds 23 patches to the five-patch device-booted build. Only 1041 retains
the previously documented adaptation (omit the personal module marker).
All other patch files preserve the pinned downstream bytes and headers.

Includes video decode controls/corrections, battery reporting, Wi-Fi
compatibility and timing, GPU recovery, gamma blob bounds validation, memlat
tuning, SMP2P and UHID corrections, SSBS signal-return policy and SDI handling.
1033 depends on 1032. The system-domain-off experiment (1043) remains disabled
by default; importing the interface does not enable runtime system collapse.
MLO is disabled by default by 00y3; 160 MHz remains enabled by default by 00y4.
1058 only disables SDI when download mode is switched off; it does not itself
install a service to switch download mode off.

The version source is `custom/version.json`. Kernel releases use:

```
7.3.0-san-v0.2.0-b<RUN>.<ATTEMPT>-tb323fu-t59
```

The custom semantic version identifies the patch/configuration batch; the build
identity distinguishes rebuilt module trees. The final `-tb323fu-t59` is the
existing helper and release-tool compatibility contract: the helper reads 59
rather than 0, so t59 is no longer spuriously newer. A genuinely newer upstream
t60 is still offered when using the upstream update source. We do not inflate
the upstream serial or suppress real upstream updates.

This does not add automatic ordering of multiple custom versions on the same
upstream tNN to the stock helper. Such builds can be inspected/installed as
local files; a dedicated custom update feed needs a separate protocol change.
CI artifacts carry the custom version in their name and include
`custom-version.json`, the exact kernel release, patch selection and source lock.
CI builds are testing artifacts, not a hardware-validated stable release.

This release also builds the separate libcamera autofocus/lens-power component
as `0.7.0-1ubuntu2+san0.2.0` for Ubuntu 26.04 ARM64. Its five patches and
source-locked build/install/device-check scripts are in `custom/libcamera/`.
The dedicated autofocus workflow ships seven matching packages and the modified
source package; installing only the kernel does not install the camera fix.
The y17 initramfs filesystem-check work is tracked independently.

## Previous five-patch build

CI 42163956147 selected 1041, 1046, 1047, 1048 and 1052. On 2026-11-07 the owner
reported successful tablet startup and working dual boot. This is not a claim
of per-feature, throughput, power or codec test coverage.
