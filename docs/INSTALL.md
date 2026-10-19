# Installation and updating — HLE 0.5.0 Alpha 1

Requires Windows x64, your own supported Steam Hoop Land installation, internet for first setup, and a writable HLE folder outside Steam. The launcher verifies the supported game fingerprint before installing. Hoop Land and native saves are not included.

## Fresh installation

Download **HLE-0.5.0-alpha.1-Windows.zip** from [this release](https://github.com/HoopLandExtended/HoopLandExtended-Mod/releases/tag/v0.5.0-alpha.1), not the automatic Source code archives. Extract all files. Open the single enclosing **HLE/** folder, then **HLE.exe**. Select the original game folder through Steam → Manage → Browse local files, choose modules and front-office mode, and complete setup. First setup and first launch can take several minutes. Then select Play HLE.

The root contains only HLE.exe, Instructions.pdf, README.md, Documentation/, and HLE_Data/. Keep the whole folder together. HLE_Data/Game is the separate modded game copy. HLE.exe remains the only normal entry point.

## Existing HLE installation

Close the game and launcher. Back up native saves and their matching HLE state. Extract the new ZIP, open its HLE folder, and copy **its contents** into the existing folder containing HLE.exe. Replace supplied package files while preserving existing Game/HLE_Data, settings, receipts, and state. Do not copy only the executable or nest a new release folder inside the old one.

Open HLE.exe. The launcher moves the old game, settings, receipts, logs, reports, and backups under HLE_Data. Recognized legacy package directories and unchanged root documents are archived under HLE_Data/Migration; unknown/custom files are preserved. An interrupted migration resumes on reopening. Conflicting old/new game or settings copies stop before files are moved: preserve both and resolve the intended source rather than deleting state to dismiss the message. Use Update HLE if offered, then Play HLE.

For a separate new installation, finish setup, close the game, then use Tools → Import previous HLE state. Select the prior Game or HLE_Data/Game folder. Keep the source and backups until the career is verified. Native saves remain in Hoop Land's normal save location and can be shared across game copies.

## Modules and controls

Settings independently selects Skills/Legendary Abilities/Athleticism, Finance, Fans, Social, CPU Training, Mentorship, Instant Practice, Persistent Form, and Draft Regression. Front-office choices are Automatic, Player control, and Recommendations. Change settings with the game closed. Use HLE DEVELOPMENT in the practice facility or launcher development tools after loading a career to manage training and mentors. Keep Advanced Form validation Off for ordinary play.

## Help and recovery

Help opens quick/full PDFs and Documentation. Tools opens reports/logs/game folders, backups, state imports, repair, and removal. If the menu fails, HLE_Data/Support/Open-HLE-Menu.cmd exposes startup errors. If setup stops, inspect the latest launcher log and confirm connectivity, writable paths, and the supported game. Repair/reinstall preserves career state and settings. Play without HLE disables the mod for that launch; it does not undo already-saved career changes.

Collect one report after closing the game if a problem persists. Reports exclude native saves but contain HLE sidecar state, local paths, and gameplay details. Review before posting to [Issues](https://github.com/HoopLandExtended/HoopLandExtended-Mod/issues). Reports are not complete backups. Existing native careers without matching HLE finance state are not automatically enrolled in Finance.

Read the [illustrated guide](HLE_Installation_Guide.pdf), [release notes](releases/v0.5.0-alpha.1.md), [verification](VERIFICATION.md), [acceptance checklist](WINDOWS_ACCEPTANCE.md), and [build instructions](BUILD.md).
