# Hoop Land Extended (HLE)

Hoop Land Extended expands Hoop Land career play with custom skills and legendary abilities, professional finances, front-office management, fan progression, and social features.

**Current release: 0.4.0-alpha.1 · Windows x64 · Steam**

Download `HLE-0.4.0-alpha.1.zip` from this repository's **Releases** page. Use **HLE.exe** to install, configure, update, and play.

## Features

### Choose your modules

Enable **Skills and Legendary Abilities**, **Finance**, **Fans**, and **Social** independently from the launcher. All four are enabled by default.

- **Skills and Legendary Abilities:** Additional career progression and ability options. Disabling the module preserves your HLE progress and loadout and releases its SP costs until you enable it again.
- **Finance:** Contracts, salary-cap accounting, team finances, front-office decisions, and facility maintenance.
- **Fans:** Fan progression for your career.
- **Social:** Social features surrounding your career and league activity.

### Professional finances

HLE tracks contracts, guarantees, options, cap room, exceptions, dead salary, and luxury tax. Personal coins and team funds have separate balances, with career earnings and team game income supporting their respective wallets.

Salary-cap room and the mid-level exception (MLE) are salary accounting, rather than spendable coins. They are alternative signing routes and cannot be added together as one budget. Facility maintenance and assessed tax bills use team coins.

### Front-office management

With Finance enabled, choose how much control you want over your employer's roster:

| Mode | Your employer | Other teams |
| --- | --- | --- |
| **Automatic** | HLE manages roster moves automatically. | HLE manages roster moves automatically. |
| **Player control** | You manage the front office and approve incoming HLE trade offers. | HLE manages roster moves automatically. |
| **Recommendations** | HLE proposes contracts, extensions, and trades for your approval. | HLE manages roster moves automatically. |

Your career player's own contracts, options, and trade consent remain personal choices. Expired-contract cleanup happens automatically on HLE-managed rosters.

HLE considers your **trade targets**, **trade block**, and **untouchables**. Untouchable players are excluded from HLE trade packages. Trade evaluations consider more than potential stars, including current contribution, development, fit, and contracts. A requested target can carry an estimated value premium of up to 10%, disclosed before approval.

Open **HLE DECISIONS** from the career menu to review proposals. Trade offers list all incoming and outgoing players and draft picks, along with estimated values and any premium. Choose **Approve**, **Reject**, or **Close** to leave a proposal pending. Proposals expire after five days or when relevant circumstances change; leaving one unanswered does not approve it.

Trades require both teams' agreement and eligibility. Completed trades appear in the game's news, message board, and social feed. Trade availability depends on the league's rosters and finances; an offer is not guaranteed every day.

### Facilities

Purchased facility tiers at your career employer are permanent. Facility condition falls by one point per twenty completed professional calendar days. **Maintain All** restores condition using team coins; maintenance is not charged automatically.

## Requirements

- Windows x64.
- Your own supported Steam installation of Hoop Land.
- An internet connection for first-time setup downloads.
- A writable folder for HLE and its separate game copy.

The launcher checks game compatibility before installation. First setup and the first launch can take several minutes. The release does not include Hoop Land game files or career saves.

## Installation

1. Close Hoop Land and any HLE launcher.
2. Download and extract the entire release ZIP. It contains one **`HLE-0.4.0-alpha.1`** folder with all required files.
3. Keep **HLE.exe** together with its accompanying files and open it.
4. Select your original Steam Hoop Land folder, choose your modules, and start setup. HLE creates a separate modded game copy inside the release folder.
5. Select **Play HLE**.

The default front-office mode is **Automatic**. Change it in the launcher settings before playing if you want **Player control** or **Recommendations**.

## Updating

1. Close the game and launcher.
2. Extract the new release ZIP.
3. Copy the **contents** of its release folder into your existing HLE package folder, replacing package files. Preserve the existing **`Game`** folder and **`installed.json`**. Do not place the new release folder inside the old one.
4. Open **HLE.exe** in your existing folder and select **Update HLE**.

Settings and HLE career state are retained when updating in place.

If you set up a separate new package folder instead, close the game and use **Tools → Import previous HLE state**, selecting the old package's **`Game`** folder. Back up your native career save and matching HLE state before moving a career. Separate game copies share the game's normal save slots.

Existing native careers without HLE financial state are not automatically enrolled in Finance. To continue an older HLE career, retain or import its matching HLE state.

## Launcher tools and support

The launcher provides settings, logs, reports, state imports, repair, and removal. Close the game before changing settings, importing state, or performing maintenance. For supported financial save editing, see **`Finance/SAVE-EDITING.md`** in the release.

**Play without HLE** disables the mod for that launch. It does not reverse changes already saved to your career.

To report an issue, use **Tools → Collect report** and open an issue on this repository. Include:

- Your HLE version and enabled modules.
- Your front-office mode and the steps that led to the issue.
- What you expected and what happened.
- Whether it happens again after restarting, plus screenshots where useful.
- The collected report ZIP.

A diagnostic report is not a complete career-save backup.

## Alpha release

HLE is a public alpha. Back up your career before installing or updating, and check the release notes for compatibility information.

Hoop Land is required and remains the property of its respective owners. Third-party dependency sources and licenses are included in **`DEPENDENCIES.txt`** in the release package.
