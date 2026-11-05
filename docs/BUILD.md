# Custom kernel builds

The initial build runs on a native ARM64 Linux host (Ubuntu 24.04), with Clang/
LLVM 18 and GCC for the static initramfs helpers. Ubuntu's build-host version
does not determine the device root filesystem version (target: Ubuntu 26.04).
On macOS, use CI first; a Linux ARM64 Docker VM can later run the same scripts.
No local container engine is started by these scripts.

```sh
bash custom-build/ci/install-deps.sh
bash custom-build/scripts/build-kernel.sh baseline
# Only after the baseline succeeds and config review is complete:
bash custom-build/scripts/build-kernel.sh integration
```

Use a fresh work directory for every attempt. Set `BUILD_WORK` to an absolute
path on a filesystem with at least 28 GiB free. This initial threshold is a
conservative admission check, not a measured upper bound. BTF/DWARF may require
more disk; CI records capacity and logs. Default parallelism is two (`BUILD_JOBS`).
Do not disable BTF/security or trim the baseline merely to fit a runner.

The build pins the Linux commit and verifies the complete upstream patch file
hash set, applies it with `git am`, and uses upstream config fragments. It builds
Image/DTBs/modules, installs the external amplifier module, checks every module's
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

The first CI builds only the baseline. No release is published automatically.
The workflow is triggered by relevant pushes to integration/gnome. A manual
workflow_dispatch entry exists, but GitHub's manual workflow discovery requires
the workflow to be present on the default branch; keep main pristine and use
branch push triggers initially.

Reproducibility status: source inputs and compiler major are fixed; package
versions are recorded, but apt repository snapshots, runner image and complete
toolchain hashes are not yet pinned. Byte-for-byte reproducibility is not yet
claimed. Initial build/boot status must be read from CI and device evidence.
