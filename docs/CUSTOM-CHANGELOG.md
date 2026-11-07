# san-flavored kernel versions

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

The separate libcamera autofocus package and y17 initramfs filesystem-check
work are outside the y16 28-patch stack and are tracked independently.

## Previous five-patch build

CI 42163956147 selected 1041, 1046, 1047, 1048 and 1052. On 2026-11-07 the owner
reported successful tablet startup and working dual boot. This is not a claim
of per-feature, throughput, power or codec test coverage.
