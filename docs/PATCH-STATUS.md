# Custom Ubuntu: P0 patch audit

Audit date: 2026-11-06. Source lock: [`sources.json`](../custom/manifests/sources.json).
Upstream project: `e236668a086a28889c4431a4545951aa316c00e1`; Linux:
`v7.3`, `c03c1a14507dfaf8b856c2608f9ac216021fc222`. Downstream reference:
`4240ea715133574fd335f2e1631a450f09c8c16e` (y16 patches; y17 initramfs).

1046, 1047, 1048 and 1052 are imported byte-for-byte; 1041 is imported with
only its personal module-version marker removed. All five are enabled in the
**testing integration** profile. The previous project revision `10fa3f3` passed
both complete baseline and five-patch integration builds in
[CI 42150201235](https://github.com/zhujunsan/tb323fu-linux/actions/runs/42150201235).
The current upstream refresh needs a new complete build. No candidate has been
tested on our device. The upstream baseline profile includes none of them.
No deep power experiments or downstream complete configuration are imported.
This refresh adds upstream LED patch 0154; all 146 previous upstream patch
files, Linux base, configuration and initramfs are unchanged. See the
[synchronization report](UPSTREAM-SYNC-2026-11-06.md).

## Method and limits

`python3 custom-build/scripts/audit-p0.py` downloads the seven original patch
files at the locked downstream commit, verifies SHA-256, reconstructs their
touched files from the exact Linux base, and applies every upstream patch's
hunks touching those files. Each candidate is independently checked forward
and backward. This checks applicability to the current project, not the complete
kernel series, candidate combinations, compilation, or semantic equivalence.
Reading the relevant code below supplements the applicability check.

The initial run passed all seven forward checks; all reverse checks failed.
The old code paths described below remain present. This is evidence against
these exact fixes already being carried, not a search of all Linux maintainer trees.

| ID | Source / author | Current-code finding | Decision / risk |
|---|---|---|---|
| 1041 | y16 `1041-ath12k-sta-ps-vif-cfg.patch`; y700 workspace | PS handling remains in per-link `bss_info_changed`, not vif-level `vif_cfg_changed` | Enabled for testing, high: owner prioritizes power saving over potential throughput loss. Patch cites Linux fix `4b66d18918f8` and revert `9222582ec524` for throughput regression. Removed personal `MODULE_VERSION` marker; functional changes retained. Validate association, latency, throughput and suspend on WCN7860. |
| 1046 | y16 `1046-drm-msm-a6xx-honor-perfmode_bw-threshold-on-a8x.patch`; Akhil P Oommen | `!adreno_is_a7xx()` still makes A8x vote perfmode at every valid bandwidth | Candidate, medium: upstream-origin change, preserve author/signoffs; compare current maintainer version before importing. |
| 1047 | y16 `1047-drm-msm-a6xx-fix-secondary-rail-vote-in-arc-votes.patch`; Akhil P Oommen | Secondary rail still compared with requested `level`, not quantized `pri[pindex]` | Candidate, medium: correctness fix to dependent voltage vote. Test GPU load, idle and suspend. |
| 1048 | y16 `1048-drm-msm-a6xx-fix-rpmh-dependency-votes.patch`; Akhil P Oommen | Dependency lookup still receives GMU device instead of GPU OPP owner | Candidate, medium: review with 1046/1047 in source-series order, also build individually. |
| 1052 | y16 `1052-media-iris-recycle-decoder-buffers-for-non-display-pictures.patch`; Xilin Wu, via radxa-pkg/libva-v4l2 v1.1.1 | NOSHOW still becomes `V4L2_BUF_FLAG_ERROR`; no new recycling/STOP guard | Candidate, medium/high: includes STOP serialization and LAST/EOS handling. Do not add old downstream 1049, which overlaps this change. Need streamoff, EOS, resolution-change, VP9 and AV1 tests. |
| 1053 | y16 `1053-soc-qcom-smp2p-reset-inbound-state-only-on-restart.patch`; Armada placeholder author; original armada commit `dac08dfe0a72`, virtudude | Inbound `last_value` cleared even when `restart` is false | Candidate, medium: small correctness fix; author attribution and licensing must be resolved before import. Do not claim power savings: source describes ready completion replay without an extra wakeup on v7.3. |
| 1057 | y16 `1057-media-iris-vpu4x-size-the-AV1-line-buffer-for-10-bit-output.patch`; y700 workspace | Upstream 0111 handles HEVC/VP9, but AV1 still calls shared helper without bit depth | Hold, high: not a duplicate of 0111. Downstream describes fitted buffer-size inference, not a firmware specification. Require 8/10-bit, 64/128 superblock, resolution and decoder comparison tests. |
| y17 fsck | `linux/kernel-y17/init`, `NOTES.md`, `kbuild-y17.sh` | Current upstream has no equivalent `rootfsck` function | Redesign before import, high: state journal replay occurs before trial count; full check after count; errors/timeouts still proceed to mount. `orphan_file` limitation is documented downstream. Define exit-bit policy, timeout recovery, trial-state failure handling, and static e2fsck provenance; test on disposable images only. |

## First imported batch

The four imported patches are in `custom/patches/{gpu,video}/` and the canonical
`series`; they retain their original headers, authors and signoffs. The manifest
records each original path, checksum, author, risk, enablement and pending build
status. The decisions marked "Candidate" above describe the audit assessment;
these four are now candidates enabled for testing, not hardware-validated stable fixes.

1052 was independently compared with Radxa's `v1.1.1`
`patches/0005-media-iris-Recycle-decoder-buffers-for-non-display-p.patch`:
both have stable patch-id `4b3ee730970952776d2a8ebbf6ba2fc987217a7c`.
The original Radxa patch names commit `841f40bbd2c8aedb2d7fb003ba67ce78b5d04209`.
GPU patches retain Qualcomm author/reviewer headers and Patchwork references
755589/755592/755593. Those web pages could not be retrieved during this pass;
no claim is made that the carried versions equal the latest maintainer versions.
Their exact changes remain absent from our locked project baseline and their
code changes are small enough for direct review against it.

Run the audit to check the four patches independently and then in series order.
Use `PATCH_IDS=1046,1047,1048` to build GPU only, `PATCH_IDS=1052` for video only,
or an individual ID. Empty `PATCH_IDS` disables every extra patch but retains
the integration security config. Unknown IDs and checksum drift fail closed.
Selection always follows canonical order; callers cannot reorder the series.

## Wi-Fi power-saving inclusion

Owner decision on 2026-11-05: prioritize power savings over possible throughput
loss and include 1041 in the default testing build. The default batch is now
**1041,1046,1047,1048,1052**. Original source SHA-256 remains `sha256` in the
manifest; adapted file integrity uses a separate `local_sha256`. Original author
and source information are preserved; the only code omission is the downstream
`MODULE_VERSION("y700-1041")` marker. No new hardware gating or PS policy is invented.

The patch forwards vif-level `BSS_CHANGED_PS` to each station link supporting
station power saving and honors `vif->cfg.ps`, including turning PS off. It does
not force power saving on if NetworkManager/mac80211 policy requests it off.
That userspace policy must be checked when preparing and validating Ubuntu.

Use `PATCH_IDS=1046,1047,1048,1052` for a fresh no-Wi-Fi-patch comparison build;
`PATCH_IDS=1041` tests the Wi-Fi patch alone. Original baseline always excludes it.
Measure display-off associated idle power, idle/loaded ping latency, iperf3 in
both directions, packet loss, reconnection, and suspend/resume against the same
AP/configuration and userspace PS setting. No power benefit, throughput penalty,
or stability result is claimed before device measurement.

## Provenance and dependencies

Original paths and full patch hashes are in the source lock; original patch
headers remain at the pinned [downstream source](https://github.com/bobsixsixsix-boop/legion-y700-gen5/tree/4240ea715133574fd335f2e1631a450f09c8c16e/linux/kernel-y16/patches).
Kernel modifications target GPL-2.0-only code, but this audit does not certify
redistribution rights for patches with incomplete author/license notices.
In particular 1053 and locally authored 1057 need provenance review before import.
1041 retains the pinned downstream author/source and records its sole adaptation.
The three GPU patches retain Qualcomm author and reviewer/signoff chains.

All candidates depend on the locked upstream project series. 1057 additionally
uses vpu4x/10-bit helpers already carried by that series (including 0111).
1052 replaces, rather than stacks on, historical 1049. Do not copy the y17
complete init over today's upstream: it is based on an earlier init and has
unrelated differences. Port only the reviewed root-check behavior.

## Security finding

`kernel/config/baldur-extra.fragment` builds AppArmor but explicitly documents
it as inactive in `CONFIG_LSM`. Baseline builds preserve that configuration as
a comparison. The integration profile adds `custom/config/ubuntu-security.fragment`
and checks the resolved config for AppArmor and its LSM entry. Policy loading,
Snap compatibility and confinement still require Ubuntu/device validation.
