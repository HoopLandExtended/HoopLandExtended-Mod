# Source and reproducible verification

The package contains complete current source and the preserved immutable-companion source/provenance handoff under HLE_Data/Developer. It is based on the latest delivered dev.13 setup-fix.1 archive, not the old public alpha. The public alpha uses the same tested dev.13 runtime; source inclusion does not imply an open-source license.

For the full game runtime build, HLE.exe > Set up / update uses the supported game/reference manifests, downloads pinned loader/Unity dependencies, builds Core and DayProbe with .NET 8 SDK 8.0.419, and runs the existing managed/native-shaped fixture suite before installing five DLLs. The short reusable Windows SDK cache remains LOCALAPPDATA/HLE/dotnet8. Mutable build output is not part of the tracked payload. The three pinned companion DLLs retain their provenance and cannot be silently replaced with a different source build.

For this launcher-only package, the five game DLLs were intentionally preserved byte-for-byte rather than rebuilt. Its native HLE.exe bootstrap is reproducible on Linux using Python 3, GCC, GNU assembler, and GNU ld with i386pep support:

```sh
python3 HLE_Data/Developer/Launcher/build_bootstrap.py
```

New and existing isolated checks (PowerShell 7 works on Linux; normal Windows launching uses Windows PowerShell 5.1):

```powershell
$Data = (Resolve-Path ./HLE_Data).Path
pwsh -NoProfile -File "$Data/Support/Verify-Launcher.ps1"
pwsh -NoProfile -File "$Data/Developer/Launcher/Verification/LayoutMigration.Tests.ps1" -PackageRoot $Data -ReportPath ./layout-results.json
pwsh -NoProfile -File "$Data/Developer/Launcher/Verification/LauncherUi.Tests.ps1" -PackageRoot $Data -ReportPath ./ui-results.json
pwsh -NoProfile -File "$Data/Developer/Launcher/Verification/SetupFlows.Tests.ps1" -PackageRoot $Data -ReportPath ./flow-results.json
```

The setup-flow fixture substitutes only SDK discovery and two compilation functions. Its production installer body, checked fixture archives, real setup preflight, five-file install, update, repair, remove/reinstall, report collector, and Form selection execute on disposable files. It performs no network download, native-game execution or real installation. The UI fixture runs production dialog functions with a recording UI port; it cannot prove Windows text rendering or DPI behavior.

The full runtime verification driver was remapped to the nested layout. Supply supported references and optional native game/metadata files; see `--help`:

```sh
python3 HLE_Data/Developer/Verification/run_verification.py --help
```

Build the PDFs with Python 3, ReportLab and DejaVu Sans. Set HLE_GUIDE_FONT_DIR if the fonts are installed outside the default Linux path. Render and inspect all seven output pages before delivering changed guides.

```sh
python3 HLE_Data/Developer/Documentation/build_guides.py
```

Repackage only after checks pass. The packager checks the preserved runtime fingerprints, regenerates manifests, executes available PowerShell fixture suites, verifies all hashes/PE metadata, and checks a clean extraction. It excludes Game, reports, logs, settings, downloads, migration data, SDKs, build outputs, native saves and other personal state.

```sh
python3 HLE_Data/Developer/Verification/package_release.py --output /absolute/path/HLE-0.5.0-alpha.1-Windows.zip --powershell /absolute/path/pwsh --dotnet /absolute/path/dotnet
```

The fixture checks are not a claim of Windows PowerShell 5.1, Windows Forms, native IL2CPP, or in-game execution. See Verification-Report.md and Windows-Acceptance.md.

Launcher.2 adds FinanceAssets.Tests.ps1 (-PackageRoot, -Dotnet, -ReportPath). It compiles and executes the original Launcher.1 verifier to reproduce the exact missing-profile-pack failure, then runs the current production Build-Finance function using the corrected assets and deliberately older source timestamps with stale caches. Only the plugin compilation is substituted with the preserved payload; the actual Finance verifier is compiled/executed. On Linux hosts where MSBuild startup cannot inspect its own process, build_finance_verifier.py invokes the real SDK Roslyn compiler over the complete same project source set and framework references. The report records that fallback. The full 1,948-case Finance verification also passes through a normal SDK build outside that host restriction.

The archive wraps the complete application in HLE/. Existing manifests remain relative to that application's root. The packager validates the wrapper on clean extraction and strips it only when applying the isolated overlay fixture. A user update copies the contents inside HLE/ into the existing application folder.

Archive output is built to a unique .building candidate and only renamed to the requested ZIP after the file is closed, flushed and verified. The final published filename is reopened and compared by byte count and SHA-256. Saving a replacement after a transfer failure requires an exact saved-copy hash/CRC check as well. Never provide a download path while its archive writer is running.
