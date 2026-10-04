# Changelog

## v0.2.0-alpha.4-rc.1 — 2026-10-04

Standalone release candidate for the expanded HLE gameplay package.

### Added
- Dedicated College ICON and Professional Legendary Ability interfaces.
- One equipped ICON/Legendary Ability slot, separate from ordinary skill-point spending and mastery.
- Accepted custom skill icons and presentation refinements.
- College-to-professional continuity for HLE skill progress and earned/equipped abilities.
- A separate opt-in profiling launcher while normal play runs without profiling overhead.
- Standalone setup that verifies the supported game build, creates a separate game copy, compiles the runtime, and runs managed verification before installation.
- Supported upgrade path from a clean alpha.3 package installation while preserving saves and HLE career state.

### Changed
- Native Hoop Land draft regression is now the sole authority; HLE no longer applies an additional NBA-entry attribute deduction.
- Professional fan progression for played career games uses the normalized HLE calculation across supported game lengths, including full 48-minute games.
- New careers enroll automatically, while recognized HLE careers continue permissively across restored, copied, rerolled, or manually edited native timelines.
- Live-game performance uses cached loadouts and modifier snapshots, pooled hot-path state, and throttled observation.

### Fixed
- Live controllers are resolved through player-data team IDs rather than unsafe team access.
- Attacking direction is derived from home/road assignment and the native halftime side-switch flag, eliminating the unavailable-team and missing-`TeamData.direction` exception storms observed during RC testing.
- Professional played-game fan awards replace the native return and persist through native save handling.

### Validation status
- Standalone package revision 7 passes its static package verification suite.
- The release loaded successfully on the supported Windows/Steam build.
- Played professional fan progression produced the expected HLE award and matching saved balance delta.
- The final report recorded zero custom-skill runtime errors.
- Simulated career-player fan rewards remain unvalidated and are deferred; native behavior may apply on that path.

### Current limitations
- Windows x64 / Steam only, targeting one exact supported game build.
- Existing non-HLE careers are not automatically adopted.
- Soft-cap, HLE contract generation, CPU roster management, trade rules, and Day Probe are not included or enabled.
- Internet access is required during first setup for pinned dependencies.

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
