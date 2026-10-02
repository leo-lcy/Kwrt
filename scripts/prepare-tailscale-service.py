#!/usr/bin/env python3
"""Make LuCI's boot helper honor the user's service_enabled preference."""
import argparse
from pathlib import Path
import re


def prepare(package: Path) -> None:
    path = package / 'root/etc/init.d/tailscale-settings'
    if not path.exists():
        print('Tailscale settings helper absent; using the standard daemon service')
        return
    text = path.read_text()
    pattern = r'(start_service\(\)\s*\{\s*)(apply_settings|handle_service_state)(\s*\})'
    match = re.search(pattern, text)
    if not match or not re.search(r'handle_service_state\(\)\s*\{', text):
        raise ValueError('Tailscale settings helper changed; review its startup behavior')
    if match.group(2) == 'apply_settings':
        text = text[:match.start(2)] + 'handle_service_state' + text[match.end(2):]
        path.write_text(text)
    print('Tailscale settings helper honors service_enabled at boot and reload')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.package)
