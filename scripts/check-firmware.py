#!/usr/bin/env python3
"""Require the selected device image and its bundled packages before upload."""
import argparse
import hashlib
from pathlib import Path

PROFILES = {
    'ax6000': 'xiaomi_redmi-router-ax6000',
    'cudy_tr3000': 'cudy_tr3000-mod',
}
CUDY_PACKAGES = (
    'kmod-usb3', 'kmod-usb-net-rndis', 'kmod-usb-net-cdc-ether',
    'kmod-usb-net-cdc-ncm', 'kmod-usb-storage', 'kmod-fs-vfat',
    'kmod-fs-exfat', 'block-mount', 'usbutils',
)


def check(device: str, directory: Path, config: Path) -> None:
    profile = PROFILES[device]
    images = list(directory.glob(f'*-{profile}-squashfs-sysupgrade.bin'))
    if len(images) != 1 or images[0].stat().st_size == 0:
        raise ValueError(f'Expected one nonempty sysupgrade image for {profile}')
    # Ensure the other personal device was not accidentally selected.
    config_lines = config.read_text().splitlines()
    enabled = {line for line in config_lines if line.endswith('=y')}
    for name, other in PROFILES.items():
        symbol = f'CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_{other}=y'
        if (symbol in enabled) != (name == device):
            raise ValueError(f'Unexpected device selection: {other}')
    manifests = list(directory.glob(f'*-{profile}.manifest'))
    # A multiple-device build with a shared rootfs has TARGET_PROFILE="";
    # OpenWrt then emits one target manifest rather than a device manifest.
    if not manifests and 'CONFIG_TARGET_PER_DEVICE_ROOTFS=y' not in enabled:
        selected = {
            line for line in enabled
            if line.startswith('CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_')
        }
        if selected == {f'CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_{profile}=y'}:
            manifests = list(directory.glob('openwrt-mediatek-filogic.manifest'))
    if len(manifests) != 1:
        raise ValueError(f'Missing package manifest for {profile}')
    installed = {line.split()[0] for line in manifests[0].read_text().splitlines() if line.strip()}
    required = {'luci-app-passwall2', 'xray-core', 'tailscale', 'luci-app-tailscale-community', 'luci-app-turboacc'}
    if device == 'cudy_tr3000':
        required.update(CUDY_PACKAGES)
        for package in CUDY_PACKAGES:
            if f'CONFIG_PACKAGE_{package}=y' not in enabled:
                raise ValueError(f'{package} is not built into the firmware')
    missing = required - installed
    if missing:
        raise ValueError('Missing bundled packages: ' + ', '.join(sorted(missing)))
    checksums = {}
    for line in (directory / 'sha256sums').read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        checksums[name.lstrip('*').removeprefix('./')] = digest
    image = images[0]
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    if checksums.get(image.name) != digest:
        raise ValueError(f'Invalid or missing SHA256 for {image.name}')
    print(f'Validated {image.name}: {image.stat().st_size} bytes, SHA256 {digest}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', choices=PROFILES, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    check(args.device, args.directory, args.config)
