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
    declarations = {
        'lastDevicesStatus': 'let lastDevicesStatus = null;',
        'peerTableHeaders': """const peerTableHeaders = [
    { text: _('Status') },
    { text: _('Hostname') },
    { text: _('IP') },
    { text: _('OS') },
    { text: _('Connection') },
    { text: _('RX') },
    { text: _('TX') },
    { text: _('Last Seen') }
];""",
    }
    missing = [definition for name, definition in declarations.items()
               if re.search(r'\b' + name + r'\b', text)
               and not re.search(r'\b(?:let|const|var)\s+' + name + r'\b', text)]
    if not missing:
        print('Tailscale device-list variables require no compatibility fix')
        return
    anchor = re.search(r'\blet\s+map\s*;', text)
    if not anchor:
        raise ValueError('Tailscale view changed; review device-list variable scope')
    text = text[:anchor.end()] + '\n' + '\n'.join(missing) + text[anchor.end():]
    path.write_text(text)
    print('Declared missing Tailscale device-list variables in module scope')


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
