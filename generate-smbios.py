#!/usr/bin/env python3
"""Create a private EFI copy with a new identity; never edit the distributed EFI."""
import argparse
import hashlib
import io
import os
from pathlib import Path
import platform
import plistlib
import re
import secrets
import shutil
import subprocess
import tempfile
import urllib.request
import uuid
import zipfile

URL = 'https://github.com/acidanthera/OpenCorePkg/releases/download/1.0.8/OpenCore-1.0.8-RELEASE.zip'
SHA256 = '2011e8b7216ecb2645d97ea710df965947edd406846e92050b9bc4190be6d27b'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--efi', type=Path, default=Path('EFI'), help='unpacked source EFI directory')
    parser.add_argument('--output', type=Path, default=Path('EFI-personalized'), help='new private EFI directory')
    parser.add_argument('--macserial', type=Path, help='use your own official macserial executable instead of downloading')
    args = parser.parse_args()
    source = args.efi.resolve()
    output = args.output.resolve()
    if output == source or source in output.parents or output.exists():
        parser.error('Output must be a new directory outside the source EFI.')
    config = plistlib.loads((source / 'OC/config.plist').read_bytes())
    if not config['PlatformInfo']['Automatic']:
        parser.error('This tool requires PlatformInfo.Automatic = true.')
    generic = config['PlatformInfo']['Generic']
    model = generic['SystemProductName']
    with tempfile.TemporaryDirectory(prefix='y50-macserial-') as temporary:
        if args.macserial:
            executable = args.macserial.resolve()
        else:
            names = {'Darwin': 'macserial', 'Linux': 'macserial.linux', 'Windows': 'macserial.exe'}
            name = names.get(platform.system())
            if not name:
                parser.error('Unsupported OS; supply --macserial with a compatible executable.')
            print('Downloading official OpenCore 1.0.8 utilities (SHA-256 verified)...')
            with urllib.request.urlopen(URL, timeout=90) as response:
                archive = response.read()
            if hashlib.sha256(archive).hexdigest() != SHA256:
                raise RuntimeError('OpenCore archive checksum mismatch; refusing to execute it.')
            with zipfile.ZipFile(io.BytesIO(archive)) as package:
                executable = Path(temporary) / name
                executable.write_bytes(package.read('Utilities/macserial/' + name))
            executable.chmod(0o700)
        result = subprocess.run([str(executable), '-m', model, '-n', '1'],
                                check=True, capture_output=True, text=True)
        match = re.search(r'^\s*([A-Z0-9]{11,12})\s*\|\s*([A-Z0-9]{17})\s*$', result.stdout, re.MULTILINE)
        if not match:
            raise RuntimeError('macserial did not return a supported serial/MLB pair.')
        generic['SystemSerialNumber'], generic['MLB'] = match.groups()
    generic['SystemUUID'] = str(uuid.uuid4()).upper()
    rom = bytearray(secrets.token_bytes(6))
    rom[0] = (rom[0] | 2) & 0xfe  # Locally administered, unicast; not the owner's MAC.
    generic['ROM'] = bytes(rom)
    # Remove any legacy identity overrides, if present in another config.
    for section in ('DataHub', 'PlatformNVRAM', 'SMBIOS'):
        legacy = config['PlatformInfo'].get(section, {})
        for key in ('SystemSerialNumber', 'BoardSerialNumber', 'MLB', 'SystemUUID', 'SystemId', 'ROM'):
            if key in legacy:
                legacy[key] = b'' if isinstance(legacy[key], bytes) else ''
    output.parent.mkdir(parents=True, exist_ok=True)
    old_umask = os.umask(0o077)
    try:
        shutil.copytree(source, output)
        with (output / 'OC/config.plist').open('wb') as stream:
            plistlib.dump(config, stream, sort_keys=False)
    finally:
        os.umask(old_umask)
    print('Created private EFI:', output)
    print('Model:', model)
    print('New serial:', generic['SystemSerialNumber'])
    print('Do not upload this folder or share its identifiers. Keep it for future updates.')
    print('Validate the config and check the generated serial before signing into Apple services.')


if __name__ == '__main__':
    main()
