#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Upstream fixes squashfs timestamps explicitly (-mkfs-time/-all-time 0).
# squashfs-tools rejects those options when SOURCE_DATE_EPOCH is also set.
# Scope the removal to this subprocess; kernel compilation keeps its epoch.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
exec env -u SOURCE_DATE_EPOCH bash "$repo/kernel/initramfs/build.sh" "$@"
