"""Guard the audit against falsely certifying minified request shapes."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ApiAuditTests(unittest.TestCase):
    def inspect(self, source):
        parser = os.environ["SONGSTERR_AUDIT_PARSER_ROOT"]
        with tempfile.TemporaryDirectory(prefix="songsterr-audit-fixture-") as folder:
            root = Path(folder)
            for label in ["july", "current"]:
                (root / label).mkdir()
                (root / label / "fixture.js").write_text(source)
            subprocess.run(["node", str(ROOT / "scripts/audit_api.cjs"), str(root), parser], check=True, capture_output=True)
            return json.loads((root / "api-calls.json").read_text())["july"]

    def test_local_alias_does_not_leak_across_parameter_scope(self):
        """Reused minified names must not invent fields from an outer object."""
        result = self.inspect("const x={wrong:1}; function a(v){const t={songId:v,parts:[]};return C.POST('/api/a',{body:t})} function b(x){return C.POST('/api/b',{body:x})}")
        a, b = result["calls"]
        self.assertIn("body.songId", a["fields"])
        self.assertIn("body.parts", a["fields"])
        self.assertIn("body.<dynamic>", b["fields"])
        self.assertNotIn("body.wrong", b["fields"])

    def test_computed_keys_and_spreads_remain_unknown(self):
        """A dynamic preferences dictionary must not become a fake literal key."""
        result = self.inspect("function a(k,v,z){return C.PUT('/api/preference',{body:{[k]:v,...z}})}")
        fields = result["calls"][0]["fields"]
        self.assertIn("body.<computed-key>", fields)
        self.assertIn("body.<spread>", fields)
        self.assertNotIn("body.k", fields)

    def test_form_beacon_and_dynamic_socket_are_not_silently_dropped(self):
        """Non-fetch transports remain visible in the coverage receipt."""
        result = self.inspect("const form={action:'/api/form',method:'post'}; navigator.sendBeacon('/version/reload?via=x'); new WebSocket(url);")
        self.assertEqual({(c['method'],c['route']) for c in result['calls']}, {('POST','/api/form'),('POST','/version/reload?via=x')})
        self.assertEqual(result['unresolved'][0]['method'], 'WebSocket')


if __name__ == '__main__':
    unittest.main()
