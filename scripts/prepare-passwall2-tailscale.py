#!/usr/bin/env python3
"""Keep tailscaled's own marked transport out of PassWall2's local proxy."""
import argparse
from pathlib import Path
import subprocess


def prepare(path: Path) -> None:
    text = path.read_text()
    for chain in ('PSW2_OUTPUT_MANGLE', 'PSW2_OUTPUT_MANGLE_V6'):
        marker = f'KWRT_TAILSCALE_BYPASS_{chain}'
        rule = (f'\tnft "add rule $NFTABLE_NAME {chain} meta mark and 0x00ff0000 '
                f'== 0x00080000 counter return comment \\\"{marker}\\\""')
        anchor = f'\tnft "flush chain $NFTABLE_NAME {chain}"'
        if marker in text:
            if text.splitlines().count(rule) != 1 or anchor + '\n' + rule not in text:
                raise ValueError('Unexpected existing bypass patch: ' + chain)
            continue
        if text.count(anchor) != 1:
            raise ValueError('PassWall2 chain layout changed: ' + chain)
        text = text.replace(anchor, anchor + '\n' + rule)
    subprocess.run(['sh', '-n'], input=text, text=True, check=True)
    path.write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--script', type=Path, required=True)
    prepare(parser.parse_args().script)
