#!/bin/sh
# SPDX-License-Identifier: MIT
# Install once in the Linux root; kernel updates alone do not install userspace.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DESTDIR=${DESTDIR:-}
install -D -m 0755 "$here/tb323fu-rtc-time" "$DESTDIR/usr/local/sbin/tb323fu-rtc-time"
install -D -m 0644 "$here/tb323fu-rtc-restore.service" "$DESTDIR/etc/systemd/system/tb323fu-rtc-restore.service"
if [ -z "$DESTDIR" ]; then
    systemctl daemon-reload
    systemctl enable --now tb323fu-rtc-restore.service
else
    mkdir -p "$DESTDIR/etc/systemd/system/sysinit.target.wants"
    ln -sfn ../tb323fu-rtc-restore.service "$DESTDIR/etc/systemd/system/sysinit.target.wants/tb323fu-rtc-restore.service"
fi
