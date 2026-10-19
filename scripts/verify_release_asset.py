#!/usr/bin/env python3
"""Validate an already-built HLE distribution without installing or running it."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive', type=Path)
parser.add_argument('--sha256', required=True)
args = parser.parse_args()
payload = args.archive.read_bytes()
digest = hashlib.sha256(payload).hexdigest()
if digest != args.sha256:
    raise SystemExit('Release SHA-256 mismatch')
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    names = z.namelist()
    if z.testzip() is not None:
        raise SystemExit('ZIP CRC failure')
    if len(names) != len(set(n.casefold() for n in names)):
        raise SystemExit('Duplicate or case-colliding ZIP paths')
    for name in names:
        p = PurePosixPath(name)
        if not name.startswith('HLE/') or p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name:
            raise SystemExit('Unsafe or loose archive path: '+name)
        if {'Game', 'Downloads', 'LauncherLogs', 'Migration', 'StateBackups', 'bin', 'obj', '__pycache__'}.intersection(p.parts):
            raise SystemExit('Mutable installation data in archive')
        if p.name in {'installed.json', 'installed-audit.json', 'world.json', 'PRO_LEAGUE_SAVE_FILE', 'COLLEGE_LEAGUE_SAVE_FILE'}:
            raise SystemExit('Personal or native state in archive')
    root = {PurePosixPath(n).parts[1] for n in names}
    if root != {'HLE.exe', 'Instructions.pdf', 'README.md', 'Documentation', 'HLE_Data'}:
        raise SystemExit('Unexpected root items')
    m = json.loads(z.read('HLE/HLE_Data/release.json'))
    if m['Version'] != '0.5.0-alpha.1' or m['RuntimeVersion'] != '0.5.0-evolution-dev.13' or m['ArchiveRootFolder'] != 'HLE':
        raise SystemExit('Wrong release/runtime metadata')
    expected = {'HLE/'+r['Path'] for r in m['Files']} | {'HLE/HLE_Data/release.json'}
    if expected != set(names):
        raise SystemExit('Manifest inventory mismatch')
    for row in m['Files']:
        if hashlib.sha256(z.read('HLE/'+row['Path'])).hexdigest() != row['Sha256']:
            raise SystemExit('Manifest content mismatch: '+row['Path'])
    base = json.loads(z.read('HLE/HLE_Data/Developer/DesignReferences/Launcher-Update-Baseline.json'))
    preserved = [r for r in base['Files'] if r['LegacyPath'].startswith(('RuntimeBuilder/Source/', 'Finance/Probe/Source/')) or (r['LegacyPath'].startswith('payload/') and r['LegacyPath'].endswith('.dll'))]
    if len(preserved) != 449:
        raise SystemExit('Unexpected runtime preservation scope')
    for row in preserved:
        if hashlib.sha256(z.read('HLE/'+row['Path'])).hexdigest() != row['Sha256']:
            raise SystemExit('Tested runtime was changed: '+row['Path'])
    proof = json.loads(z.read('HLE/HLE_Data/Developer/DevelopmentEvidence/launcher-package-verification.json'))
    if not proof['Passed'] or len(proof['Checks']) != 9 or not all(r['Passed'] for r in proof['Checks']):
        raise SystemExit('Incomplete fixture verification')
    if not proof['CleanExtraction']['Passed'] or not proof['LegacyOverlay']['Passed']:
        raise SystemExit('Extraction/overlay verification failed')
print(json.dumps({'Passed': True, 'Bytes': len(payload), 'Sha256': digest, 'Files': len(names), 'UnchangedGameplayDlls': 5, 'UnchangedProductionSourceFiles': 444, 'CheckGroups': 9, 'NativeRuntimeExecutedByThisCheck': False}, indent=2))
