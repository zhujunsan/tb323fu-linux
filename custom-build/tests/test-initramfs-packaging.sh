#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Exercise the real upstream packer and squashfs-tools without a kernel build.
# Modules below are synthetic fixtures, NOT loadable or boot-test artifacts.
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/kout/usr" "$work/modules/7.3.0-packaging-test"
moddir=$work/modules/7.3.0-packaging-test
for name in qcom_pil_info qcom_common qcom_sysmon qcom_q6v5 qcom_q6v5_pas nt36536_ts; do
  printf 'packaging fixture, not a real module\n' > "$moddir/$name.ko"
  printf '%s.ko:\n' "$name" >> "$moddir/modules.dep"
done
# The exact Linux commit is already locked; only the small host cpio utility
# is needed for this test. No device firmware or Android data is accessed.
python3 - "$repo/custom/manifests/sources.json" "$work/gen_init_cpio.c" <<'PY'
import json, pathlib, sys, urllib.request
commit = json.loads(pathlib.Path(sys.argv[1]).read_text())['linux']['commit']
with urllib.request.urlopen(
    f'https://raw.githubusercontent.com/torvalds/linux/{commit}/usr/gen_init_cpio.c',
    timeout=90,
) as response:
    pathlib.Path(sys.argv[2]).write_bytes(response.read())
PY
cc -O2 -o "$work/kout/usr/gen_init_cpio" "$work/gen_init_cpio.c"
args=(-k "$work/kout" -b /bin/busybox -m "$moddir" -c gcc)
export SOURCE_DATE_EPOCH=1700000000
if bash "$repo/kernel/initramfs/build.sh" "${args[@]}" "$work/broken.cpio.gz" > "$work/broken.log" 2>&1; then
  echo 'Expected the unadapted upstream invocation to reproduce the timestamp conflict' >&2
  exit 1
fi
grep -F "SOURCE_DATE_EPOCH and command line options can't be used at the same time" "$work/broken.log"
bash "$repo/custom-build/scripts/build-initramfs.sh" "${args[@]}" \
  -l "$work/initramfs.list" "$work/fixed.cpio.gz"
test "$SOURCE_DATE_EPOCH" = 1700000000
gzip -t "$work/fixed.cpio.gz"
gzip -dc "$work/fixed.cpio.gz" | cpio -it > "$work/contents" 2>/dev/null
grep -Fx 'init' "$work/contents"
grep -Fx 'lib/modules/7.3.0-packaging-test.sqfs' "$work/contents"
unsquashfs -cat "$work/initramfs.d/modules.sqfs" modules.dep > "$work/packed-modules.dep"
cmp "$moddir/modules.dep" "$work/packed-modules.dep"
echo 'PASS: reproduced conflict, packed shared modules through adapter, preserved parent epoch'
