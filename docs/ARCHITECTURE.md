# Custom Ubuntu integration architecture

`main` follows joonhoekim/tb323fu-linux without custom commits.
`integration/gnome` carries our additions. `upstream` is the authoritative
project; `origin` is zhujunsan's Fork; `downstream` is a reference only.
Never merge the downstream repository wholesale or rewrite existing history.

- `custom/manifests/sources.json`: exact project/Linux/downstream identities,
  upstream patch hashes and P0 candidate/import status.
- `custom/patches/series`: explicitly ordered extra patches; first batch is
  Wi-Fi 1041, GPU 1046/1047/1048 followed by Iris 1052, enabled for testing only.
- `custom/config/`: integration fragments, starting with Ubuntu security.
- `custom-build/scripts/`: scoped source audit and native ARM64 build driver.
- `custom-build/ci/`: build-host provisioning.
- `.github/workflows/custom-kernel.yml`: fast audit/packaging checks, then
  baseline and testing integration builds in parallel on free standard ARM64
  runners. Both must succeed; the initial serial baseline has already passed.

The pipeline preserves the upstream built-in DTB, command line, shared modules,
initramfs and helper contracts. Trial/Keep/Rollback remain upstream mechanisms.
The baseline profile changes only build paths and identity; integration adds
reviewed patches and config. High-risk idle/power settings remain absent.
GNOME is the target desktop; no KDE dependencies or gaming customizations are
introduced. P1 keyboard, multimedia and power services follow P0/build work.
