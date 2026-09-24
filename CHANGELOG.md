# Changelog

## v0.2.0-alpha.3 — 2026-09-24

Compatibility hotfix for HLE career persistence.

### Fixed
- Same-career native save edits no longer automatically invalidate the HLE career checkpoint.
- HLE can reconcile a manually edited native Hoop Land save while retaining HLE skill, social, fan, and checkpoint state.
- Native save inspection now preserves case-distinct Hoop Land JSON fields such as `pf` and `PF`.
- Compatibility backups stage through the Windows temporary directory to avoid long-path failures on deeply nested HLE checkpoint files.
- A failed or unrelated save reconciliation no longer has to disable every other HLE career.

### Added
- Branch-aware timeline reconciliation for restored or alternate native save states.
- Compatibility handling intended to support Hoop Land Backup Saves, intentional career rewinds, and alternate branches.
- Low-overhead checkpoint/hash indexing so normal unchanged launches do not repeatedly parse full native save history.

### Validation status
- Manual same-career save editing passed a live Windows/Hoop Land reconciliation and cold-reload test.
- Backup/rollback branch handling is included but has not yet completed the same live end-to-end test; this remains an alpha feature and tester reports are requested.

### Current limitations
- Windows x64 / Steam only.
- Automatic HLE enrollment is for new careers; existing non-HLE career migration remains unsupported.
- Soft-cap, HLE contract generation, CPU roster management, and HLE trade rules are not enabled yet.

## v0.2.0-alpha.2 — 2026-09-22

First public experimental alpha of Hoop Land Extended.

### Added
- Expanded HLE skills and skill progression
- Legendary skill framework with concealed locked effects and requirements
- Improved skill descriptions and compact layout behavior
- Expanded social-media personalities
- College and professional fan-progression fixes
- Automatic enrollment for new HLE careers
- Persistent HLE career state
- Setup, modded launch, loader-bypassed launch, report collection, and removal helpers

### Current limitations
- Windows x64 / Steam only
- New careers only
- Supports one exact Hoop Land build; setup verifies compatibility
- Soft-cap, HLE contract generation, CPU roster management, and HLE trade rules are not enabled yet
- Experimental/unverified skills are not treated as release-ready behavior
