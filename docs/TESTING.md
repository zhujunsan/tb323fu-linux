# Validation gates

Track separately: source inspection, patch application, configuration, build,
artifact checks, device boot, functional tests and long-duration validation.
CI build success is never a device boot result.

First build the unmodified project series/config. Then enable small reviewed
patch batches, recording the exact source lock and config for each build.
Compare all module vermagic strings and embedded DTB/initramfs against the
final Image. Preserve failed build logs and avoid publishing partial artifacts.

Device gates include display/touch, UFS I/O, Wi-Fi reconnect/throughput, audio,
video frame correctness and EOS/streamoff, USB/DP unplug and suspend cycles,
AppArmor policy loading, Trial/Keep/Rollback and Android switching.
Power tests use controlled A/B conditions and record firmware, brightness,
refresh rate, network/AP, services, duration and battery measurement method.
No numerical power target is considered reproduced before such measurements.

For initramfs fsck work, first test disposable loopback ext4 images covering
clean/dirty/error-marked/orphan_file filesystems, e2fsck exit bits, timeout,
unavailable checker, read-only state and trial counter persistence. No automatic
repair policy is enabled in the initial integration.
