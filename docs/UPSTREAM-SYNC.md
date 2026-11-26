# Upstream synchronization

Routine flow: `upstream/main` → local and origin `main` → `san-flavored`.
Do not create a candidate branch or a review PR for ordinary upstream syncs.
This direct flow was explicitly confirmed by the owner on 2026-11-06.

1. Fetch upstream and inspect new commits; fast-forward main only, then push
   the unmodified mirror to origin/main.
2. Switch to san-flavored and merge main, preserving both histories.
3. Compare kernel base, patch additions/deletions/content, config, initramfs and
   helper contracts. Update sources.json only after reviewing those changes.
4. Check custom patches for conflicts and absorbed fixes. Remove absorbed
   patches explicitly with provenance; never silently skip failures.
5. Update [release notes](../custom/release-notes.json) with the version's
   changes, known limitations and device validation. The workflow fills in
   source and build details using the [template](../custom-build/ci/kernel-release-notes.md).
6. Run applicable local checks, commit the synchronization and source-lock
   changes, and push san-flavored. After the audit and build succeed, CI uploads
   verified assets and publishes the release on GitHub.

CI covers source audit, helper workspace tests, packaging regression and an
san-flavored build on san-flavored pushes. Baseline rebuilding is opt-in
for explicit investigations, not a gate for routine builds. Record the last green
source revision so that pending updates are not mistaken for validated builds.
Scheduled upstream detection is not yet implemented. Device validation is
tracked separately and recorded in the release notes.
