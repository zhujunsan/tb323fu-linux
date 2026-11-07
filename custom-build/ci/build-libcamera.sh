#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Native ARM64 Ubuntu 26.04 container. Build packages; never install on a tablet.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
test "$(dpkg --print-architecture)" = arm64
. /etc/os-release
test "$ID/$VERSION_ID" = ubuntu/26.04
export LIBCAMERA_SAN_WORK="$repo/out/libcamera-work"
export LIBCAMERA_Y700_JOBS=4
python3 "$repo/custom-build/scripts/audit-libcamera.py"
bash "$repo/custom/libcamera/libcamera-af-build.sh"
# Source-only dpkg-buildpackage performs debian/rules clean before packing.
# The binary build leaves debian/* staging trees which dpkg-source must not ship.
(cd "$LIBCAMERA_SAN_WORK/libcamera-0.7.0" && dpkg-buildpackage -S -d -us -uc)
output="$repo/out/libcamera-artifacts"
mkdir -p "$output"
cp "$LIBCAMERA_SAN_WORK"/*_arm64.deb "$output/"
cp "$LIBCAMERA_SAN_WORK"/*.dsc "$LIBCAMERA_SAN_WORK"/*.debian.tar.xz \
   "$LIBCAMERA_SAN_WORK"/*.orig.tar.gz "$output/"
cp "$repo/custom/libcamera/"libcamera-af-{install,check}.sh "$output/"
cp "$repo/custom/libcamera/README.md" "$repo/custom/libcamera/source-lock.json" "$output/"
cp "$repo/custom/version.json" "$output/custom-version.json"
cp "$repo/LICENSES/GPL-3.0-or-later.txt" "$repo/LICENSES/LGPL-2.1-or-later.txt" "$output/"
git -c safe.directory="$repo" -C "$repo" rev-parse HEAD > "$output/project-commit.txt"
(cd "$output" && sha256sum -- * > SHA256SUMS)
tar -C "$output" -czf "$repo/out/libcamera-san-v0.2.0-arm64.tar.gz" .
echo 'LIBCAMERA BUILD COMPLETE: no hardware autofocus test or tablet installation performed.'
