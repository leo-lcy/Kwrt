#!/usr/bin/env python3
"""Insert shell-quoted personal settings without logging secret values."""
import os
from pathlib import Path
import shlex
import subprocess


def inject(profile: Path, env) -> None:
    paths = [
        profile / 'diy/package/base-files/files/etc/uci-defaults/99-cudy-settings',
        profile / 'diy/package/base-files/files/etc/rc.local',
    ]
    for name in ('ROOT_PASSWD', 'WIFI_PASSWD'):
        value = env.get(name, '')
        if not value or '\n' in value or '\r' in value:
            raise ValueError(f'{name} must be set and contain no line breaks')
    wifi = env['WIFI_PASSWD']
    if not (8 <= len(wifi.encode()) <= 63 or
            len(wifi) == 64 and all(c in '0123456789abcdefABCDEF' for c in wifi)):
        raise ValueError('WIFI_PASSWD must be 8–63 bytes or 64 hexadecimal digits')
    for path in paths:
        text = path.read_text()
        for name in ('ROOT_PASSWD', 'WIFI_PASSWD'):
            text = text.replace(f'__{name}_SHELL__', shlex.quote(env[name]))
        if '__ROOT_PASSWD_SHELL__' in text or '__WIFI_PASSWD_SHELL__' in text:
            raise ValueError(f'Unresolved setting in {path}')
        check = subprocess.run(['sh', '-n'], input=text, text=True, capture_output=True)
        if check.returncode:
            raise ValueError(f'Invalid shell syntax in {path.name}')
        path.write_text(text)


if __name__ == '__main__':
    inject(Path('devices/cudy_tr3000'), os.environ)
