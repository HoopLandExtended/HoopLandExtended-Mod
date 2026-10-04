# Hoop Land Extended

**Hoop Land Extended (HLE)** is an unofficial gameplay expansion for the Windows/Steam version of **Hoop Land**.

> **Current release:** v0.2.0-alpha.4-rc.1  
> **Status:** Experimental release candidate  
> **Platform:** Windows x64 / Steam  
> **Career support:** New HLE careers and existing alpha.3 HLE careers; existing non-HLE careers are not automatically adopted

## What HLE currently adds

- Expanded custom skills, skill progression, and accepted custom skill icons
- Dedicated College ICON and Professional Legendary Ability interfaces
- One equipped ICON/Legendary Ability slot, separate from ordinary skill-point spending
- College-to-professional continuity for HLE skill progress and earned/equipped abilities
- Expanded social-media personalities, accounts, and community feed
- Normalized professional fan progression for played career games
- Automatic HLE enrollment for new careers and persistent HLE career state
- Branch-aware continuation for restored, copied, rerolled, or manually edited HLE careers
- Separate setup, normal/profiling play, loader-bypassed play, report collection, and removal helpers

## Alpha.4 RC1 highlights

v0.2.0-alpha.4-rc.1 packages HLE as a standalone release candidate that creates and maintains its own separate Hoop Land game copy. It does not overwrite the Steam installation or a development installation.

This release candidate adds the ICON and Legendary Ability interfaces, custom icons, college-to-professional continuity, and live-game performance improvements. It also removes HLE's former NBA-entry attribute deduction so native Hoop Land draft regression is the sole authority.

Professional fan gains from played career games now use the normalized HLE calculation at supported game lengths, including full 48-minute games. The live-controller direction fix derives attacking direction from home/road assignment and Hoop Land's halftime side-switch flag, eliminating the unavailable-team and missing-direction exception storms found during RC testing.

## Not in this release

The planned soft-cap, HLE contract-generation, CPU roster-management, and trade overhaul are **not enabled**. Hoop Land's native finance and transaction behavior remains authoritative.

Simulated career-player fan rewards have not been validated for this release candidate and may still use native behavior. Existing careers that were never enrolled in HLE are not automatically adopted.

## Installation

1. Download **`HoopLandExtended-0.2.0-alpha.4-rc.1-win-x64.zip`** from the Releases page.
2. Extract it into its own new writable folder. Do **not** extract it into the Steam Hoop Land folder or an HLE development installation.
3. Close Hoop Land completely.
4. Run `1-SETUP.cmd`.
5. Run `2-PLAY-HLE.cmd` for normal play.

Setup verifies the supported Steam game build, creates a separate game copy, downloads pinned dependencies, compiles the RC runtime with warnings treated as errors, and runs its managed verification suite before installation. Your Steam installation is not modified.

For complete instructions, read `0-START-HERE.txt` inside the release ZIP.

### Upgrading from alpha.3

Extract this RC over a clean alpha.3 package folder that still contains its matching `installed.json` receipt, then run `1-SETUP.cmd`. Setup verifies the prior installation, updates the separate game copy, and preserves saves and HLE career state. Keep an untouched alpha.3 archive as your rollback copy.

## Verify your download

SHA-256:

```text
cb2f7c6104e0182d98e8effe646ab90e89629dc17c306cb90ab50e2e1aaf466a
```

for:

```text
HoopLandExtended-0.2.0-alpha.4-rc.1-win-x64.zip
```

## Reporting bugs

Close the game first, then run `4-COLLECT-REPORT.cmd`. Review the generated report ZIP before sharing it because logs can include local machine paths or gameplay details.

When reporting a problem, include what you were doing, whether it reproduces after a restart, and screenshots when useful.

## Important

- This is an experimental prerelease.
- HLE currently targets one exact Windows/Steam Hoop Land build.
- Do not bypass setup's compatibility check.
- The normal launcher disables profiling overhead; use `2A-PLAY-HLE-PROFILING.cmd` only when collecting performance evidence.
- Do not redistribute a post-setup HLE folder. It may contain copied Hoop Land files, downloaded dependencies, logs, and local state. Share only the original release ZIP.

## Disclaimer

Hoop Land Extended is an unofficial fan-made project and is not affiliated with or endorsed by Koality Game.

Hoop Land itself is **not** included in this repository or release package.
