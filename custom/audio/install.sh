#!/bin/sh
# SPDX-License-Identifier: MIT
# Install the userspace half of upstream DisplayPort audio; reboot afterwards.
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
DESTDIR=${DESTDIR:-}
install -D -m 0644 "$repo/firmware/audio/LENOVO-TB323FU-tplg.bin" \
    "$DESTDIR/lib/firmware/qcom/kaanapali/LENOVO-TB323FU-tplg.bin"
for path in conf.d/kaanapali/LENOVO-TB323FU.conf Lenovo/TB323FU/HiFi.conf; do
    install -D -m 0644 "$repo/userspace/platform/alsa/ucm2/$path" \
        "$DESTDIR/usr/share/alsa/ucm2/$path"
done
for name in tb323fu-dsp tb323fu-audio-defaults; do
    install -D -m 0755 "$repo/userspace/platform/libexec/$name" \
        "$DESTDIR/usr/libexec/tb323fu/$name"
done
install -D -m 0644 "$repo/userspace/platform/systemd/system/tb323fu-dsp.service" \
    "$DESTDIR/usr/lib/systemd/system/tb323fu-dsp.service"
if [ -z "$DESTDIR" ]; then
    systemctl daemon-reload
fi
echo 'Audio files installed. Reboot after installing the matching kernel.'
