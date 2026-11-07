# san-flavored v0.2.0 autofocus packages

This is the camera component of san-flavored v0.2.0, separate from the kernel
Image. Installing the kernel alone does not update libcamera or enable autofocus.
The ARM64 Ubuntu 26.04 packages are version `0.7.0-1ubuntu2+san0.2.0`.

Five pinned patches provide native manual focus, a software focus metric,
contrast-detect autofocus, default continuous focus and settling, plus lens
power management. The fifth patch must accompany the first four: it releases
the lens after streaming and avoids leaving the actuator driven at the last
focus position. Front cameras without a lens do not advertise autofocus.

Source: bobsixsixsix-boop/legion-y700-gen5 at
`4240ea715133574fd335f2e1631a450f09c8c16e`, `linux/camera/`. Patches retain their
original authors and DEP-3 provenance, including Osilvfe/mzak's iceland-mainline
work. `source-lock.json` records original and adapted checksums. The build,
install and verification scripts are adapted for our version, paths and desktop
username; patch bodies are unchanged. The Ubuntu source inputs are independently
pinned by SHA-256 in the build script. Matching source packages accompany binaries.

CI builds all seven binary packages and verifies the autofocus controls and
lens-power code are present. It cannot test focus sharpness, actual lens motion,
front-camera behavior or PipeWire lens release without a tablet. No device
validation is claimed by a successful build.

To prepare installation on an Ubuntu 26.04 tablet, extract the archive into
`/root/libcamera-san/` and verify `sha256sum -c SHA256SUMS` there. The installer
checks the currently installed version, backs up stock packages and installs
the matching library and IPA together. Run as root:

```
bash /root/libcamera-san/libcamera-af-install.sh --install
```

Log out and back in so camera/audio services use the new library. The optional
`--restart-wireplumber` restarts the desktop user's audio/camera session instead.
The desktop user defaults to UID 1000; set `LIBCAMERA_SAN_USER` if needed.
The installer holds these packages to prevent stock libcamera replacing them;
future Ubuntu security updates require a reviewed rebuild and unhold.

To inspect and test (close other camera apps first; use a detailed object
20–50 cm from the rear camera):

```
bash /root/libcamera-san/libcamera-af-install.sh --status
bash /root/libcamera-san/libcamera-af-check.sh --pipewire
```

Rollback restores the backed-up stock packages:

```
bash /root/libcamera-san/libcamera-af-install.sh --rollback
```
