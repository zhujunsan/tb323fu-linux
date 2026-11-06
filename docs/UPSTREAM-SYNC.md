# Upstream synchronization

1. Fetch upstream and inspect new commits; update main by fast-forward only.
2. Create a candidate branch from integration/gnome and merge the reviewed
   upstream revision, without rewriting integration history.
3. Compare kernel base, patch additions/deletions/content, config, initramfs and
   helper contracts. Regenerate sources.json only after explaining each change.
4. Re-run the scoped P0 audit, full-series application and baseline build.
5. Check carried candidates for conflicts and equivalent fixes. Remove absorbed
   patches explicitly with their provenance record; never silently skip failures.
6. Build integration and review the report/config changes in a PR. Device tests
   gate stable promotion. Never publish a stable kernel just because CI passed.

Current automation covers source audit, helper workspace tests, packaging
regression, baseline build and integration build on integration pushes and
`codex/upstream-sync-*` candidate pushes. Candidate CI runs before PR review;
keep the last verified integration revision until the update is approved.
Scheduled upstream detection, candidate creation and automatic PR opening are
future work, not active jobs. Do not dispatch maintenance against an untrusted
PR with repository write credentials.
