#!/usr/bin/env python3
"""Prepare Tailscale's optional service helper and LuCI device list."""
import argparse
from pathlib import Path
import re


def prepare_ui(package: Path) -> None:
    path = package / 'htdocs/luci-static/resources/view/tailscale.js'
    if not path.exists():
        print('Tailscale LuCI view absent; skipping device-list compatibility fix')
        return
    text = path.read_text()
    if not re.search(r'\blastDevicesStatus\b', text):
        print('Tailscale view does not use lastDevicesStatus; no fix needed')
        return
    if re.search(r'\b(?:let|const|var)\s+lastDevicesStatus\b', text):
        print('Tailscale device-list status variable already declared')
        return
    anchor = re.search(r'\blet\s+map\s*;', text)
    if not anchor:
        raise ValueError('Tailscale view changed; review device-list variable scope')
    text = text[:anchor.end()] + '\nlet lastDevicesStatus = null;' + text[anchor.end():]
    path.write_text(text)
    print('Declared Tailscale device-list status variable in module scope')


def prepare(package: Path) -> None:
    prepare_ui(package)
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
