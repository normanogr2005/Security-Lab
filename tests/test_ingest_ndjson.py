import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "integration" / "ingest_ndjson.py"

spec = importlib.util.spec_from_file_location("ingest_ndjson", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load integration/ingest_ndjson.py")

ingest_ndjson = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ingest_ndjson
spec.loader.exec_module(ingest_ndjson)


class TestIngestNdjson(unittest.TestCase):
    def valid_event(self, **overrides):
        event = {
            "event_id": "netscope-test-001",
            "timestamp": "2026-10-03T09:00:00Z",
            "source": "netscope",
            "event_type": "tcp_connection",
            "severity": "info",
            "source_ip": "192.168.1.20",
            "destination_ip": "192.168.1.50",
            "source_port": 51544,
            "destination_port": 22,
            "metadata": {"state": "ESTABLISHED"},
        }
        event.update(overrides)
        return event

    def write_ndjson(self, *events):
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".ndjson",
            delete=False,
        )
        path = Path(handle.name)
        with handle:
            for event in events:
                if isinstance(event, str):
                    handle.write(event + "\n")
                else:
                    handle.write(json.dumps(event) + "\n")
        self.addCleanup(path.unlink)
        return path

    def test_valid_ipv4_event(self):
        event = self.valid_event()
        ingest_ndjson.validate_event(event)

    def test_valid_ipv6_event(self):
        event = self.valid_event(
            event_id="netscope-ipv6-001",
            source_ip="2001:db8::1",
            destination_ip="2001:db8::2",
            source_port=50000,
            destination_port=443,
        )
        ingest_ndjson.validate_event(event)

    def test_invalid_json_line(self):
        path = self.write_ndjson("{not-json")
        with self.assertRaisesRegex(ValueError, r"line 1: invalid JSON"):
            ingest_ndjson.read_events(path)

    def test_missing_required_field(self):
        event = self.valid_event()
        del event["severity"]
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "severity"):
            ingest_ndjson.read_events(path)

    def test_invalid_source(self):
        event = self.valid_event(source="unknown")
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "source"):
            ingest_ndjson.read_events(path)

    def test_invalid_severity(self):
        event = self.valid_event(severity="urgent")
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "severity"):
            ingest_ndjson.read_events(path)

    def test_port_out_of_range(self):
        event = self.valid_event(destination_port=65536)
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "destination_port"):
            ingest_ndjson.read_events(path)

    def test_boolean_port_rejected(self):
        event = self.valid_event(destination_port=True)
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "destination_port"):
            ingest_ndjson.read_events(path)

    def test_invalid_timestamp_rejected(self):
        event = self.valid_event(timestamp="not-a-timestamp")
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "timestamp"):
            ingest_ndjson.read_events(path)

    def test_empty_event_id_rejected(self):
        event = self.valid_event(event_id="")
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "event_id"):
            ingest_ndjson.read_events(path)

    def test_invalid_ip_rejected(self):
        event = self.valid_event(source_ip="999.999.999.999")
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "source_ip"):
            ingest_ndjson.read_events(path)

    def test_additional_property_rejected(self):
        event = self.valid_event(unexpected_field="nope")
        path = self.write_ndjson(event)
        with self.assertRaisesRegex(ValueError, "additional properties"):
            ingest_ndjson.read_events(path)

    def test_duplicate_event_id_rejected(self):
        first = self.valid_event(event_id="duplicate-001")
        second = self.valid_event(
            event_id="duplicate-001",
            source_ip="192.168.1.21",
        )
        path = self.write_ndjson(first, second)

        with self.assertRaisesRegex(ValueError, "duplicate event_id"):
            ingest_ndjson.read_events(path)

    def test_multiple_ndjson_events(self):
        ipv4 = self.valid_event(event_id="netscope-ipv4-001")
        ipv6 = self.valid_event(
            event_id="netscope-ipv6-001",
            source_ip="::1",
            destination_ip="::2",
            source_port=50000,
            destination_port=22,
        )
        auth = self.valid_event(
            event_id="socforge-auth-001",
            source="socforge",
            event_type="authentication_failed",
            severity="medium",
            source_ip="192.168.1.20",
            destination_ip=None,
            source_port=None,
            destination_port=22,
        )
        path = self.write_ndjson(ipv4, ipv6, auth)

        events = ingest_ndjson.read_events(path)

        self.assertEqual(len(events), 3)
        self.assertEqual(
            [event["source"] for event in events],
            ["netscope", "netscope", "socforge"],
        )


if __name__ == "__main__":
    unittest.main()
