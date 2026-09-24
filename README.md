# Hoop Land Extended

**Hoop Land Extended (HLE)** is an unofficial gameplay expansion for the Windows/Steam version of **Hoop Land**.

> **Current release:** v0.2.0-alpha.3  
> **Status:** Experimental alpha  
> **Platform:** Windows x64 / Steam  
> **Career support:** New HLE careers; existing non-HLE career migration is not supported yet

## What HLE currently adds

- Expanded skills and skill progression
- Legendary skill framework with concealed locked effects/requirements
- Improved skill descriptions and layout behavior
- Expanded social-media personalities and navigation-performance fixes
- College and professional fan-progression fixes
- Automatic HLE enrollment for new careers
- Persistent HLE career state
- Save-edit compatibility for enrolled HLE careers
- Branch-aware checkpoint handling for restored/alternate native save timelines
- Separate setup, modded launch, loader-bypassed launch, report collection, and removal helpers

## Alpha.3 compatibility changes

v0.2.0-alpha.3 fixes a major issue where editing a native Hoop Land save could make HLE reject the career and disable its gameplay modules.

For an enrolled HLE career, the native Hoop Land save now determines the active timeline and HLE follows it. Same-career external save edits can be reconciled without discarding HLE progression. The compatibility layer also contains branch-aware handling for older/restored native saves.

The normal same-career save-edit workflow has passed a live Windows/Hoop Land test. Backup/rollback branching is included but is less-tested in this alpha; please report problems if you use Hoop Land's Backup Saves or intentionally rewind a career.

## Not in this release

The planned soft-cap, HLE contract-generation, CPU roster-management, and trade overhaul are **not enabled** in this alpha. Hoop Land's native finance/trade behavior remains active.

Existing non-HLE career migration is also not supported in this release.

## Installation

1. Download **`HoopLandExtended-0.2.0-alpha.3-win-x64.zip`** from the Releases page.
2. Extract it to a new writable folder. Do **not** extract it into the Steam Hoop Land folder.
3. Close Hoop Land completely.
4. Run `1-SETUP.cmd`.
5. Run `2-PLAY-HLE.cmd`.
6. Create a **new career in an empty save slot**.

Setup uses your legitimate Steam installation to create a separate game copy and downloads pinned BepInEx/Unity dependencies. Your Steam installation is not modified.

For complete instructions, read `0-START-HERE.txt` inside the release ZIP.

## Verify your download

SHA-256:

```text
569be1375d31bee2f5058772435c6cb34eff24efad1640f1c253787ad62da43f
```

for:

```text
HoopLandExtended-0.2.0-alpha.3-win-x64.zip
```

## Reporting bugs

Close the game first, then run `4-COLLECT-REPORT.cmd`. Review the generated report ZIP before sharing it because logs can include local machine paths or gameplay details.

For alpha.3, reports involving any of these are especially useful:
- manually editing an enrolled career's native save JSON;
- restoring files from Hoop Land's `Backup Saves` folder;
- rewinding and rerunning the draft or another career transition;
- copying an HLE career into another slot and continuing both branches.

When reporting a problem, include what you were doing, whether the issue reproduces after a restart, and screenshots when useful.

## Important

- This is an experimental alpha.
- HLE currently targets one exact supported Windows/Steam Hoop Land build.
- Do not bypass setup's compatibility check.
- Keep normal backups before manual save editing or intentional rollback while alpha.3 receives broader testing.
- Do not redistribute a post-setup HLE folder. It may contain copied Hoop Land files, downloaded dependencies, logs, and local state. Share only the original release ZIP.

## Disclaimer

Hoop Land Extended is an unofficial fan-made project and is not affiliated with or endorsed by Koality Game.

Hoop Land itself is **not** included in this repository or release package.
