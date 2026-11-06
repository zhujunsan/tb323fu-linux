# Upstream synchronization: 2026-11-06

## Source revisions

- Previous upstream: `2ba0908546b482792d3bf03a102799060b90553e`.
- New upstream: `e236668a086a28889c4431a4545951aa316c00e1`.
- Previous verified integration: `10fa3f366f1be21aa6748f4616249496c1b20754`.
- Previous complete CI: [42150201235](https://github.com/zhujunsan/tb323fu-linux/actions/runs/42150201235),
  audit, baseline and five-patch integration all succeeded; both artifacts exist.
- Delivery: directly into `san-flavored` after synchronizing `main`.
  An initial candidate branch/PR was unnecessary and is retired per owner instruction.

## Upstream changes reviewed

Five new commits (including the merge commit), 23 upstream paths:

- `5151f83`: kernel patch 0154 for AW22127 LED ring color effects, zones and current.
- `b174e6f`: helper chase/rainbow controls using the kernel LED rotation interface.
- `6dc884f`: upstream merge of the LED work.
- `160bca5`: Helper 0.4.7 and associated metadata/package versions.
- `e236668`: firmware issue template, label and compatibility table.

The kernel baseline remains Linux v7.3 at
`c03c1a14507dfaf8b856c2608f9ac216021fc222`. The carried upstream series grows
from 146 to 147 files: exactly one addition (0154), with no removals or content
changes to previous patches. Config fragments, initramfs and custom-kernel
update contracts are unchanged. No imported P0 candidate is absorbed.

Our five testing patches (1041/1046/1047/1048/1052), including Wi-Fi PS enabled
per owner preference, remain selected in the same order and with the same hashes.
Downstream reference is unchanged. The source lock records the previous green
build separately; current-build statuses are reset to pending upstream refresh.

## Behavioral considerations

0154 programs LED current in steps up to the vendor maximum of 30 mA rather
than leaving the old 3 mA reset value. Helper default ring brightness changes
from 40 to 128. Default mode is still charge; existing saved configurations
keep their configured brightness. These are observable lighting/power changes,
not a measured battery-power result. Animated effects run on the LED MCU and
can continue during system suspend. Follow upstream here; verify brightness
and charge indication on device, and consider an explicit lower-brightness/off
user preference when measuring standby power.

The firmware table identifies ROW .104 as working and ROW .187 as hanging;
it does not establish compatibility for China-market firmware. Device bring-up
and private backup rules remain unchanged.

## Validation and delivery

Local checks passed: source-lock deltas, P0 independent/combined applicability,
147 upstream patches plus five custom patches applied to an isolated Git index
at the exact Linux base, and helper-core tests (58 passed, 2 ignored). The index
check avoids macOS case-insensitive checkout collisions; it is not compilation.
The P0 check used Git objects for the exact Linux base and cached downstream
patches validated by the original SHA-256 checks after local raw-download TLS
failures. Integration CI will also repeat online source retrieval.
Integration CI additionally tests the complete Linux helper workspace, real
initramfs packing, the entire upstream build and the five-patch integration.
Full ARM64 build results must be read from integration CI, not inferred from
the previous green run. No device validation or stable release is claimed.

`main` mirrors the new upstream revision without custom commits.
`san-flavored` now contains that main revision, its five custom patches and
the refreshed source lock. The owner confirmed direct main-to-integration
synchronization; no additional branch or PR approval is required for routine
updates. The initial merge commits are retained without rewriting history.

The custom branch and build profile were subsequently renamed to `san-flavored`
on 2026-11-06. Historical CI job names and source revisions are unchanged.
