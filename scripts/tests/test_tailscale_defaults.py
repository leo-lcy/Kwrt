"""Exercise the first-boot script with fresh and restored OpenWrt settings."""
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / 'devices/common/diy/package/base-files/files/etc/uci-defaults/zz-router-tailscale'
MOCK = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
p = Path(os.environ['TEST_STATE'])
state = json.loads(p.read_text())
args = [a for a in sys.argv[1:] if a != '-q']
name = Path(sys.argv[0]).name
if name == 'uci':
    op = args[0]
    if op == 'get':
        if args[1] not in state['uci']: sys.exit(1)
        value = state['uci'][args[1]]
        print(' '.join(value) if isinstance(value, list) else value)
    elif op == 'show':
        for key, value in state['uci'].items():
            if key.startswith(args[1] + '.'):
                print(key + '=' + (' '.join(value) if isinstance(value, list) else value))
    elif op == 'set':
        key, value = args[1].split('=', 1)
        state['uci'][key] = value
    elif op == 'add_list':
        key, value = args[1].split('=', 1)
        state['uci'].setdefault(key, []).append(value)
    elif op != 'commit':
        raise RuntimeError('Unexpected UCI operation')
else:
    state['calls'].append([name] + args)
    if args == ['disable']:
        state['enabled'][name] = False
    elif args == ['stop']:
        state['running'][name] = False
    elif name == 'tailscale-settings' and args == ['enable']:
        state['enabled'][name] = True
    elif name == 'tailscale-settings' and args == ['start']:
        state['registered'] = True
        if state['uci']['tailscale.settings.service_enabled'] != '0':
            raise RuntimeError('Helper started without the opt-out preference')
        state['running'][name] = False
    else:
        raise RuntimeError('Unexpected service operation')
