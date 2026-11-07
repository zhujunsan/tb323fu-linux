# Upstream synchronization: 2026-11-07

Upstream/main and our main advance from
`e236668a086a28889c4431a4545951aa316c00e1` to
`099d3d081e860cfc300502387b66e9343c056619`. main remains an upstream mirror;
san-flavored merges main without rewriting history or importing downstream wholesale.

Five upstream commits change 16 files: Helper 0.4.8, LED screen-off behavior
(enabled by default, with charge colors excepted), and restarting the helper
daemon when its Debian package is upgraded. No kernel patch, kernel configuration,
Linux base or initramfs input changed. The kernel compatibility identity remains
t59; the custom batch remains v0.2.0 while this initial candidate is being built.

The full 28-patch kernel at custom commit
`f78cf05bc03aa894442f82cdf1e59dae219177bd` passed complete CI, including the helper
workspace, real initramfs packaging, ARM64 kernel/modules and final artifact
verification: https://github.com/zhujunsan/tb323fu-linux/actions/runs/42377391751.
This is compilation/packaging evidence, not a tablet boot test of the 28-patch stack.

The matching autofocus workflow compiled and verified all seven ARM64 packages,
then failed packing its modified source because binary staging directories were
left in debian/. The CI driver now uses source-only dpkg-buildpackage, which runs
the package's clean target before creating the source package. The five camera
patches and binary build logic are unchanged. The source archive is required;
we do not treat compilation alone as a complete camera artifact delivery.

The refreshed source lock records the current upstream and the successful
28-patch build separately. Follow-up CI covers the refreshed integration and
the corrected camera source/binary bundle. Existing local device backups,+migration scripts and unrelated file-mode changes are outside these commits.
