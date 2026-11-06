#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Baseline first. Native ARM64 Linux; no flashing or release publication.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
profile=${1:-san-flavored}
case "$profile" in baseline|san-flavored) ;; *) echo 'profile: baseline|san-flavored' >&2; exit 2 ;; esac
test "$(uname -s)/$(uname -m)" = Linux/aarch64
work=${BUILD_WORK:-$repo/out/build-$profile}
mkdir -p "$work"
work=$(cd "$work" && pwd)
exec > >(tee "$work/build.log") 2>&1
available=$(df -Pk "$work" | awk 'NR==2 {print $4}')
test "$available" -ge 29360128 || { echo 'Need at least 28 GiB free for initial full BTF build'; exit 1; }
src=$work/linux
kout=$work/kout
mods=$work/mods
assets=$work/artifacts
test ! -e "$src" || { echo 'Use a fresh BUILD_WORK for each build'; exit 1; }
mkdir -p "$kout" "$assets"
export KBUILD_BUILD_USER=tb323fu KBUILD_BUILD_HOST=ci KBUILD_BUILD_VERSION=1
export SOURCE_DATE_EPOCH
SOURCE_DATE_EPOCH=$(git -C "$repo" show -s --format=%ct HEAD)
export KBUILD_BUILD_TIMESTAMP
KBUILD_BUILD_TIMESTAMP=$(date -u -d "@$SOURCE_DATE_EPOCH" '+%a %b %d %T UTC %Y')
base=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["linux"]["commit"])' "$repo/custom/manifests/sources.json")
python3 - "$repo" <<'PY'
import hashlib,json,pathlib,sys
r=pathlib.Path(sys.argv[1]); lock=json.loads((r/'custom/manifests/sources.json').read_text())
assert {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'kernel/patches').glob('*.patch')} == lock['upstream_patch_sha256'], 'Upstream patch lock mismatch'
PY
git init "$src"
git -C "$src" fetch --depth=1 https://github.com/torvalds/linux.git "$base"
git -C "$src" checkout --detach FETCH_HEAD
test "$(git -C "$src" rev-parse HEAD)" = "$base"
git -C "$src" -c user.name='TB323FU Build' -c user.email=build@localhost am "$repo"/kernel/patches/*.patch
if [ "$profile" = san-flavored ]; then
  python3 "$repo/custom-build/scripts/patch-plan.py" > "$work/selected-patches.txt"
  while IFS= read -r patch; do
    git -C "$src" -c user.name='TB323FU Build' -c user.email=build@localhost am "$patch"
  done < "$work/selected-patches.txt"
else
  : > "$work/selected-patches.txt"
fi
cd "$src"
make_args=(ARCH=arm64 LLVM=-18 O="$kout" LOCALVERSION=)
if [ "${USE_CCACHE:-0}" = 1 ]; then
  command -v ccache >/dev/null
  export CCACHE_DIR=${CCACHE_DIR:-$repo/out/ccache-$profile}
  export CCACHE_BASEDIR=$work CCACHE_COMPILERCHECK=content
  ccache --max-size 2G
  ccache --zero-stats
  make_args+=(CC='ccache clang-18')
  trap 'ccache --show-stats' EXIT
fi
jobs=${BUILD_JOBS:-$(nproc)}
case "$jobs" in ''|*[!0-9]*|0) echo 'BUILD_JOBS must be a positive integer' >&2; exit 2 ;; esac
echo "Build profile=$profile jobs=$jobs ccache=${USE_CCACHE:-0}"
make "${make_args[@]}" defconfig
fragments=(arch/arm64/configs/kaanapali-oneplus-infiniti_defconfig)
for f in baldur baldur-display baldur-netfilter baldur-extra; do fragments+=("$repo/kernel/config/$f.fragment"); done
[ "$profile" != san-flavored ] || fragments+=("$repo/custom/config/ubuntu-security.fragment")
scripts/kconfig/merge_config.sh -m -O "$kout" "$kout/.config" "${fragments[@]}"
# CI/local artifacts use unique names, deliberately outside the release tNN channel.
ident=${GITHUB_RUN_ID:-$SOURCE_DATE_EPOCH}-${GITHUB_RUN_ATTEMPT:-1}-$(git -C "$repo" rev-parse --short=12 HEAD)
scripts/config --file "$kout/.config" --set-str LOCALVERSION "-tb323fu-ci-$profile-$ident" --disable LOCALVERSION_AUTO --set-str INITRAMFS_SOURCE ''
make "${make_args[@]}" olddefconfig
if [ "$profile" = san-flavored ]; then
  grep -qx 'CONFIG_SECURITY_APPARMOR=y' "$kout/.config"
  grep '^CONFIG_LSM=' "$kout/.config" | grep -q apparmor
fi
make "${make_args[@]}" -j"$jobs" Image qcom/kaanapali-lenovo-baldur-display.dtb modules headers_install
make "${make_args[@]}" INSTALL_MOD_PATH="$mods" INSTALL_MOD_STRIP=1 modules_install
# Separate build/install targets avoid a parallel build/install race.
oot=$work/aw882xx
cp -a "$repo/kernel/out-of-tree/aw882xx" "$oot"
make "${make_args[@]}" M="$oot" CONFIG_SND_SOC_AW882XX=m modules
make "${make_args[@]}" M="$oot" CONFIG_SND_SOC_AW882XX=m INSTALL_MOD_PATH="$mods" INSTALL_MOD_STRIP=1 modules_install
rel=$(make -s "${make_args[@]}" kernelrelease)
rm -f "$mods/lib/modules/$rel/build" "$mods/lib/modules/$rel/source"
depmod -b "$mods" "$rel"
while IFS= read -r -d '' module; do
  case "$(modinfo -F vermagic "$module")" in "$rel "*) ;; *) echo "vermagic mismatch: $module"; exit 1 ;; esac
done < <(find "$mods/lib/modules/$rel" -name '*.ko' -print0)
cc -O2 -o "$kout/usr/gen_init_cpio" usr/gen_init_cpio.c
bash "$repo/custom-build/scripts/build-initramfs.sh" -k "$kout" -b /bin/busybox -m "$mods/lib/modules/$rel" -c gcc \
  -l "$work/initramfs.list" "$work/initramfs.cpio.gz"
scripts/config --file "$kout/.config" --set-str INITRAMFS_SOURCE "$work/initramfs.cpio.gz"
make "${make_args[@]}" olddefconfig
make "${make_args[@]}" -j"$jobs" Image
dtb=$kout/arch/arm64/boot/dts/qcom/kaanapali-lenovo-baldur-display.dtb
python3 - "$kout/arch/arm64/boot/Image" "$dtb" "$work/initramfs.cpio.gz" "$rel" <<'PY'
from pathlib import Path
import sys
image=Path(sys.argv[1]).read_bytes()
assert image[56:60] == b'ARM\x64', 'Not an ARM64 Image'
assert ('Linux version '+sys.argv[4]+' ').encode() in image, 'Wrong kernel release'
for p in sys.argv[2:4]:
    data=Path(p).read_bytes()
    assert len(data)>1024 and data in image, f'{p} missing from Image'
PY
cp "$kout/arch/arm64/boot/Image" "$dtb" "$work/initramfs.cpio.gz" "$assets/"
gzip -9 -n -c "$assets/Image" > "$assets/Image.gz"
cp "$kout/.config" "$assets/config"
cp "$repo/custom/manifests/sources.json" "$assets/sources.json"
sed "s|$repo/||" "$work/selected-patches.txt" > "$assets/selected-patches.txt"
git -C "$repo" rev-parse HEAD > "$assets/project-commit.txt"
git rev-parse HEAD > "$assets/patched-linux-commit.txt"
dpkg-query -W > "$assets/build-packages.txt"
printf '%s\n' "$rel" > "$assets/kernelrelease.txt"
tar -C "$repo" -czf "$assets/patches-and-module-sources.tar.gz" kernel/patches kernel/config kernel/out-of-tree/aw882xx custom
if [ "${USE_CCACHE:-0}" = 1 ]; then
  ccache --show-stats > "$assets/ccache-stats.txt"
fi
(cd "$assets" && sha256sum -- * > SHA256SUMS)
echo 'BUILD COMPLETE: static checks passed; no device boot test; no vendor firmware included.'