p.write_text(json.dumps(state))
# An already stopped service may return nonzero; setup must still succeed.
if name != 'uci' and args == ['stop']: sys.exit(1)
'''


class TailscaleDefaults(unittest.TestCase):
    def exercise(self, cudy, restored, helper):
        baseline = {
            'network.lan': 'interface', 'network.lan.ipaddr': '192.168.20.1' if cudy else '192.168.10.1',
            'network.wan': 'interface', 'network.wan.proto': 'dhcp' if cudy else 'pppoe',
            'network.wan.metric': '20' if cudy else '0',
            'dhcp.main.server': ['223.5.5.5'],
            'wireless.ap.ssid': 'Home 5G',
            'firewall.wan': 'zone', 'firewall.wan.name': 'wan',
            'firewall.wan.input': 'REJECT',
            'tailscale.settings': 'settings', 'tailscale.settings.service_enabled': '1',
            'tailscale.settings.port': '41641',
            'tailscale.settings.dns_mode': 'disabled',
            'tailscale.settings.advertise_routes': ['192.168.20.0/24'] if cudy else ['192.168.10.0/24'],
        }
        if cudy:
            baseline.update({'network.wan_f50': 'interface', 'network.wan_f50.proto': 'dhcp',
                             'network.wan_f50.metric': '10',
                             'firewall.f50': 'zone', 'firewall.f50.name': 'f50',
                             'firewall.f50.input': 'REJECT'})
        if restored:
            baseline.update({'firewall.@zone[2]': 'zone',
                             'firewall.@zone[2].name': 'tailscale',
                             'firewall.@zone[2].network': ['tailscale', 'other_vpn'],
                             'firewall.@forwarding[0]': 'forwarding',
                             'firewall.@forwarding[0].src': 'lan',
                             'firewall.@forwarding[0].dest': 'tailscale'})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_path = root / 'state.json'
            state_path.write_text(json.dumps({'uci': baseline, 'calls': [],
                                             'enabled': {'tailscale': True, 'tailscale-settings': helper},
                                             'running': {'tailscale': True, 'tailscale-settings': helper}}))
            for name in ('uci', 'tailscale') + (('tailscale-settings',) if helper else ()):
                path = root / name
                path.write_text(MOCK)
                path.chmod(0o755)
            script = SCRIPT.read_text()
            for name in ('tailscale-settings', 'tailscale'):
                script = script.replace('/etc/init.d/' + name, str(root / name))
            env = {**os.environ, 'PATH': str(root) + ':' + os.environ['PATH'],
                   'TEST_STATE': str(state_path)}
            subprocess.run(['sh', '-n'], input=script, text=True, check=True)
            previous = None
            for _ in range(2):
                subprocess.run(['sh'], input=script, text=True, env=env, check=True)
                state = json.loads(state_path.read_text())
                config = state['uci']
                for key, value in baseline.items():
                    if key != 'tailscale.settings.service_enabled':
                        self.assertEqual(config[key], value, key)
                self.assertEqual(config['tailscale.settings.service_enabled'], '0')
                self.assertFalse(state['enabled']['tailscale'])
                self.assertFalse(state['running']['tailscale'])
                if helper:
                    self.assertTrue(state['enabled']['tailscale-settings'])
                    self.assertFalse(state['running']['tailscale-settings'])
                    self.assertTrue(state['registered'])
                self.assertEqual(config['network.tailscale.proto'], 'none')
                self.assertEqual(config['network.tailscale.device'], 'tailscale0')
                zones = [k for k, v in config.items() if v == 'zone' and config.get(k + '.name') == 'tailscale']
                self.assertEqual(len(zones), 1)
                for option in ('input', 'output', 'forward'):
                    self.assertEqual(config[zones[0] + '.' + option], 'ACCEPT')
                for option in ('masq', 'mtu_fix'):
                    self.assertEqual(config[zones[0] + '.' + option], '1')
                pairs = [(config[k + '.src'], config[k + '.dest'])
                         for k, v in config.items() if v == 'forwarding']
                expected = [('lan', 'tailscale'), ('tailscale', 'lan'), ('tailscale', 'wan')]
                if cudy:
                    expected.append(('tailscale', 'f50'))
                self.assertCountEqual(pairs, expected)
                self.assertTrue(all(call[1] in ('disable', 'stop') for call in state['calls']
                                    if call[0] == 'tailscale'))
                if previous is not None:
                    self.assertEqual(config, previous)
                previous = config

    def test_fresh_ax6000(self):
        self.exercise(cudy=False, restored=False, helper=True)

    def test_fresh_cudy(self):
        self.exercise(cudy=True, restored=False, helper=True)

    def test_restored_anonymous_zones(self):
        for cudy in (False, True):
            with self.subTest(cudy=cudy):
                self.exercise(cudy=cudy, restored=True, helper=True)

    def test_older_package_without_settings_service(self):
        self.exercise(cudy=False, restored=False, helper=False)

    def test_helper_honors_preference_at_boot_and_reload(self):
        spec = importlib.util.spec_from_file_location('prepare', REPO / 'scripts/prepare-tailscale-service.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)
            path = package / 'root/etc/init.d/tailscale-settings'
            path.parent.mkdir(parents=True)
            # Execute the shell callbacks, so a disabled service cannot apply DNS
            # or routes, while opting in works both at boot and from LuCI reload.
            source = '''handle_service_state() {
    if [ "$service_enabled" = '1' ]; then
        printf 'daemon-start\\n'
        apply_settings
    else
        printf 'daemon-stop\\n'
    fi
}
apply_settings() { printf 'settings-apply\\n'; }
start_service() {
    apply_settings
}
reload_service() { handle_service_state; }
'''
            path.write_text(source)
            module.prepare(package)
            prepared = path.read_text()
            module.prepare(package)
            self.assertEqual(path.read_text(), prepared)
            for callback in ('start_service', 'reload_service'):
                for enabled in ('0', '1'):
                    result = subprocess.run(['sh'], input=prepared + '\nservice_enabled=' + enabled + '\n' + callback,
                                            text=True, capture_output=True, check=True)
                    expected = 'daemon-stop\n' if enabled == '0' else 'daemon-start\nsettings-apply\n'
                    self.assertEqual(result.stdout, expected)
            path.write_text('start_service() { unexpected_upstream_change; }')
            with self.assertRaises(ValueError):
                module.prepare(package)


if __name__ == '__main__':
    unittest.main()
