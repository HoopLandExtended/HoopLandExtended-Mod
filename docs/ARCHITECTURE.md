# Launcher layout and migration contract

Layout version 2 separates ApplicationRoot (the visible folder containing HLE.exe) from PackageRoot (HLE_Data). GameRoot is HLE_Data/Game. DeveloperRoot is HLE_Data/Developer. Keep the whole HLE_Data directory: the launcher loads its required PowerShell and C# helpers from it.

| State | Location after update |
|---|---|
| Game, BepInEx runtime and in-game HLE data | HLE_Data/Game |
| Installation/removal receipt | HLE_Data/installed.json / removed-installation.json |
| Pre-setup module choices | HLE_Data/settings/modules.json |
| Installed module choices | HLE_Data/Game/BepInEx/HoopLandExpanded/modules.json |
| Setup/launcher logs and report ZIPs | HLE_Data/LauncherLogs and HLE_Data/Reports |
| HLE state import backups | HLE_Data/StateBackups |
| Financial import backups | Game/BepInEx/HoopLandExpanded/FinanceDevelopment/Ledger/EditBackups, within HLE_Data |
| Preserved previous package files | HLE_Data/Migration/Legacy-{journal id} |
| Finance receipt/reports | HLE_Data/Finance/installed-audit.json and Finance/Reports |
| Source, build tools, fixtures, historical evidence | HLE_Data/Developer |
| Native career saves and per-slot HLE sidecars | Existing native save location, unchanged by layout migration |

The release manifest is HLE_Data/release.json. Its file paths are relative to ApplicationRoot, beginning with HLE.exe, Instructions.pdf, README.md, Documentation/, or HLE_Data/. Hash validation rejects paths outside that root. Mutable game/state/cache files are excluded. Finance's inventory uses the same relative root and covers product Finance files and Developer/Finance source.

Migration runs before startup logs/settings create destination directories. All legacy source and destination paths are scoped to the application; junction/symlink ancestors are rejected. The game must be closed. Package integrity and all conflicts are checked before any move. A lock excludes concurrent migration writers. An atomically replaced JSON journal records source, destination, file hash or directory move marker, and completion status. Directory moves use a unique marker so a crash after rename can be distinguished from an unrelated destination. Relative paths allow resume after copying or renaming the package folder. Completed steps are not replayed; markers are removed after journal commit.

Game, installed receipt, removal receipt, pending settings, or Finance-receipt conflicts are not merged or overwritten. Report/log/cache conflicts preserve the old tree under the legacy archive while keeping the new destination. Old Finance reports/backups are moved before archiving the rest of the old Finance directory. Entire old engineering directories, including local source edits and unknown files within them, are archived intact. Unchanged root engineering documents are recognized using the baseline or a supported legacy release's own inventory. Customized and unknown root files remain at root, so an existing user's folder may intentionally contain more than five entries.

A failed/interrupted migration preserves both data locations. Reopen HLE.exe to resume. If a required source is missing or a destination cannot be identified, the launcher stops and explains the collision rather than guessing. Preserve the complete folder before recovery. The journal and Legacy directories are recovery material; do not delete them during an interrupted migration. There is no automatic destructive rollback.

The game move changes no native player values or HLE transaction history. Installed module settings remain byte-authoritative. No runtime identity is derived from the package's visible folder name; source and five-DLL preservation is verified against the latest delivered setup-fix.1. Existing native/HLE save qualification continues to be handled by the unchanged runtime.

The archive has one outer HLE/ directory; all manifest paths remain relative to the application root inside it. Finance verification assets are passed as an explicit third argument pointing at HLE_Data/Finance/ProfilePacks. They are independent of Developer/Finance/Verification/Fixtures. Finance setup clears only its six build/cache directories before rebuilding both outputs, preventing ZIP timestamp reuse of an old verifier. Imported player/profile data and installed module settings are not targets of that cleanup.
