# Custom Ubuntu: P0 patch audit

Audit date: 2026-11-05. Source lock: [`sources.json`](../custom/manifests/sources.json).
Upstream project: `2ba0908546b482792d3bf03a102799060b90553e`; Linux:
`v7.3`, `c03c1a14507dfaf8b856c2608f9ac216021fc222`. Downstream reference:
`4240ea715133574fd335f2e1631a450f09c8c16e` (y16 patches; y17 initramfs).

All candidates are disabled. No candidate has been built or tested on our device.
No deep power experiments or downstream complete configuration are imported.

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
| 1041 | y16 `1041-ath12k-sta-ps-vif-cfg.patch`; y700 workspace | PS handling remains in per-link `bss_info_changed`, not vif-level `vif_cfg_changed` | Hold, high: patch explicitly cites Linux fix `4b66d18918f8` and revert `9222582ec524` for throughput regression. Investigate hardware gating and association/suspend behavior before enabling. Drop personal `MODULE_VERSION` marker if adapted. |
| 1046 | y16 `1046-drm-msm-a6xx-honor-perfmode_bw-threshold-on-a8x.patch`; Akhil P Oommen | `!adreno_is_a7xx()` still makes A8x vote perfmode at every valid bandwidth | Candidate, medium: upstream-origin change, preserve author/signoffs; compare current maintainer version before importing. |
| 1047 | y16 `1047-drm-msm-a6xx-fix-secondary-rail-vote-in-arc-votes.patch`; Akhil P Oommen | Secondary rail still compared with requested `level`, not quantized `pri[pindex]` | Candidate, medium: correctness fix to dependent voltage vote. Test GPU load, idle and suspend. |
| 1048 | y16 `1048-drm-msm-a6xx-fix-rpmh-dependency-votes.patch`; Akhil P Oommen | Dependency lookup still receives GMU device instead of GPU OPP owner | Candidate, medium: review with 1046/1047 in source-series order, also build individually. |
| 1052 | y16 `1052-media-iris-recycle-decoder-buffers-for-non-display-pictures.patch`; Xilin Wu, via radxa-pkg/libva-v4l2 v1.1.1 | NOSHOW still becomes `V4L2_BUF_FLAG_ERROR`; no new recycling/STOP guard | Candidate, medium/high: includes STOP serialization and LAST/EOS handling. Do not add old downstream 1049, which overlaps this change. Need streamoff, EOS, resolution-change, VP9 and AV1 tests. |
| 1053 | y16 `1053-soc-qcom-smp2p-reset-inbound-state-only-on-restart.patch`; Armada placeholder author; original armada commit `dac08dfe0a72`, virtudude | Inbound `last_value` cleared even when `restart` is false | Candidate, medium: small correctness fix; author attribution and licensing must be resolved before import. Do not claim power savings: source describes ready completion replay without an extra wakeup on v7.3. |
| 1057 | y16 `1057-media-iris-vpu4x-size-the-AV1-line-buffer-for-10-bit-output.patch`; y700 workspace | Upstream 0111 handles HEVC/VP9, but AV1 still calls shared helper without bit depth | Hold, high: not a duplicate of 0111. Downstream describes fitted buffer-size inference, not a firmware specification. Require 8/10-bit, 64/128 superblock, resolution and decoder comparison tests. |
| y17 fsck | `linux/kernel-y17/init`, `NOTES.md`, `kbuild-y17.sh` | Current upstream has no equivalent `rootfsck` function | Redesign before import, high: state journal replay occurs before trial count; full check after count; errors/timeouts still proceed to mount. `orphan_file` limitation is documented downstream. Define exit-bit policy, timeout recovery, trial-state failure handling, and static e2fsck provenance; test on disposable images only. |

## Provenance and dependencies

Original paths and full patch hashes are in the source lock; original patch
headers remain at the pinned [downstream source](https://github.com/bobsixsixsix-boop/legion-y700-gen5/tree/4240ea715133574fd335f2e1631a450f09c8c16e/linux/kernel-y16/patches).
Kernel modifications target GPL-2.0-only code, but this audit does not certify
redistribution rights for patches with incomplete author/license notices.
In particular 1053 and locally authored 1041/1057 need provenance review before import.
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
