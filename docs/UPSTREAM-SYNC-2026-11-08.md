# Upstream synchronization: 2026-11-08

main fast-forwards from `099d3d081e860cfc300502387b66e9343c056619` to
`3cc8131f84d0450a4534d1e57d657c8dbe0c26f5`, then merges into san-flavored.
There are 20 upstream commits. Linux remains v7.3 at the same locked commit.
The upstream patch set grows from 147 to 198 files: 51 additions and four
existing patch revisions (0055, 0118, 0147, 0148). All hashes are refreshed from
the actual merged files. Kernel configuration now builds Qualcomm dwc3 glue in.

The t60/t61 changes add DisplayPort MST and IRQ_HPD handling, boot-time sink
detection, MST suspend/resume and link/PHY fixes. Patch 0206 excludes an IOVA
range the codec firmware cannot access: upstream reports an 8K HEVC Main10
stream now fails with a decode error instead of resetting the tablet. This is
not support for decoding 8K HEVC Main10. MST daisy chains, 4K and audio remain
outside upstream's tested cases. Upstream also improves firmware memory-map
device checks and documents measured hardware behavior.

Our 28-patch stack is retained in canonical order. The custom version becomes
0.3.0 with the compatible trailing `-tb323fu-t61` suffix. The autofocus code is
unchanged and retains its independent package version 0.2.0; the already verified
Ubuntu ARM64 archive from v0.2.0 is included again without rebuilding it.

Existing local GNOME autorotation/extension edits are not part of this sync.
The previous 400 MiB CI artifact budget remains unchanged. A manually requested
release build may stage its verified outputs directly in an existing draft
release, avoiding another large duplicate in the nearly full Actions artifact
store. The staging step verifies the exact source commit and never publishes.
Publication follows successful CI and downloaded-file verification.
