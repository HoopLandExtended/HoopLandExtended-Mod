## Hoop Land Extended v0.2.0-alpha.4-rc.1

This is the standalone release candidate for the expanded HLE gameplay package. Setup creates a separate Hoop Land game copy and does not overwrite the Steam installation or a development installation.

### Highlights
- Dedicated College ICON and Professional Legendary Ability interfaces
- One ICON/Legendary Ability slot, separate from ordinary skill-point spending
- College-to-professional continuity for HLE skills and earned/equipped abilities
- Accepted custom skill icons and presentation refinements
- Live-game performance improvements with normal-play profiling disabled
- Native Hoop Land draft regression is now the sole authority; HLE no longer applies an additional NBA-entry deduction
- Normalized HLE professional fan growth for played career games, including full 48-minute games
- Fixed unavailable-team and missing-`TeamData.direction` exception storms
- Supported upgrade path from alpha.3 while preserving the separate game copy, saves, and HLE career state

### Validation
- Standalone package revision 7 passes its package verification suite
- Loaded successfully on the supported Windows/Steam build
- Played Pro League fan award matched the HLE calculation and saved balance delta
- Final diagnostic report recorded zero custom-skill runtime errors

### Known limitations
- **Windows x64 / Steam only**, targeting one exact supported game build
- Existing non-HLE careers are not automatically adopted
- Simulated career-player fan rewards are not validated in this RC and may still use native behavior
- The financial overhaul, Day Probe, development controls, HLE contracts, cap/trade logic, and CPU roster-management changes are not included or enabled
- First setup requires Internet access for pinned dependencies

### Installation
Download `HoopLandExtended-0.2.0-alpha.4-rc.1-win-x64.zip`, extract it into its own writable folder outside the Steam and development folders, and read `0-START-HERE.txt`.

### SHA-256
`cb2f7c6104e0182d98e8effe646ab90e89629dc17c306cb90ab50e2e1aaf466a`

Hoop Land Extended is an unofficial fan mod and is not affiliated with Koality Game.
