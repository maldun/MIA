// eachProvider(interface, name, make, body): registers a contract test twice (protected).
// kind "mock" runs against the mock (green from the start, stage 1); kind "real" is skipped until the provider node is integrated (stage 2);
// the integration step of that node replaces the reason below by the real adapter.
import test from 'node:test';

export const REAL_NOT_READY = {
  'IF-111': 'real side: ui/godot/tools/test_bridge.gd in Godot (D-155, A-73)',
  'IF-104': 'real side: tests/test_graph_api.py in the image (A-60, A-66); the JS real cases skip (TD-23)',
};

export function eachProvider(iface, name, make, body) {
  for (const kind of ['mock', 'real']) {
    const skip = kind === 'real' ? REAL_NOT_READY[iface] : false;
    test(`${name} [${kind}]`, { skip }, () => body(make(kind)));
  }
}
