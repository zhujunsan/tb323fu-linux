# san-flavored Ubuntu architecture

`main` follows joonhoekim/tb323fu-linux without custom commits.
`san-flavored` carries our additions. `upstream` is the authoritative
project; `origin` is zhujunsan's Fork; `downstream` is a reference only.
Never merge the downstream repository wholesale or rewrite existing history.

- `custom/manifests/sources.json`: exact project/Linux/downstream identities,
  upstream patch hashes and P0 candidate/import status.
- `custom/patches/series`: the complete pinned y16 28-patch stack, in downstream
  order, enabled for testing. The previous batch contained five patches.
- `custom/version.json`: independent custom semantic version and upstream tNN
  compatibility identity; see `CUSTOM-CHANGELOG.md` for update semantics.
- `custom/config/`: integration fragments, starting with Ubuntu security.
- `custom-build/scripts/`: scoped source audit and native ARM64 build driver.
- `custom-build/ci/`: build-host provisioning.
- `.github/workflows/custom-kernel.yml`: fast audit/packaging checks, then the
  san-flavored build on a free standard ARM64 runner. Original upstream
  baseline builds are optional for explicit investigations, not routine pushes.

The pipeline preserves the upstream built-in DTB, command line, shared modules,
initramfs and helper contracts. Trial/Keep/Rollback remain upstream mechanisms.
The baseline profile changes only build paths and identity; san-flavored adds
reviewed patches and config. High-risk idle/power settings remain absent.
GNOME is the target desktop; no KDE dependencies or gaming services are
introduced. The kernel stack includes 0540's Wine-related SSBS correction per
the owner's expanded-stack request. P1 keyboard, multimedia and power services
are separate from the kernel patch stack.
