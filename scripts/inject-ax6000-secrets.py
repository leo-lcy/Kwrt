#!/usr/bin/env python3
"""Insert AX6000 settings as shell literals and validate without logging them."""
import os
from pathlib import Path
import shlex
import subprocess


def inject(profile: Path, env) -> None:
    names = ('ROOT_PASSWD', 'PPPOE_USERNAME', 'PPPOE_PASSWD', 'WIFI_PASSWD')
    for name in names:
        value = env.get(name, '')
        if not value or any(char in value for char in ('\n', '\r', '\0')):
            raise ValueError(f'{name} must be set and contain no line breaks or NUL')
    wifi = env['WIFI_PASSWD']
    if not (8 <= len(wifi.encode()) <= 63 or
            len(wifi) == 64 and all(c in '0123456789abcdefABCDEF' for c in wifi)):
        raise ValueError('WIFI_PASSWD must be 8–63 bytes or 64 hexadecimal digits')
    files = profile / 'diy/package/base-files/files'
    rendered = []
    for relative in ('etc/uci-defaults/99-router-settings', 'etc/rc.local'):
        path = files / relative
        text = path.read_text()
        for name in names:
            text = text.replace(f'__{name}_SHELL__', shlex.quote(env[name]))
        if any(f'__{name}_SHELL__' in text for name in names):
            raise ValueError(f'Unresolved setting in {path.name}')
        check = subprocess.run(['sh', '-n'], input=text, text=True, capture_output=True)
        if check.returncode:
            raise ValueError(f'Invalid shell syntax in {path.name}')
        rendered.append((path, text))
    for path, text in rendered:
        path.write_text(text)


if __name__ == '__main__':
    inject(Path('devices/common'), os.environ)
