# Custom kernel builds

The initial build runs on a native ARM64 Linux host (Ubuntu 24.04), with Clang/
LLVM 18 and GCC for the static initramfs helpers. Ubuntu's build-host version
does not determine the device root filesystem version (target: Ubuntu 26.04).
On macOS, use CI first; a Linux ARM64 Docker VM can later run the same scripts.
No local container engine is started by these scripts.

The fast audit job also runs `custom-build/tests/test-initramfs-packaging.sh`
with real squashfs-tools and the upstream initramfs packer. It first reproduces
the inherited `SOURCE_DATE_EPOCH`/explicit-timestamp conflict, then verifies the
adapter creates a cpio with shared modules and preserves the parent epoch.
Synthetic module fixtures are used here; this is not a boot or module-load test.
`custom-build/scripts/build-initramfs.sh` removes `SOURCE_DATE_EPOCH` only from
the packer's subprocess because upstream already fixes squashfs timestamps to
zero. Kernel compilation retains the source-derived timestamp.

```sh
bash custom-build/ci/install-deps.sh
bash custom-build/scripts/build-kernel.sh baseline
# Only after the baseline succeeds and config review is complete:
bash custom-build/scripts/build-kernel.sh integration
# Separate fresh directory per selection; all five are enabled by default.
BUILD_WORK=/absolute/path/gpu-only PATCH_IDS=1046,1047,1048 bash custom-build/scripts/build-kernel.sh integration
BUILD_WORK=/absolute/path/video-only PATCH_IDS=1052 bash custom-build/scripts/build-kernel.sh integration
```

Use a fresh work directory for every attempt. Set `BUILD_WORK` to an absolute
path on a filesystem with at least 28 GiB free. This initial threshold is a
conservative admission check, not a measured upper bound. BTF/DWARF may require
more disk; CI records capacity and logs. Default parallelism follows `nproc`;
CI uses four (`BUILD_JOBS=4`) on the free four-core ARM64 runner.
Do not disable BTF/security or trim the baseline merely to fit a runner.

The build pins the Linux commit and verifies the complete upstream patch file
hash set, applies it with `git am`, and uses upstream config fragments. It builds
Image/the display DTB/modules, installs the external amplifier module, checks every module's
vermagic, constructs shared modules through upstream initramfs/build.sh, then
rebuilds Image with the initramfs. It checks the final ARM64 header, release
banner, embedded display DTB and embedded initramfs.

`out/build-PROFILE/artifacts/` contains Image, Image.gz, display DTB, initramfs,
config, source lock, source commits, package versions, carried patch/module
sources and checksums. CI identities include profile, run ID, attempt and project
commit. They are local-install/testing artifacts, not releases in the helper's
`tNN` update channel. No stock boot image or device firmware is required or
included. Packaging an Android boot image later requires the user's own stock
image and upstream tooling; this job performs no partition writes.

After the first successful baseline and integration builds, routine CI now builds
both profiles in parallel after the fast checks. The workflow requires both to
succeed; parallel execution does not promote a failing baseline. The default
batch enables Wi-Fi 1041, GPU 1046/1047/1048 and Iris 1052;
1053, 1057 and fsck remain disabled. Wi-Fi is included per the owner's preference
for power savings; actual power/throughput impact is unmeasured. Set
`PATCH_IDS=1046,1047,1048,1052` for a no-Wi-Fi-patch comparison build in a fresh
work directory. No release is published automatically.
The workflow is triggered by relevant pushes to integration/gnome. A manual
workflow_dispatch entry exists, but GitHub's manual workflow discovery requires
the workflow to be present on the default branch; keep main pristine and use
branch push triggers initially.

## Free-runner performance and storage policy

The first green run took 48m35s for baseline and 51m03s for integration, serially.
Both used only two compilation jobs and no compiler cache. Routine builds now
use the standard public-repository `ubuntu-24.04-arm` runner, four compiler jobs
and two independent profile jobs in parallel. Only the board's display DTB is
built, not DTBs for unrelated machines. No kernel config/features are trimmed.
Cold-build speedup must be measured in the new run; no fixed duration is promised.

Set `USE_CCACHE=1` to use compiler caching locally. CI keeps a separate compressed
ccache for each profile, capped at 2 GiB, and checks compiler content for validity.
No unsafe cache-sloppiness settings are used. New CI identities still force the
necessary version/module regeneration and final linking. The first run is cold;
later hits depend on changed sources/config and eviction. Ccache stats are saved
with successful build outputs and printed in the job log even after build failure.
Remote caching is used only if the repository cache cap is at most 10 GiB. It is
never increased by the workflow; older snapshots are evicted by GitHub at the cap.

Build outputs remain complete in each job, but baseline uploads diagnostics only;
integration uploads its complete outputs in `kernel-artifacts.tar.gz` (which
contains `SHA256SUMS`). Retention is three days, and the already-compressed bundle
is not compressed again by upload-artifact. A 100 MiB bundle cap and 400 MiB
repository artifact soft budget prevent unbounded accumulation. If the cap is
reached or storage usage cannot be checked, the workflow skips the full archive
or upload and explains why in its job summary; no previous artifacts are deleted.
Actions logs remain available. This repository guard cannot account for storage
consumed by other repositories/Packages under the owner's shared account quota.

The workflow refuses non-public repository compute and never selects paid larger
runners. New pushes cancel superseded runs on the same branch. These policies
do not modify account billing settings, spending budgets or cache storage limits.

Reproducibility status: source inputs and compiler major are fixed; package
versions are recorded, but apt repository snapshots, runner image and complete
toolchain hashes are not yet pinned. Byte-for-byte reproducibility is not yet
claimed. Initial build/boot status must be read from CI and device evidence.
