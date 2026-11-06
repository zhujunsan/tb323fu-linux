# Upstream synchronization

Routine flow: `upstream/main` → local and origin `main` → `integration/gnome`.
Do not create a candidate branch or a review PR for ordinary upstream syncs.
This direct flow was explicitly confirmed by the owner on 2026-11-06.

1. Fetch upstream and inspect new commits; fast-forward main only, then push
   the unmodified mirror to origin/main.
2. Switch to integration/gnome and merge main, preserving both histories.
3. Compare kernel base, patch additions/deletions/content, config, initramfs and
   helper contracts. Update sources.json only after reviewing those changes.
4. Check custom patches for conflicts and absorbed fixes. Remove absorbed
   patches explicitly with provenance; never silently skip failures.
5. Run applicable local checks, commit the synchronization and source-lock
   changes, and push integration/gnome to trigger CI directly.
6. Report baseline/integration results separately from device validation.
   Device tests gate stable promotion. Never auto-publish a stable kernel.

CI covers source audit, helper workspace tests, packaging regression, baseline
build and integration build on integration/gnome pushes. Record the last green
source revision so that pending updates are not mistaken for validated builds.
Scheduled upstream detection is not yet implemented. No device writes or
stable release publication are part of source synchronization.
