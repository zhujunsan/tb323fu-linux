# Device arrival checklist

Device: China-market TB323FU, 16 GiB / 512 GiB. Compatibility is unverified.

1. Record the actual Android build, bootloader/baseband versions and partition
   layout read-only; compare upstream firmware/root requirements and anti-rollback
   information before choosing a boot/root path.
2. Establish an authorized recovery and backup plan using this device's own
   files. Store private firmware, keys and backups outside public source control.
3. Review the precise proposed partition/boot operations with the owner before
   executing any destructive writes. Do not automate GPT/UFS/boot modifications.
4. Establish an upstream kernel control result before testing custom changes.
   Use upstream install/boot packaging and helper Trial/Keep/Rollback contracts.
5. Run docs/TESTING.md gates, preserve Android switching, and verify UFS install
   behavior only after the boot/recovery path is demonstrated.

Trial cannot recover a kernel that never reaches initramfs; a separate proven
recovery path is required. No build generated before arrival is hardware-certified.
