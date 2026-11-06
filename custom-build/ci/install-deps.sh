#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Native ARM64 Ubuntu 24.04 build host. No device firmware is needed.
set -euo pipefail
test "$(uname -m)" = aarch64
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  build-essential git python3 clang-18 llvm-18 lld-18 flex bison \
  libssl-dev libelf-dev bc dwarves kmod cpio squashfs-tools \
  busybox-static console-setup-linux wireless-regdb zstd ccache
