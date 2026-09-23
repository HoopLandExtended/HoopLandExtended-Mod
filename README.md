# Hoop Land Extended

**Hoop Land Extended (HLE)** is an unofficial gameplay expansion for the Windows/Steam version of **Hoop Land**.

> **Current release:** v0.2.0-alpha.2  
> **Status:** Experimental alpha  
> **Platform:** Windows x64 / Steam  
> **Career support:** New careers only

> [!WARNING]
> **Known issue in v0.2.0-alpha.2:** externally editing a native Hoop Land save can cause HLE to enter recovery mode and disable its gameplay modules. Avoid save editing with this build while a hotfix is being prepared. Existing HLE sidecar progression is not intentionally deleted by this condition.

## What HLE currently adds

- Expanded skills and skill progression
- Legendary skill framework with concealed locked effects/requirements
- Improved skill descriptions and layout behavior
- Expanded social-media personalities and navigation-performance fixes
- College and professional fan-progression fixes
- Automatic HLE enrollment for new careers
- Persistent HLE career state
- Separate setup, modded launch, loader-bypassed launch, report collection, and removal helpers

## Not in this release

The planned soft-cap, HLE contract-generation, CPU roster-management, and trade overhaul are **not enabled** in this alpha. Hoop Land's native finance/trade behavior remains active.

Existing-career migration is also not supported in this release.

## Installation

1. Download **`HoopLandExtended-0.2.0-alpha.2-win-x64.zip`** from the Releases page.
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
4dabc9efd3885c03c41cffe9a51a36d4a1a756893e0e5226ecadcf4a0081149a
```

for:

```text
HoopLandExtended-0.2.0-alpha.2-win-x64.zip
```

## Reporting bugs

Close the game first, then run `4-COLLECT-REPORT.cmd`. Review the generated report ZIP before sharing it because logs can include local machine paths or gameplay details.

When reporting a problem, include:
- what you were doing;
- whether this was the first or a later HLE launch;
- whether the issue reproduces after a restart;
- screenshots when useful.

## Important

- This is an experimental alpha.
- HLE currently targets one exact supported Windows/Steam Hoop Land build.
- Do not bypass setup's compatibility check.
- Do not redistribute a post-setup HLE folder. It may contain copied Hoop Land files, downloaded dependencies, logs, and local state. Share only the original release ZIP.

## Disclaimer

Hoop Land Extended is an unofficial fan-made project and is not affiliated with or endorsed by Koality Game.

Hoop Land itself is **not** included in this repository or release package.
